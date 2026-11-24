"""Which matching signals actually predict fit? (cnamuangtoun/resume-job-description-fit)

Computes several candidate signals for every pair, then:
  1. ranks each single signal by ROC-AUC on the TRAIN split,
  2. fits a logistic regression on all signals using TRAIN only,
  3. reports everything once on TEST.

Train and test share some resumes, so the learned model is also evaluated
with a resume-grouped split of TRAIN (no resume in both folds) to check it is
not memorising candidates.

    pip install -r requirements.txt "datasets>=2.19,<3" "pyarrow==16.1.0" scikit-learn
    python benchmarks/feature_experiment.py --out benchmarks/results
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import matcher  # noqa: E402

LABELS = {"No Fit": 0, "Potential Fit": 1, "Good Fit": 2}
REQ_WORDS = re.compile(
    r"\b(experience|experienced|knowledge|proficien|skill|familiar|degree|years?|require|must|"
    r"ability|able to|understanding|expertise|background|qualif|certif|strong|hands-on)\b", re.I)

FEATURES = [
    "skill_coverage", "skill_jaccard", "n_jd_skills", "n_cv_skills", "n_matched_skills",
    "sem_mean_all", "sem_mean_req", "sem_top5", "sem_max", "doc_cosine", "lex_cosine",
]


def requirement_like(lines):
    req = [l for l in lines if REQ_WORDS.search(l) or matcher.extract_skills(l)]
    return req or lines


def features(cv: str, jd: str) -> dict:
    cv_sk, jd_sk = set(matcher.extract_skills(cv)), set(matcher.extract_skills(jd))
    inter = cv_sk & jd_sk
    cv_chunks = matcher.chunk_text(cv)[:80]
    jd_lines = matcher.requirement_lines(jd, limit=60)
    f = {
        "skill_coverage": len(inter) / len(jd_sk) if jd_sk else 0.0,
        "skill_jaccard": len(inter) / len(cv_sk | jd_sk) if (cv_sk | jd_sk) else 0.0,
        "n_jd_skills": float(len(jd_sk)),
        "n_cv_skills": float(len(cv_sk)),
        "n_matched_skills": float(len(inter)),
        "lex_cosine": matcher._lexical_sim(matcher._bow(cv), matcher._bow(jd)),
    }
    if not cv_chunks or not jd_lines:
        f.update(sem_mean_all=0.0, sem_mean_req=0.0, sem_top5=0.0, sem_max=0.0, doc_cosine=0.0)
        return f
    req = requirement_like(jd_lines)
    cv_v = matcher.embedder.embed(cv_chunks)
    jd_v = matcher.embedder.embed(jd_lines)
    req_v = matcher.embedder.embed(req)
    best_all = (jd_v @ cv_v.T).max(axis=1)
    best_req = (req_v @ cv_v.T).max(axis=1)
    doc_cv, doc_jd = cv_v.mean(axis=0), jd_v.mean(axis=0)
    f.update(
        sem_mean_all=float(best_all.mean()),
        sem_mean_req=float(best_req.mean()),
        sem_top5=float(np.sort(best_req)[-5:].mean()),
        sem_max=float(best_all.max()),
        doc_cosine=float(doc_cv @ doc_jd / (np.linalg.norm(doc_cv) * np.linalg.norm(doc_jd) or 1.0)),
    )
    return f


def build(rows):
    X, y, groups = [], [], []
    for r in rows:
        f = features(r["resume_text"], r["job_description_text"])
        X.append([f[k] for k in FEATURES])
        y.append(LABELS[r["label"]])
        groups.append(hash(r["resume_text"]))
    return np.array(X, float), np.array(y), np.array(groups)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="benchmarks/results")
    args = ap.parse_args()

    from datasets import load_dataset
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import spearmanr

    assert matcher.embedder.load(), matcher.embedder.error
    ds = load_dataset("cnamuangtoun/resume-job-description-fit")
    t0 = time.time()
    Xtr, ytr, gtr = build(ds["train"])
    Xte, yte, gte = build(ds["test"])
    print(f"features for {len(ytr)} train + {len(yte)} test pairs in {time.time() - t0:.0f}s")

    shared = len(set(gtr) & set(gte))
    single = {}
    for j, name in enumerate(FEATURES):
        single[name] = {
            "train_auc_fit_vs_nofit": round(roc_auc_score(ytr > 0, Xtr[:, j]), 4),
            "test_auc_fit_vs_nofit": round(roc_auc_score(yte > 0, Xte[:, j]), 4),
            "test_spearman": round(float(spearmanr(Xte[:, j], yte).correlation), 4),
        }
    best_single = max(single, key=lambda k: single[k]["train_auc_fit_vs_nofit"])

    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    # resume-grouped CV on train
    cv_aucs = []
    for a, b in GroupKFold(n_splits=5).split(Xtr, ytr > 0, gtr):
        model.fit(Xtr[a], ytr[a] > 0)
        cv_aucs.append(roc_auc_score(ytr[b] > 0, model.predict_proba(Xtr[b])[:, 1]))
    model.fit(Xtr, ytr > 0)
    p = model.predict_proba(Xte)[:, 1]
    p_unseen = p[~np.isin(gte, gtr)]
    y_unseen = yte[~np.isin(gte, gtr)]
    coefs = dict(zip(FEATURES, np.round(model[-1].coef_[0], 3).tolist()))

    res = {
        "n_train": int(len(ytr)), "n_test": int(len(yte)),
        "test_resumes_also_in_train": int(shared), "test_resumes_total": int(len(set(gte))),
        "single_signals": single,
        "best_single_by_train_auc": best_single,
        "logistic_regression": {
            "train_grouped_cv_auc_mean": round(float(np.mean(cv_aucs)), 4),
            "train_grouped_cv_auc_std": round(float(np.std(cv_aucs)), 4),
            "test_auc_fit_vs_nofit": round(roc_auc_score(yte > 0, p), 4),
            "test_auc_good_vs_nofit": round(roc_auc_score(yte[yte != 1] == 2, p[yte != 1]), 4),
            "test_spearman": round(float(spearmanr(p, yte).correlation), 4),
            "test_auc_unseen_resumes_only": round(roc_auc_score(y_unseen > 0, p_unseen), 4) if len(set(y_unseen > 0)) > 1 else None,
            "n_test_unseen_resumes": int(len(y_unseen)),
            "standardised_coefficients": coefs,
            "intercept": round(float(model[-1].intercept_[0]), 4),
            "scaler_mean": dict(zip(FEATURES, np.round(model[0].mean_, 6).tolist())),
            "scaler_scale": dict(zip(FEATURES, np.round(model[0].scale_, 6).tolist())),
            "raw_coefficients": dict(zip(FEATURES, np.round(model[-1].coef_[0], 6).tolist())),
        },
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "feature_experiment.json").write_text(json.dumps(res, indent=2))
    print("RESULTS_JSON_START")
    print(json.dumps(res, indent=2))
    print("RESULTS_JSON_END")


if __name__ == "__main__":
    main()
