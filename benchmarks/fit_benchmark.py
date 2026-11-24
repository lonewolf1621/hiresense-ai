"""Benchmark HireSense matching on a public, labelled resume–job dataset.

Dataset: cnamuangtoun/resume-job-description-fit (Hugging Face), ~8k
resume / job-description pairs labelled "No Fit", "Potential Fit" or
"Good Fit" (train 6.2k, test 1.8k). The dataset card states no licence, so it
is downloaded at run time and not stored in this repository.

What is measured (HireSense is unsupervised, so nothing is trained here):
  * ROC-AUC of the match score for "fit" (Good or Potential) vs "No Fit"
  * ROC-AUC for "Good Fit" vs "No Fit"
  * Spearman correlation between the score and the 3-level label
  * the same for skill coverage alone and semantic coverage alone
  * the skill/semantic weight is tuned on a TRAIN subset only, then the
    tuned and the default (0.6/0.4) weights are both reported on TEST
  * throughput: pairs per hour with a cold embedding cache, on this machine

    pip install datasets
    python benchmarks/fit_benchmark.py --out benchmarks/results
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import matcher  # noqa: E402

LABELS = {"No Fit": 0, "Potential Fit": 1, "Good Fit": 2}


def auc(scores_pos, scores_neg) -> float:
    """ROC-AUC via the Mann-Whitney U statistic (ties count half)."""
    pos, neg = np.asarray(scores_pos, float), np.asarray(scores_neg, float)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    ranks = _rank(allv)
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def _rank(x):
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), float)
    xs = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and xs[j + 1] == xs[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a, b) -> float:
    ra, rb = _rank(np.asarray(a, float)), _rank(np.asarray(b, float))
    return float(np.corrcoef(ra, rb)[0, 1])


def score_pairs(rows):
    out = []
    for r in rows:
        m = matcher.match(r["resume_text"], r["job_description_text"])
        out.append({
            "label": LABELS[r["label"]],
            "skill": m["skill_score"] / 100 if m["skill_score"] is not None else None,
            "semantic": m["semantic_score"] / 100,
            "method": m["method"],
        })
    return out


def combined(s, w):
    return s["semantic"] if s["skill"] is None else w * s["skill"] + (1 - w) * s["semantic"]


def evaluate(scored, key):
    y = np.array([s["label"] for s in scored])
    v = np.array([key(s) for s in scored], float)
    return {
        "auc_fit_vs_nofit": round(auc(v[y > 0], v[y == 0]), 4),
        "auc_good_vs_nofit": round(auc(v[y == 2], v[y == 0]), 4),
        "spearman_vs_label": round(spearman(v, y), 4),
        "mean_score_by_label": {name: round(float(v[y == k].mean()) * 100, 1) for name, k in LABELS.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="benchmarks/results")
    ap.add_argument("--train-sample", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    from datasets import load_dataset

    ds = load_dataset("cnamuangtoun/resume-job-description-fit")
    train, test = ds["train"], ds["test"]
    print(f"train {len(train)}  test {len(test)}")

    assert matcher.embedder.load(), f"embedding model failed to load: {matcher.embedder.error}"

    # Throughput with a cold cache: first 100 test pairs.
    matcher.embedder._cache.clear()
    t0 = time.time()
    score_pairs(test.select(range(100)))
    cold = time.time() - t0
    matcher.embedder._cache.clear()

    rng = np.random.default_rng(args.seed)
    idx = rng.choice(len(train), size=min(args.train_sample, len(train)), replace=False)
    t0 = time.time()
    train_scored = score_pairs(train.select(sorted(idx.tolist())))
    print(f"scored {len(train_scored)} train pairs in {time.time() - t0:.0f}s")

    # Tune the skill weight on TRAIN only.
    grid = [round(w, 2) for w in np.arange(0, 1.0001, 0.05)]
    tuning = {w: evaluate(train_scored, lambda s, w=w: combined(s, w))["auc_fit_vs_nofit"] for w in grid}
    best_w = max(tuning, key=tuning.get)

    t0 = time.time()
    test_scored = score_pairs(test)
    test_seconds = time.time() - t0

    results = {
        "dataset": "cnamuangtoun/resume-job-description-fit (Hugging Face), test split",
        "n_test": len(test_scored),
        "test_label_counts": {name: int(sum(s["label"] == k for s in test_scored)) for name, k in LABELS.items()},
        "embedding_method": test_scored[0]["method"],
        "test": {
            "default_weights_0.6_skill_0.4_semantic": evaluate(test_scored, lambda s: combined(s, matcher.SKILL_WEIGHT)),
            f"tuned_on_train_{best_w}_skill": evaluate(test_scored, lambda s: combined(s, best_w)),
            "skill_coverage_only": evaluate([s for s in test_scored if s["skill"] is not None], lambda s: s["skill"]),
            "semantic_coverage_only": evaluate(test_scored, lambda s: s["semantic"]),
        },
        "tuning": {"train_pairs": len(train_scored), "best_skill_weight": best_w,
                   "train_auc_by_weight": {str(k): v for k, v in tuning.items()}},
        "throughput": {
            "cold_cache_pairs_per_hour": round(100 / cold * 3600),
            "cold_cache_seconds_per_pair": round(cold / 100, 3),
            "full_test_run_seconds": round(test_seconds, 1),
            "machine": f"{platform.system()} {platform.machine()}, {platform.python_version()}",
        },
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "fit_benchmark.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
