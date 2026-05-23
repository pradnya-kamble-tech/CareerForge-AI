# m7_risk.py — AI Risk Prediction Model (Module 7)
# Predicts rejection probability based on score, features, and skills.

import os
import json
import math

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_THRESHOLDS_PATH = os.path.join(_BASE_DIR, "models", "risk_thresholds.json")

# Default risk thresholds
_DEFAULT_THRESHOLDS = {
    "low_max": 30,
    "medium_max": 60,
    "score_weight": 0.50,
    "skill_weight": 0.25,
    "completeness_weight": 0.25,
}


def _load_thresholds():
    """Load risk thresholds from disk or use defaults."""
    if os.path.exists(_THRESHOLDS_PATH):
        with open(_THRESHOLDS_PATH, "r") as f:
            return json.load(f)
    return dict(_DEFAULT_THRESHOLDS)


def predict_risk(score_result, skills_result, resume_text=""):
    """
    Predict the rejection probability for a resume.

    Args:
        score_result (dict): Output from m6_scoring.calculate_score().
        skills_result (dict): Output from m5_skill_extractor.extract_skills().
        resume_text (str): Raw resume text for additional analysis.

    Returns:
        dict: {
            "risk_probability": float (0-100),
            "risk_level": str (Low/Medium/High),
            "risk_icon": str,
            "risk_factors": list of str,
            "mitigations": list of str,
            "reason": str
        }
    """
    thresholds = _load_thresholds()
    score = score_result.get("total_score", score_result.get("score", 50))
    total_skills = skills_result.get("total", 0)
    dimensions = score_result.get("dimensions", {})
    categorized = skills_result.get("categorized", {})

    # ── Calculate risk probability (inversely proportional to score) ──
    # Base risk from score (0-100 → 100-0)
    score_risk = max(0, 100 - score)

    # Skill deficiency risk
    if total_skills == 0:
        skill_risk = 100
    elif total_skills <= 3:
        skill_risk = 80
    elif total_skills <= 6:
        skill_risk = 55
    elif total_skills <= 10:
        skill_risk = 35
    elif total_skills <= 15:
        skill_risk = 20
    else:
        skill_risk = max(5, 30 - total_skills)

    # Completeness risk
    completeness = dimensions.get("completeness", 50)
    completeness_risk = max(0, 100 - completeness)

    # ── Dynamic Penalties ──
    penalty = 0
    if dimensions.get("skill_relevance", 50) < 40:
        penalty += 15  # Missing critical skills penalty
    if dimensions.get("role_alignment", 50) < 40:
        penalty += 10  # Weak alignment penalty

    # Weighted combination with dynamic penalties
    w = thresholds
    base_risk = (
        score_risk * w["score_weight"]
        + skill_risk * w["skill_weight"]
        + completeness_risk * w["completeness_weight"]
    )
    
    # Ensure strong inverse correlation with strict bounds
    risk_prob = base_risk + penalty
    risk_prob = round(min(max(risk_prob, 0), 100), 1)

    # ── Risk level ──
    if risk_prob <= thresholds["low_max"]:
        risk_level = "Low"
        risk_icon = "low"
    elif risk_prob <= thresholds["medium_max"]:
        risk_level = "Medium"
        risk_icon = "medium"
    else:
        risk_level = "High"
        risk_icon = "high"

    # ── Risk factors ──
    factors = []
    mitigations = []

    if total_skills <= 5:
        factors.append(f"Low skill count ({total_skills} detected)")
        mitigations.append("Add more technical and domain-specific skills to your resume.")

    if len(categorized) <= 2:
        factors.append(f"Limited skill diversity ({len(categorized)} categories)")
        mitigations.append("Diversify skills across multiple categories (e.g., cloud, databases, soft skills).")

    if dimensions.get("experience_quality", 50) < 40:
        factors.append("Weak experience indicators")
        mitigations.append("Add detailed work experience with quantified achievements.")

    if dimensions.get("completeness", 50) < 50:
        factors.append("Incomplete resume sections")
        mitigations.append("Include Education, Experience, Skills, Projects, and Certifications sections.")

    if dimensions.get("skill_relevance", 50) < 40:
        factors.append("Low skill-role alignment")
        mitigations.append("Tailor skills specifically to the target job role.")

    if dimensions.get("role_alignment", 50) < 40:
        factors.append("Unclear career direction")
        mitigations.append("Add a clear professional summary highlighting your target role.")

    if score < 40:
        factors.append(f"Low overall score ({score}/100)")
        mitigations.append("Strengthen your resume with relevant skills, projects, and certifications.")

    if not factors:
        factors.append("Resume looks well-rounded")
        mitigations.append("Keep your resume updated with new skills and achievements.")

    # ── Reason text ──
    reason_parts = [f"Risk level: {risk_level} ({risk_prob}% rejection probability)."]
    reason_parts.append(f"Resume score is {score}/100 with {total_skills} skill(s) detected.")
    if risk_level == "High":
        reason_parts.append("This indicates significant gaps that may lead to rejection.")
    elif risk_level == "Medium":
        reason_parts.append("Your profile meets basic requirements but has room for improvement.")
    else:
        reason_parts.append("Your profile demonstrates strong alignment with industry expectations.")

    return {
        "risk_probability": risk_prob,
        "risk_level": risk_level,
        "risk_icon": risk_icon,
        "risk_factors": factors,
        "mitigations": mitigations,
        "suggestions": mitigations,  # Legacy compatibility
        "reason": " ".join(reason_parts),
    }


def save_thresholds(thresholds=None):
    """Save risk thresholds to JSON."""
    if thresholds is None:
        thresholds = _DEFAULT_THRESHOLDS
    os.makedirs(os.path.dirname(_THRESHOLDS_PATH), exist_ok=True)
    with open(_THRESHOLDS_PATH, "w") as f:
        json.dump(thresholds, f, indent=2)


# Save defaults on first load
save_thresholds()
