# evaluate_models.py — AI Engine Evaluation Script
# Evaluates trained models, generates classification report and confusion matrix insights.

import os
import json
import joblib
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_BASE_DIR, "models")
_OUTPUT_DIR = os.path.join(_BASE_DIR, "outputs")

def evaluate():
    """Evaluate trained model on the held-out test set."""
    print("📊 Evaluating AI Engine Performance...")

    # Load artifacts
    try:
        model = joblib.load(os.path.join(_MODEL_DIR, "role_model.pkl"))
        vectorizer = joblib.load(os.path.join(_MODEL_DIR, "tfidf_vectorizer.pkl"))
        le = joblib.load(os.path.join(_MODEL_DIR, "label_encoder.pkl"))
        test_df = pd.read_csv(os.path.join(_MODEL_DIR, "test_data.csv"))
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please run train_models.py first.")
        return

    # Transform test set
    X_test_vec = vectorizer.transform(test_df["Clean_Text"])
    y_test = test_df["Label"]

    # Predict
    preds = model.predict(X_test_vec)

    # Metrics
    acc = accuracy_score(y_test, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, preds, average="weighted", zero_division=0)
    
    # Classification Report
    target_names = le.inverse_transform(range(len(le.classes_)))
    report_dict = classification_report(y_test, preds, target_names=target_names, output_dict=True, zero_division=0)

    # Compile JSON report
    performance_report = {
        "model_type": type(model).__name__,
        "dataset_size": {
            "test_samples": len(y_test)
        },
        "overall_metrics": {
            "accuracy": round(acc, 4),
            "precision_weighted": round(precision, 4),
            "recall_weighted": round(recall, 4),
            "f1_weighted": round(f1, 4)
        },
        "class_metrics": {}
    }

    print("\n--- Model Performance Summary ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("---------------------------------\n")

    # Add class metrics
    for tgt in target_names:
        if tgt in report_dict:
            performance_report["class_metrics"][tgt] = {
                "precision": round(report_dict[tgt]["precision"], 4),
                "recall": round(report_dict[tgt]["recall"], 4),
                "f1-score": round(report_dict[tgt]["f1-score"], 4),
                "support": report_dict[tgt]["support"]
            }

    # Save to JSON
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(_OUTPUT_DIR, "performance_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(performance_report, f, indent=2)

    print(f"✅ Full performance report saved to {report_path}")

if __name__ == "__main__":
    evaluate()
