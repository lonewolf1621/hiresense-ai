"""Tests for app/services/matcher.py (run with: pytest tests/)."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "matcher", Path(__file__).resolve().parents[1] / "app" / "services" / "matcher.py"
)
matcher = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(matcher)

CV = """Machine Learning Engineer
- Built a RAG system in Python with Sentence Transformer embeddings and a FAISS index.
- Served models with FastAPI and Docker on GCP, with CI/CD in GitHub Actions.
- Cut API latency from 400ms to under 200ms by redesigning a PostgreSQL schema."""

JD = """We need Python, NLP and LLM experience to build retrieval-augmented generation pipelines.
You will deploy models on AWS with Kubernetes and Docker.
Experience with vector databases and REST APIs is required."""


def test_skill_extraction_handles_symbols_and_aliases():
    skills = matcher.extract_skills("C++, C#, node.js, k8s, sklearn and retrieval-augmented generation")
    assert {"c++", "c#", "node.js", "kubernetes", "scikit-learn", "rag"} <= set(skills)


def test_common_words_are_not_skills():
    assert matcher.extract_skills("I will go home and rest, then node off.") == []


def test_match_returns_expected_shape():
    r = matcher.match(CV, JD)
    assert 0 <= r["match_score"] <= 100
    assert {"python", "docker", "rag"} <= set(r["matched_skills"])
    assert {"aws", "kubernetes", "llm", "nlp"} <= set(r["missing_skills"])
    assert r["evidence"] and r["method"] in {"embeddings", "lexical"}


def test_better_cv_scores_higher():
    strong = CV + "\n- Deployed LLM and NLP services on AWS with Kubernetes, using a vector database and REST APIs."
    assert matcher.match(strong, JD)["match_score"] > matcher.match(CV, JD)["match_score"]


def test_empty_inputs_do_not_crash():
    assert matcher.match("", JD)["match_score"] == 0
    assert matcher.match(CV, "")["match_score"] == 0
