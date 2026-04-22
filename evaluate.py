import json
from app.services.skill_extractor import extract_skills
from app.evaluation.evaluator import compute_metrics


with open("data/test_cases.json", "r") as f:
    test_cases = json.load(f)


all_metrics = []

for case in test_cases:
    predicted = extract_skills(case["resume"])
    actual = case["expected_skills"]

    metrics = compute_metrics(predicted, actual)
    all_metrics.append(metrics)

    print("\n--- Test Case ---")
    print("Predicted:", predicted)
    print("Actual:", actual)
    print("Metrics:", metrics)


# average metrics
avg_precision = sum(m["precision"] for m in all_metrics) / len(all_metrics)
avg_recall = sum(m["recall"] for m in all_metrics) / len(all_metrics)
avg_f1 = sum(m["f1_score"] for m in all_metrics) / len(all_metrics)

print("\n=== FINAL METRICS ===")
print("Precision:", round(avg_precision, 2))
print("Recall:", round(avg_recall, 2))
print("F1 Score:", round(avg_f1, 2))