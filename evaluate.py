"""Evaluate skill extraction on a hand-labelled set (data/eval/skill_extraction.json).

The set holds 40 short CV/JD sentences labelled with the skills they mention,
including traps (aliases, C++/C#, Node.js, and English words such as "go" and
"rest" that are not skills). Run: python evaluate.py
"""
import json
import sys
from pathlib import Path

from app.services.matcher import extract_skills

cases = json.loads(Path("data/eval/skill_extraction.json").read_text())
tp = fp = fn = 0
errors = []
for case in cases:
    pred, gold = set(extract_skills(case["text"])), set(case["skills"])
    tp += len(pred & gold)
    fp += len(pred - gold)
    fn += len(gold - pred)
    if pred != gold:
        errors.append((case["text"], sorted(pred - gold), sorted(gold - pred)))

precision = tp / (tp + fp) if tp + fp else 1.0
recall = tp / (tp + fn) if tp + fn else 1.0
f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
exact = 1 - len(errors) / len(cases)

print(f"Cases: {len(cases)}  labelled skills: {tp + fn}")
print(f"Micro precision: {precision:.3f}  recall: {recall:.3f}  F1: {f1:.3f}  exact-match: {exact:.3f}")
for text, extra, missed in errors:
    print(f"  - {text!r}\n      false positives: {extra}  missed: {missed}")

Path("data/eval/results.json").write_text(json.dumps(
    {"cases": len(cases), "precision": round(precision, 3), "recall": round(recall, 3),
     "f1": round(f1, 3), "exact_match": round(exact, 3)}, indent=1))
sys.exit(0 if f1 >= 0.9 else 1)
