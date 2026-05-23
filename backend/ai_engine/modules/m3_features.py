# m3_features.py — Feature Extraction Engine (Module 3)
# Converts cleaned text into TF-IDF feature vectors and statistical features.

import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .m2_preprocessing import preprocess, get_stats

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_BASE_DIR, "models")

# Lazy-loaded singleton
_vectorizer = None


def _load_vectorizer():
    """Load the pre-trained TF-IDF vectorizer (fitted during training)."""
    global _vectorizer
    if _vectorizer is None:
        path = os.path.join(_MODEL_DIR, "tfidf_vectorizer.pkl")
        if os.path.exists(path):
            _vectorizer = joblib.load(path)
        else:
            raise FileNotFoundError(
                f"TF-IDF vectorizer not found at {path}. Run training first."
            )
    return _vectorizer


def create_vectorizer(max_features=15000, ngram_range=(1, 3)):
    """Create an advanced TF-IDF vectorizer (for V2.1 training)."""
    return TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=True,
        min_df=2,
        max_df=0.9,
    )


def save_vectorizer(vectorizer):
    """Save a fitted TF-IDF vectorizer to disk."""
    os.makedirs(_MODEL_DIR, exist_ok=True)
    path = os.path.join(_MODEL_DIR, "tfidf_vectorizer.pkl")
    joblib.dump(vectorizer, path)


import functools

@functools.lru_cache(maxsize=128)
def extract_tfidf(text):
    """
    Transform a single resume text into a TF-IDF feature vector.

    Args:
        text (str): Raw or cleaned resume text.

    Returns:
        scipy.sparse matrix: TF-IDF vector (1 × n_features).
    """
    vectorizer = _load_vectorizer()
    cleaned = preprocess(text)
    return vectorizer.transform([cleaned])


def extract_features(text):
    """
    Full feature extraction: TF-IDF vector + statistical features.

    Returns:
        dict with 'tfidf' (sparse matrix) and 'stats' (dict).
    """
    tfidf = extract_tfidf(text)
    stats = get_stats(text)
    return {"tfidf": tfidf, "stats": stats}


def get_top_tfidf_words(text, n=20):
    """Return the top N TF-IDF scoring words for a given text."""
    vectorizer = _load_vectorizer()
    cleaned = preprocess(text)
    vec = vectorizer.transform([cleaned])
    feature_names = vectorizer.get_feature_names_out()
    scores = vec.toarray()[0]
    top_indices = np.argsort(scores)[::-1][:n]
    return [(feature_names[i], round(float(scores[i]), 4)) for i in top_indices if scores[i] > 0]
