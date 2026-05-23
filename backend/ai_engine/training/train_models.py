# train_models.py — AI Engine Training Pipeline
# Handles data splitting, vectorization, and training multiple classifiers.

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report

import sys
# Add parent dir to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.m1_role_mapping import load_dataset, get_label_encoder
from modules.m2_preprocessing import preprocess
from modules.m3_features import create_vectorizer

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_BASE_DIR, "models")
_OUTPUT_DIR = os.path.join(_BASE_DIR, "outputs")


def train():
    """Execute the full training pipeline."""
    print("🚀 Starting AI Engine Training Pipeline...")
    
    # Ensure dirs exist
    os.makedirs(_MODEL_DIR, exist_ok=True)
    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    # 1. Load Data & Encode Labels
    print("\n[1/5] Loading dataset and encoding labels...")
    df = load_dataset()
    le = get_label_encoder()
    
    # Add mapped labels
    df["Label"] = le.transform(df["Category_Clean"])
    
    # Save label encoder
    joblib.dump(le, os.path.join(_MODEL_DIR, "label_encoder.pkl"))
    print(f"✅ Loaded {len(df)} resumes across {len(le.classes_)} categories.")

    # 2. Text Preprocessing
    print("\n[2/5] Preprocessing resume texts... (This may take a minute)")
    df["Clean_Text"] = df["Resume_str"].apply(preprocess)
    print("✅ Preprocessing complete.")

    # 3. Train/Test Split (80/20 stratified)
    print("\n[3/5] Splitting dataset (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        df["Clean_Text"], df["Label"], 
        test_size=0.2, random_state=42, stratify=df["Label"]
    )
    print(f"✅ Training samples: {len(X_train)} | Testing samples: {len(X_test)}")

    # 4. Feature Extraction (TF-IDF)
    print("\n[4/5] Fitting TF-IDF Vectorizer (Upgraded 15000 features)...")
    vectorizer = create_vectorizer(max_features=15000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    joblib.dump(vectorizer, os.path.join(_MODEL_DIR, "tfidf_vectorizer.pkl"))
    print(f"✅ Vocabulary size: {len(vectorizer.get_feature_names_out())}")

    # 5. Model Training & Comparison
    print("\n[5/5] Training models and comparing performance...")
    
    svc_calibrated = CalibratedClassifierCV(LinearSVC(C=5.0, random_state=42, max_iter=2000), method='sigmoid')
    lr = LogisticRegression(C=5.0, max_iter=2000, random_state=42)
    rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)

    models = {
        "NaiveBayes": MultinomialNB(alpha=0.1),
        "LogisticRegression": lr,
        "RandomForest": rf,
        "LinearSVC": svc_calibrated,
        "Ensemble (LR+RF+SVC)": VotingClassifier(
            estimators=[("LR", lr), ("RF", rf), ("SVC", svc_calibrated)],
            voting="soft"
        )
    }

    best_model_name = None
    best_accuracy = 0
    best_model = None

    results = []

    for name, model in models.items():
        print(f"   ► Training {name}...")
        model.fit(X_train_vec, y_train)
        preds = model.predict(X_test_vec)
        acc = accuracy_score(y_test, preds)
        print(f"     Accuracy: {acc:.4f}")
        
        results.append({"model": name, "accuracy": acc})
        
        if acc > best_accuracy:
            best_accuracy = acc
            best_model_name = name
            best_model = model

    print(f"\n🏆 Best Model Selected: {best_model_name} (Accuracy: {best_accuracy:.4f})")
    
    # Save the best model
    joblib.dump(best_model, os.path.join(_MODEL_DIR, "role_model.pkl"))
    
    # Save test sets for evaluation script
    pd.DataFrame({"Clean_Text": X_test, "Label": y_test}).to_csv(
        os.path.join(_MODEL_DIR, "test_data.csv"), index=False
    )

    print("\n✅ Training Pipeline Completed Successfully.")
    print(f"Artifacts saved to: {_MODEL_DIR}")


if __name__ == "__main__":
    train()
