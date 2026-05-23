# m6_scoring.py — AI Resume Scoring Model (Module 6)
# Multi-dimension weighted scoring: skill relevance, volume, experience,
# role alignment, and completeness.

import os
import re
import json
import math

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WEIGHTS_PATH = os.path.join(_BASE_DIR, "models", "scoring_weights.json")

# Default scoring weights
_DEFAULT_WEIGHTS = {
    "skill_relevance": 0.30,
    "skill_volume": 0.20,
    "experience_quality": 0.20,
    "role_alignment": 0.15,
    "completeness": 0.15,
}

# Resume section keywords for completeness scoring
_SECTION_KEYWORDS = {
    "education": r"\b(education|degree|university|college|bachelor|master|phd|b\.?e|b\.?tech|m\.?tech|diploma|school)\b",
    "experience": r"\b(experience|work|employment|intern|position|job|company|worked|employed|role)\b",
    "skills": r"\b(skills|technical|proficiencies|competencies|expertise|technologies)\b",
    "projects": r"\b(projects|project|developed|built|created|implemented|designed)\b",
    "certifications": r"\b(certifications?|certified|certificate|license|accreditation)\b",
    "summary": r"\b(summary|objective|profile|about|overview|introduction)\b",
    "achievements": r"\b(achievements?|awards?|honors?|recognition|accomplishments?)\b",
}

# Experience-level keywords
_EXPERIENCE_KEYWORDS = {
    "senior": r"\b(senior|lead|principal|architect|director|manager|head|vp|chief)\b",
    "mid": r"\b(developer|engineer|analyst|specialist|consultant|coordinator)\b",
    "junior": r"\b(intern|trainee|junior|entry|graduate|fresher|assistant|apprentice)\b",
}

# Experience duration patterns
_DURATION_PATTERNS = [
    r"(\d+)\+?\s*years?",
    r"(\d+)\+?\s*yrs?",
]


def _load_weights():
    """Load scoring weights from disk or use defaults."""
    if os.path.exists(_WEIGHTS_PATH):
        with open(_WEIGHTS_PATH, "r") as f:
            return json.load(f)
    return dict(_DEFAULT_WEIGHTS)


def _score_skill_relevance(skills_list, role_skills, resume_text, max_score=100):
    """Score how well the resume matches the target role using TF-IDF cosine similarity."""
    if not role_skills or not resume_text:
        return min(len(skills_list) * 5, max_score)

    from .m3_features import extract_tfidf
    from sklearn.metrics.pairwise import cosine_similarity

    # Create an "ideal" resume context containing the role's critical skills repeated.
    ideal_text = " ".join(role_skills) * 5 

    try:
        resume_vec = extract_tfidf(resume_text)
        ideal_vec = extract_tfidf(ideal_text)
        
        sim = cosine_similarity(resume_vec, ideal_vec)[0][0]
        # Normalize: sim is usually 0.05 to 0.40 in this raw approach
        # A sim of 0.25 is very good.
        raw_score = min((sim / 0.30) * 100, 100)
        
        # Boost with literal skill overlap
        skills_lower = {s.lower() for s in skills_list}
        role_lower = {s.lower() for s in role_skills}
        overlap = len(skills_lower & role_lower)
        total_req = len(role_lower)
        
        if total_req > 0:
            literal_score = (overlap / total_req) * 100
        else:
            literal_score = 50
            
        final = (raw_score * 0.4) + (literal_score * 0.6)
        if overlap == total_req and total_req > 0:
            final = max(final, 95) # Perfect skill overlap gets top marks
            
        return min(round(final), max_score)
    except Exception:
        # Fallback if TF-IDF fails (e.g. vectorizer not trained)
        skills_lower = {s.lower() for s in skills_list}
        role_lower = {s.lower() for s in role_skills}
        overlap = len(skills_lower & role_lower)
        total = len(role_lower)
        if total == 0:
            return 50
        raw = (overlap / total) * 100
        return min(round(raw), max_score)


def _score_skill_volume(total_skills, domain="DEFAULT", max_score=100):
    """Score based on total number of skills detected, adjusted by domain."""
    expected_max = {
        "TECHNICAL": 25,
        "BUSINESS": 15,
        "CREATIVE": 15,
        "EDUCATION": 10,
        "HEALTHCARE": 12,
        "FINANCE": 15,
        "LEGAL": 10,
        "OPERATIONS": 12,
        "DEFAULT": 15
    }
    
    target = expected_max.get(domain, 15)
    
    if total_skills == 0:
        return 0
        
    ratio = total_skills / target
    if ratio >= 1.0:
        return min(95 + (total_skills - target), max_score)
    elif ratio >= 0.8:
        return 85
    elif ratio >= 0.6:
        return 70
    elif ratio >= 0.4:
        return 50
    elif ratio >= 0.2:
        return 30
    else:
        return 15


def _score_experience(resume_text, max_score=100):
    """Score experience quality from text analysis."""
    if not resume_text:
        return 0

    text_lower = resume_text.lower()
    score = 30  # Base score

    # Check for experience-level indicators
    for level, pattern in _EXPERIENCE_KEYWORDS.items():
        if re.search(pattern, text_lower):
            if level == "senior":
                score += 30
            elif level == "mid":
                score += 20
            elif level == "junior":
                score += 10
            break

    # Check for years of experience
    for pattern in _DURATION_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            years = int(match.group(1))
            score += min(years * 5, 30)
            break

    # Check for multiple positions/companies
    position_count = len(re.findall(r"\b(worked|employed|position|role|company|intern)\b", text_lower))
    score += min(position_count * 3, 15)

    return min(score, max_score)


def _score_role_alignment(confidence, max_score=100):
    """Score based on role classification confidence."""
    return min(round(confidence * 100), max_score)


def _score_completeness(resume_text, domain="DEFAULT", max_score=100):
    """Score based on presence of key resume sections, adjusted by domain."""
    if not resume_text:
        return 0

    text_lower = resume_text.lower()
    
    core_sections = ["experience", "education", "skills"]
    domain_sections = {
        "TECHNICAL": ["projects"],
        "BUSINESS": ["summary", "achievements"],
        "CREATIVE": ["projects", "summary"],
        "EDUCATION": ["certifications", "summary"],
        "HEALTHCARE": ["certifications"],
        "FINANCE": ["certifications", "achievements"],
        "LEGAL": ["summary", "achievements"],
        "OPERATIONS": ["summary"],
        "DEFAULT": ["projects"]
    }
    
    expected_sections = core_sections + domain_sections.get(domain, [])
    sections_found = 0

    for section in expected_sections:
        pattern = _SECTION_KEYWORDS.get(section)
        if pattern and re.search(pattern, text_lower):
            sections_found += 1

    raw = (sections_found / len(expected_sections)) * 100
    return min(round(raw), max_score)


def calculate_score(resume_text, skills_result, role_result):
    """
    Calculate a multi-dimension resume score (0-100).

    Args:
        resume_text (str): Raw resume text.
        skills_result (dict): Output from m5_skill_extractor.extract_skills().
        role_result (dict): Output from m4_role_classifier.predict_role().

    Returns:
        dict: {
            "total_score": int (0-100),
            "level": str,
            "dimensions": {dim: score, ...},
            "weights": {dim: weight, ...},
            "percentile_rank": int,
            "explanation": str
        }
    """
    # Dataset-driven role skills (preferred) — falls back to m5 static map if needed
    try:
        import sys, os as _os
        _rk_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "..")
        if _rk_path not in sys.path:
            sys.path.insert(0, _rk_path)
        from ai_engine.role_knowledge import get_role_knowledge as _get_rk
        _role_data = _get_rk(role_result.get("predicted_role", ""))
        _dataset_skills = _role_data.get("top_skills", [])
    except Exception:
        _dataset_skills = []

    from .m5_skill_extractor import get_skills_for_role
    from .m1_role_mapping import get_domain_for_role
    
    predicted_role = role_result.get("predicted_role", "")
    domain = get_domain_for_role(predicted_role)

    # Domain specific weights
    domain_weights = {
        "TECHNICAL": {"skill_relevance": 0.35, "skill_volume": 0.20, "experience_quality": 0.15, "role_alignment": 0.15, "completeness": 0.15},
        "EDUCATION": {"skill_relevance": 0.30, "skill_volume": 0.05, "experience_quality": 0.30, "role_alignment": 0.20, "completeness": 0.15},
        "BUSINESS": {"skill_relevance": 0.30, "skill_volume": 0.10, "experience_quality": 0.30, "role_alignment": 0.15, "completeness": 0.15},
        "HEALTHCARE": {"skill_relevance": 0.35, "skill_volume": 0.05, "experience_quality": 0.25, "role_alignment": 0.15, "completeness": 0.20},
        "CREATIVE": {"skill_relevance": 0.30, "skill_volume": 0.15, "experience_quality": 0.15, "role_alignment": 0.20, "completeness": 0.20},
        "FINANCE": {"skill_relevance": 0.35, "skill_volume": 0.05, "experience_quality": 0.25, "role_alignment": 0.15, "completeness": 0.20},
        "LEGAL": {"skill_relevance": 0.35, "skill_volume": 0.05, "experience_quality": 0.30, "role_alignment": 0.15, "completeness": 0.15},
        "OPERATIONS": {"skill_relevance": 0.25, "skill_volume": 0.10, "experience_quality": 0.30, "role_alignment": 0.20, "completeness": 0.15},
        "DEFAULT": _load_weights()
    }
    weights = domain_weights.get(domain, _load_weights())
    
    confidence = role_result.get("confidence", 0.5)
    skills_list = skills_result.get("skills", [])
    total_skills = skills_result.get("total", 0)

    # Prefer dataset-derived skills; fall back to static role map if dataset unavailable
    if _dataset_skills:
        role_skills = _dataset_skills
    else:
        role_skills = get_skills_for_role(predicted_role)

    # Calculate dimension scores
    dim_scores = {
        "skill_relevance": _score_skill_relevance(skills_list, role_skills, resume_text),
        "skill_volume": _score_skill_volume(total_skills, domain=domain),
        "experience_quality": _score_experience(resume_text),
        "role_alignment": _score_role_alignment(confidence),
        "completeness": _score_completeness(resume_text, domain=domain),
    }

    # Calculate weighted total
    total = 0
    for dim, score in dim_scores.items():
        w = weights.get(dim, 0.2)
        total += score * w
    total_score = min(round(total), 100)

    # Level classification
    if total_score >= 80:
        level = "Excellent"
    elif total_score >= 60:
        level = "Good"
    elif total_score >= 40:
        level = "Average"
    else:
        level = "Weak"

    # True statistical percentile estimation (Sigmoid mapping around mean 65)
    # mean=65, scale=12. Normal cdf approximation using tanh.
    z = (total_score - 65) / 12
    percentile = min(max(round((0.5 * (1 + math.tanh(z * 0.79788))) * 100), 1), 99)

    # Explanation
    explanations = []
    explanations.append(f"Resume score: {total_score}/100 ({level}).")
    best_dim = max(dim_scores, key=dim_scores.get)
    worst_dim = min(dim_scores, key=dim_scores.get)
    explanations.append(
        f"Strongest area: {best_dim.replace('_', ' ').title()} ({dim_scores[best_dim]}/100)."
    )
    if dim_scores[worst_dim] < 50:
        explanations.append(
            f"Needs improvement: {worst_dim.replace('_', ' ').title()} ({dim_scores[worst_dim]}/100)."
        )

    return {
        "total_score": total_score,
        "score": total_score,  # Legacy compatibility
        "level": level,
        "dimensions": dim_scores,
        "weights": weights,
        "percentile_rank": percentile,
        "explanation": " ".join(explanations),
        "breakdown": {
            "skill_score": dim_scores["skill_relevance"],
            "diversity_bonus": dim_scores["skill_volume"],
            "skills_detected": total_skills,
            "skills_count": total_skills,
            "categories_covered": len(skills_result.get("categorized", {})),
            "categories_count": len(skills_result.get("categorized", {})),
        },
        "reason": " ".join(explanations),  # Legacy compatibility
    }


def save_weights(weights=None):
    """Save scoring weights to JSON."""
    if weights is None:
        weights = _DEFAULT_WEIGHTS
    os.makedirs(os.path.dirname(_WEIGHTS_PATH), exist_ok=True)
    with open(_WEIGHTS_PATH, "w") as f:
        json.dump(weights, f, indent=2)


# Save defaults on first load
save_weights()
