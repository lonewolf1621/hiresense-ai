"""
CV <-> job description matching for the /api/match endpoint.

Pipeline:
  1. Skill extraction from both texts (curated skills list + aliases).
  2. Chunk the CV into sentence groups and embed every chunk with the
     384-dim all-MiniLM-L6-v2 Sentence Transformer model (run through
     fastembed / ONNX Runtime so it fits a small CPU instance, no PyTorch).
  3. Index the CV chunks in FAISS and retrieve, for every requirement line
     of the job description, the CV chunk that best supports it.
  4. Hybrid score = 0.6 * skill coverage + 0.4 * semantic coverage.

If the embedding model or FAISS cannot be loaded, the matcher falls back to
a lexical (bag-of-words cosine) similarity so the endpoint never fails; the
response says which method was used.
"""

from __future__ import annotations

import json
import re
import threading
from collections import Counter, OrderedDict
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SKILL_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4

# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

_BASE_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "rust",
    "kotlin", "swift", "scala", "r",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "bigquery", "snowflake",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "streamlit", "html", "css", "graphql", "rest api", "microservices",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "linux", "git", "ci/cd", "jenkins", "github actions", "gitlab",
    "kafka", "rabbitmq", "spark", "airflow", "nginx",
    "machine learning", "deep learning", "nlp", "computer vision", "llm",
    "rag", "transformers", "tensorflow", "pytorch", "scikit-learn", "xgboost",
    "pandas", "numpy", "faiss", "vector database", "mlflow", "mlops",
    "hugging face", "langchain", "embeddings",
    "agile", "scrum", "jira",
]

# variant -> canonical name
_ALIASES = {
    "rest": "rest api", "rest apis": "rest api", "restful": "rest api",
    "restful api": "rest api", "restful apis": "rest api",
    "microservice": "microservices",
    "ml": "machine learning",
    "dl": "deep learning",
    "natural language processing": "nlp",
    "large language model": "llm", "large language models": "llm", "llms": "llm",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    "k8s": "kubernetes",
    "nodejs": "node.js", "node": "node.js",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "ci cd": "ci/cd", "cicd": "ci/cd", "ci/cd pipelines": "ci/cd",
    "sklearn": "scikit-learn", "scikit learn": "scikit-learn",
    "google cloud": "gcp", "google cloud platform": "gcp",
    "amazon web services": "aws",
    "huggingface": "hugging face",
    "go": "golang",
    "vector db": "vector database", "vector store": "vector database",
    "vector databases": "vector database", "vector dbs": "vector database",
    "vector stores": "vector database",
    "sentence transformers": "embeddings", "sentence-transformers": "embeddings",
}

# Terms that are also common English words: only match them case-sensitively.
_CASE_SENSITIVE = {"go": "Go", "r": "R", "rest": "REST", "node": "Node"}


def _load_skills() -> List[str]:
    skills = set(_BASE_SKILLS)
    path = Path(__file__).resolve().parents[2] / "data" / "skills_db.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        skills.update(s.lower() for s in data.get("core_skills", []) if isinstance(s, str))
    except Exception:
        pass
    skills.discard("go")
    skills.discard("microservice")
    return sorted(skills)


SKILLS = _load_skills()


def _pattern(term: str) -> str:
    # Word boundaries that also work for terms such as "c++", "c#", "node.js".
    return r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#])"


def extract_skills(text: str) -> List[str]:
    """Return the canonical skills mentioned in text (no guessing fallback)."""
    if not text:
        return []
    lower = text.lower()
    # "sentence-transformers" is the embeddings library, not the transformers skill
    core_text = re.sub(r"sentence[- ]transformers", "sentence_embeddings_lib", lower)
    found = set()
    for skill in SKILLS:
        if skill in _CASE_SENSITIVE:
            continue
        if re.search(_pattern(skill), core_text):
            found.add(skill)
    for variant, canonical in _ALIASES.items():
        if variant in _CASE_SENSITIVE:
            if re.search(_pattern(_CASE_SENSITIVE[variant]), text):
                found.add(canonical)
        elif re.search(_pattern(variant), lower):
            found.add(canonical)
    # "R" as a language: only when written as a capital R word.
    if re.search(r"(?<![\w+#.])R(?![\w+#'])", text):
        found.add("r")
    return sorted(found)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, min_chars: int = 40, max_chars: int = 400) -> List[str]:
    """One chunk per CV bullet / sentence; very short fragments are merged forward."""
    pieces: List[str] = []
    for line in re.split(r"\n+", text or ""):
        line = re.sub(r"^[\s\-•*→>]+", "", line).strip()
        if not line:
            continue
        pieces.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())

    pieces = list(dict.fromkeys(pieces))
    chunks: List[str] = []
    carry = ""
    for piece in pieces:
        piece = f"{carry} {piece}".strip() if carry else piece
        if len(piece) < min_chars:
            carry = piece
            continue
        carry = ""
        chunks.append(piece[:max_chars])
    if carry:
        if chunks and len(chunks[-1]) + len(carry) < max_chars:
            chunks[-1] = f"{chunks[-1]} {carry}"
        else:
            chunks.append(carry)
    return chunks


_REQUIREMENT_WORDS = re.compile(
    r"\b(experience|experienced|knowledge|proficien\w*|skills?|familiar\w*|degree|years?|requires?|required|"
    r"must|ability|able to|understanding|expertise|background|qualif\w*|certif\w*|strong|hands-on|"
    r"you will|you'll|responsib\w*|build|design|develop|deploy|manage|lead)\b", re.I)


def _job_sentences(jd_text: str) -> List[str]:
    lines = []
    for line in re.split(r"\n+", jd_text or ""):
        line = re.sub(r"^[\s\-•*→>]+", "", line).strip()
        lines.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return list(dict.fromkeys(lines))  # drop repeated sentences, keep order


def requirement_lines(jd_text: str, limit: int = 25) -> List[str]:
    """Job-description sentences that state requirements or duties.

    Company boilerplate ("About us", benefits, mission statements) is skipped:
    on the public fit benchmark, scoring only requirement-like sentences
    raised the semantic signal's test AUC from 0.53 to 0.57.
    """
    sentences = _job_sentences(jd_text)
    lines = [l for l in sentences if len(l.split()) >= 4]
    reqs = [l for l in lines if _REQUIREMENT_WORDS.search(l) or extract_skills(l)]
    return (reqs or lines or sentences)[:limit]


# ---------------------------------------------------------------------------
# Embedding backends
# ---------------------------------------------------------------------------

class _Embedder:
    """Lazily loads the ONNX MiniLM model; thread-safe, loaded once."""

    CACHE_SIZE = 20000

    def __init__(self) -> None:
        self._model = None
        self._error: Optional[str] = None
        self._lock = threading.Lock()
        # text -> normalised vector; CV and JD lines repeat a lot across requests
        self._cache: "OrderedDict[str, np.ndarray]" = OrderedDict()
        self._cache_lock = threading.Lock()

    def load(self) -> bool:
        if self._model is not None:
            return True
        if self._error is not None:
            return False
        with self._lock:
            if self._model is None and self._error is None:
                try:
                    from fastembed import TextEmbedding

                    self._model = TextEmbedding(model_name=MODEL_NAME)
                    print(f"[MATCH] Loaded embedding model {MODEL_NAME}")
                except Exception as e:  # missing package, download failure, ...
                    self._error = f"{type(e).__name__}: {e}"
                    print(f"[MATCH] Embedding model unavailable, using lexical fallback: {self._error}")
        return self._model is not None

    @property
    def status(self) -> str:
        if self._model is not None:
            return "embeddings"
        if self._error is not None:
            return "lexical"
        return "loading"

    @property
    def error(self) -> Optional[str]:
        return self._error

    def embed(self, texts: List[str]) -> np.ndarray:
        with self._cache_lock:
            missing = list(dict.fromkeys(t for t in texts if t not in self._cache))
        if missing:
            vecs = np.array(list(self._model.embed(missing)), dtype="float32")
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vecs = vecs / norms
            with self._cache_lock:
                for t, v in zip(missing, vecs):
                    self._cache[t] = v
                while len(self._cache) > self.CACHE_SIZE:
                    self._cache.popitem(last=False)
        with self._cache_lock:
            out = []
            for t in texts:
                v = self._cache.get(t)
                if v is None:  # evicted between the two locks; embed directly
                    v = np.array(list(self._model.embed([t]))[0], dtype="float32")
                    v = v / (np.linalg.norm(v) or 1.0)
                else:
                    self._cache.move_to_end(t)
                out.append(v)
        return np.stack(out).astype("float32")


embedder = _Embedder()


def warm_up() -> None:
    """Load the model in the background so the first request is fast."""
    threading.Thread(target=embedder.load, daemon=True).start()


def _search(cv_vecs: np.ndarray, jd_vecs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Best CV chunk for every JD line: FAISS inner-product index, numpy fallback."""
    try:
        import faiss

        index = faiss.IndexFlatIP(cv_vecs.shape[1])
        index.add(cv_vecs)
        scores, idx = index.search(jd_vecs, 1)
        return scores[:, 0], idx[:, 0]
    except Exception:
        sims = jd_vecs @ cv_vecs.T
        return sims.max(axis=1), sims.argmax(axis=1)


_TOKEN = re.compile(r"[a-z][a-z0-9+#.]{1,}")
_STOP = set(
    "the and for with you your our are will have has this that from into who what "
    "able work working experience strong knowledge skills using use years year team "
    "role job plus etc including such well good about their they them can must "
    "should would also within across".split()
)


def _bow(text: str) -> Counter:
    return Counter(t for t in _TOKEN.findall(text.lower()) if t not in _STOP)


def _lexical_sim(a: Counter, b: Counter) -> float:
    common = set(a) & set(b)
    num = sum(a[t] * b[t] for t in common)
    den = sqrt(sum(v * v for v in a.values())) * sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _semantic_to_percent(sim: float) -> float:
    """Map MiniLM cosine similarity to 0..1. ~0.2 is unrelated, ~0.7+ is a strong match."""
    return float(min(1.0, max(0.0, (sim - 0.2) / 0.5)))


def _lexical_to_percent(sim: float) -> float:
    return float(min(1.0, max(0.0, sim / 0.5)))


def match(resume_text: str, jd_text: str, top_k: int = 5) -> Dict:
    resume_text = (resume_text or "").strip()
    jd_text = (jd_text or "").strip()

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)
    matched = sorted(set(resume_skills) & set(jd_skills))
    missing = sorted(set(jd_skills) - set(resume_skills))
    extra = sorted(set(resume_skills) - set(jd_skills))
    skill_score = len(matched) / len(jd_skills) if jd_skills else None

    cv_chunks = chunk_text(resume_text)
    jd_lines = requirement_lines(jd_text)

    evidence: List[Dict] = []
    semantic_score = 0.0
    method = "none"

    if cv_chunks and jd_lines:
        if embedder.load():
            method = "embeddings"
            cv_vecs = embedder.embed(cv_chunks)
            jd_vecs = embedder.embed(jd_lines)
            sims, idx = _search(cv_vecs, jd_vecs)
            per_line = [_semantic_to_percent(float(s)) for s in sims]
        else:
            method = "lexical"
            cv_bows = [_bow(c) for c in cv_chunks]
            sims_list, idx_list = [], []
            for line in jd_lines:
                lb = _bow(line)
                scores = [_lexical_sim(lb, cb) for cb in cv_bows]
                best = int(np.argmax(scores))
                sims_list.append(scores[best])
                idx_list.append(best)
            sims, idx = np.array(sims_list), np.array(idx_list)
            per_line = [_lexical_to_percent(float(s)) for s in sims]

        semantic_score = float(np.mean(per_line))
        order = np.argsort(-np.array(per_line))
        for i in order[:top_k]:
            supported = per_line[i] > 0
            evidence.append({
                "requirement": jd_lines[i],
                "cv_evidence": cv_chunks[int(idx[i])] if supported else None,
                "similarity": round(float(sims[i]), 3),
            })

    if skill_score is None:
        overall = semantic_score
    else:
        overall = SKILL_WEIGHT * skill_score + SEMANTIC_WEIGHT * semantic_score

    weak = [jd_lines[i] for i in np.argsort(np.array(per_line))[:3]] if cv_chunks and jd_lines else []

    suggestions: List[str] = []
    if missing:
        suggestions.append(
            "If you have used these, name them explicitly in your CV: " + ", ".join(missing[:8])
        )
    if weak and semantic_score < 0.75:
        suggestions.append(
            "Requirements your CV supports least, add a bullet with evidence for: "
            + " | ".join(w[:90] for w in weak[:2])
        )
    if not re.search(r"\d+\s?%|\d{2,}", resume_text):
        suggestions.append("Add measurable results (percentages, volumes, time saved).")
    if not suggestions:
        suggestions.append("Strong match. Mirror the job's wording for your top 3 skills in your summary.")

    pct = lambda v: round(v * 100, 1)  # noqa: E731
    return {
        "match_score": pct(overall),
        "skill_score": None if skill_score is None else pct(skill_score),
        "semantic_score": pct(semantic_score),
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
        "evidence": evidence,
        "suggestions": suggestions,
        "method": method,
        "model": MODEL_NAME if method == "embeddings" else None,
        "weights": {"skills": SKILL_WEIGHT, "semantic": SEMANTIC_WEIGHT},
    }
