# m2_preprocessing.py — Text Preprocessing Pipeline (Module 2)
# Cleans and normalizes raw resume text for ML consumption.

import re
import html

# Common English stopwords (lightweight — no NLTK dependency required)
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "am", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "dare", "ought", "used", "this", "that", "these", "those", "i", "me",
    "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they",
    "them", "their", "theirs", "themselves", "what", "which", "who",
    "whom", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "as", "until", "while", "about", "between", "through",
    "during", "before", "after", "above", "below", "up", "down", "out",
    "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "if", "also", "into",
})

# Regex patterns (compiled once)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
_SPECIAL_CHAR_RE = re.compile(r"[^a-zA-Z0-9\s\+\#\./]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def strip_html(text):
    """Remove HTML tags and decode HTML entities."""
    text = _HTML_TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return text


import functools

@functools.lru_cache(maxsize=128)
def preprocess(text):
    """
    Full preprocessing pipeline: HTML strip → lowercase → URL/email removal →
    special char cleaning → stopword removal → whitespace normalization.

    Args:
        text (str): Raw resume text (may contain HTML).

    Returns:
        str: Cleaned, normalized text ready for feature extraction.
    """
    if not text or not isinstance(text, str):
        return ""

    # Step 1: Strip HTML
    text = strip_html(text)

    # Step 2: Lowercase
    text = text.lower()

    # Step 3: Remove URLs and emails
    text = _URL_RE.sub(" ", text)
    text = _EMAIL_RE.sub(" ", text)

    # Step 4: Remove special characters (keep letters, numbers, +, #, ., /)
    text = _SPECIAL_CHAR_RE.sub(" ", text)

    # Step 5: Remove stopwords
    tokens = text.split()
    tokens = [t for t in tokens if t not in _STOPWORDS and len(t) > 1]

    # Step 6: Normalize whitespace
    cleaned = " ".join(tokens)
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned).strip()

    return cleaned


def get_tokens(text):
    """Return the list of tokens from preprocessed text."""
    cleaned = preprocess(text)
    return cleaned.split() if cleaned else []


def get_stats(text):
    """Return basic statistical features from text."""
    tokens = get_tokens(text)
    return {
        "token_count": len(tokens),
        "unique_tokens": len(set(tokens)),
        "avg_word_length": round(sum(len(t) for t in tokens) / max(len(tokens), 1), 2),
        "char_count": len(" ".join(tokens)),
    }
