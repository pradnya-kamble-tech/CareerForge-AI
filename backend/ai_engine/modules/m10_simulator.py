# m10_simulator.py — Digital Twin Simulator (Module 10)
# Re-runs scoring and risk analysis dynamically when new skills are simulated.
# Now role-knowledge-aware: uses dataset top_skills for context.

from .m5_skill_extractor import extract_skills
from .m6_scoring import calculate_score
from .m7_risk import predict_risk
from .m4_role_classifier import predict_role


def simulate(resume_text, appended_text):
    """
    Simulate the impact of adding new skills/text to the resume.

    Args:
        resume_text (str): The original resume text.
        appended_text (str): The new text/skills to add (e.g., 'AWS Kubernetes').

    Returns:
        dict: {
            "before": { role, score, risk },
            "after": { role, score, risk },
            "deltas": { score_change, risk_change },
            "role_context": { role, top_skills, is_role_relevant }
        }
    """
    # Normalize inputs
    resume_text = (resume_text or "").strip()
    appended_text = (appended_text or "").strip()

    if not resume_text:
        return {
            "before": {"score": 0, "risk_level": "Unknown", "risk_prob": 0, "skills_count": 0},
            "after":  {"score": 0, "risk_level": "Unknown", "risk_prob": 0, "skills_count": 0},
            "deltas": {"score_change": 0, "risk_change": 0, "skills_added": 0},
            "summary": "No resume text provided.",
            "role_context": {"role": "Unknown", "top_skills": [], "is_role_relevant": False},
        }

    # 1. Base State Calculation
    base_skills = extract_skills(resume_text)
    base_role   = predict_role(resume_text)
    base_score  = calculate_score(resume_text, base_skills, base_role)
    base_risk   = predict_risk(base_score, base_skills, resume_text)

    # 2. Simulated State Calculation
    combined_text = (resume_text + " " + appended_text).strip() if appended_text else resume_text
    new_skills = extract_skills(combined_text)
    new_role   = predict_role(combined_text)
    new_score  = calculate_score(combined_text, new_skills, new_role)
    new_risk   = predict_risk(new_score, new_skills, combined_text)

    # 3. Deltas
    score_change = new_score["total_score"] - base_score["total_score"]
    risk_change  = round(new_risk["risk_probability"] - base_risk["risk_probability"], 1)

    # 4. Role context — load dataset knowledge to enrich response
    predicted_role_name = base_role.get("predicted_role", "Unknown")
    role_top_skills  = []
    is_role_relevant = False

    try:
        import sys, os as _os
        _rk_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".."
        )
        if _rk_path not in sys.path:
            sys.path.insert(0, _rk_path)
        from ai_engine.role_knowledge import get_role_knowledge as _get_rk
        _role_data       = _get_rk(predicted_role_name)
        role_top_skills  = _role_data.get("top_skills", [])
        # Check if the injected text contains a role-relevant skill
        appended_lower   = appended_text.lower()
        is_role_relevant = any(
            skill.lower() in appended_lower or appended_lower in skill.lower()
            for skill in role_top_skills
        )
    except Exception:
        pass

    # 5. Build human-readable summary
    direction = "+" if score_change > 0 else ""
    if appended_text:
        summary = (
            f"Adding '{appended_text}' changes your score by {direction}{score_change} "
            f"and risk by {'+' if risk_change > 0 else ''}{risk_change}%."
        )
        if is_role_relevant:
            summary += f" This skill is highly relevant for {predicted_role_name} roles."
    else:
        summary = f"Current score: {base_score['total_score']}/100 for {predicted_role_name}."

    # 6. New roles unlocked (deterministic logic)
    new_roles = []
    if score_change >= 5:
        # Map specific skill clusters to career progression
        progression_map = {
            "Senior Engineering": ["aws", "kubernetes", "docker", "system design", "architecture"],
            "Lead Developer": ["leadership", "project management", "mentoring", "agile"],
            "Product Manager": ["market research", "strategy", "product design"],
            "Data Architect": ["big data", "spark", "hadoop", "data engineering"]
        }
        
        appended_lower = appended_text.lower()
        for role, skills in progression_map.items():
            if any(s in appended_lower for s in skills):
                new_roles.append(role)
        
        # Fallback if it's just a general score boost
        if not new_roles:
            if new_score["total_score"] > 85:
                new_roles = ["Solution Architect"]
            elif new_score["total_score"] > 70:
                new_roles = ["Senior Specialist"]

    return {
        "success": True,
        "before": {
            "score":        base_score["total_score"],
            "level":        base_score["level"],
            "risk_level":   base_risk["risk_level"],
            "risk":         base_risk["risk_level"], # Frontend compatibility
            "risk_prob":    base_risk["risk_probability"],
            "skills_count": base_skills["total"],
            "careers":      0 # Default to 0, app.py can enrich
        },
        "after": {
            "score":        new_score["total_score"],
            "level":        new_score["level"],
            "risk_level":   new_risk["risk_level"],
            "risk":         new_risk["risk_level"], # Frontend compatibility
            "risk_prob":    new_risk["risk_probability"],
            "skills_count": new_skills["total"],
            "careers":      5 # Default fallback
        },
        "deltas": {
            "score_change": score_change,
            "score_delta":  score_change, # For QA Harness
            "risk_change":  risk_change,
            "risk_delta":   risk_change,  # For QA Harness consistency
            "skills_added": new_skills["total"] - base_skills["total"],
        },
        "gain": score_change,
        "new_roles": new_roles,
        "role_context": {
            "role":             predicted_role_name,
            "top_skills":       role_top_skills[:8],
            "is_role_relevant": is_role_relevant,
        },
        "summary": summary,
    }
