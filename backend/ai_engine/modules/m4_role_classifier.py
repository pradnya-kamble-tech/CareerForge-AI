# m4_role_classifier.py — Role Classification Model (Module 4)
# Predicts the most suitable job role from resume text using a trained classifier.

import os
import joblib
import numpy as np

from .m2_preprocessing import preprocess
from .m1_role_mapping import get_role_icon

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_BASE_DIR, "models")

# Lazy-loaded singletons
_model = None
_vectorizer = None
_label_encoder = None


def _load_artifacts():
    """Load trained model, vectorizer, and label encoder once."""
    global _model, _vectorizer, _label_encoder
    if _model is None:
        _model = joblib.load(os.path.join(_MODEL_DIR, "role_model.pkl"))
        _vectorizer = joblib.load(os.path.join(_MODEL_DIR, "tfidf_vectorizer.pkl"))
        _label_encoder = joblib.load(os.path.join(_MODEL_DIR, "label_encoder.pkl"))
    return _model, _vectorizer, _label_encoder


import functools

@functools.lru_cache(maxsize=128)
def predict_role(resume_text):
    """
    Predict the job role from resume text.
    """
    model, vectorizer, le = _load_artifacts()

    cleaned = preprocess(resume_text)
    features = vectorizer.transform([cleaned])

    # Get prediction and probabilities
    predicted_idx = model.predict(features)[0]
    raw_predicted_role = le.inverse_transform([predicted_idx])[0]

    # Get probability distribution
    if hasattr(model, "predict_proba"):
        probas = model.predict_proba(features)[0]
    else:
        # Fallback for models without predict_proba
        probas = np.zeros(len(le.classes_))
        probas[predicted_idx] = 1.0

    # Build full distribution
    full_dist = {}
    for i, role in enumerate(le.classes_):
        full_dist[role] = round(float(probas[i]), 4)

    # Sort by probability for top-3
    sorted_roles = sorted(full_dist.items(), key=lambda x: x[1], reverse=True)
    top_3 = [
        {"role": role, "probability": round(prob, 4), "icon": get_role_icon(role)}
        for role, prob in sorted_roles[:3]
    ]

    confidence = round(float(probas[predicted_idx]), 4)
    needs_disambiguation = confidence < 0.60
    
    # Handle confusing hybrid roles
    final_role = raw_predicted_role
    if needs_disambiguation and len(top_3) >= 2:
        final_role = f"Hybrid ({top_3[0]['role']} / {top_3[1]['role']})"

    return {
        "predicted_role": final_role,
        "raw_role": raw_predicted_role,
        "confidence": confidence,
        "confidence_pct": round(confidence * 100, 1),
        "needs_disambiguation": needs_disambiguation,
        "icon": get_role_icon(raw_predicted_role),
        "top_3": top_3,
        "full_distribution": full_dist,
    }
