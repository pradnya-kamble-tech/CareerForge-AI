# m12_storage.py — Output Standardizer (Module 12)
# Standardizes all AI module outputs into a single JSON schema.

import uuid
from datetime import datetime

def build_output(role_result, skills_result, score_result, risk_result,
                 trajectory_result=None, explainer_result=None, jd_match_result=None,
                 role_knowledge_data=None, resume_text=None):
    """
    Build the master standardized JSON output for the AI Engine.

    Args:
        role_result (dict): M4 output.
        skills_result (dict): M5 output.
        score_result (dict): M6 output.
        risk_result (dict): M7 output.
        trajectory_result (dict, optional): M9 output.
        explainer_result (dict, optional): M11 output.
        jd_match_result (dict, optional): M8 output.

    Returns:
        dict: Standardized API response object.
    """
    response = {
        "analysis_id": f"ai-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engine_version": "2.0 (AI)",
        
        "role_prediction": {
            "predicted_role": role_result.get("predicted_role"),
            "confidence": role_result.get("confidence"),
            "confidence_pct": role_result.get("confidence_pct"),
            "icon": role_result.get("icon"),
            "top_3": role_result.get("top_3")
        },
        
        "skill_intelligence": {
            "total_skills": skills_result.get("total"),
            "skills_list": skills_result.get("skills"),
            "categorized": skills_result.get("categorized"),
            "category_distribution": skills_result.get("category_distribution"),
            "proficiency_hints": skills_result.get("proficiency_hints")
        },
        
        "score_analysis": {
            "total_score": score_result.get("total_score"),
            "level": score_result.get("level"),
            "percentile_rank": score_result.get("percentile_rank"),
            "dimensions": score_result.get("dimensions"),
            "breakdown": score_result.get("breakdown")
        },
        
        "risk_analysis": {
            "probability": risk_result.get("risk_probability"),
            "level": risk_result.get("risk_level"),
            "icon": risk_result.get("risk_icon"),
            "factors": risk_result.get("risk_factors"),
            "mitigations": risk_result.get("mitigations")
        }
    }

    # Add optional modules if provided
    if trajectory_result:
        response["career_trajectory"] = trajectory_result

    if explainer_result:
        def _format_bullets(items):
            if not items: return ""
            if isinstance(items, str): return items
            return "<br>• " + "<br>• ".join(items)
            
        response["xai_explanations"] = {
            "role": _format_bullets(explainer_result.get("role_explanation")),
            "score": _format_bullets(explainer_result.get("score_explanation")),
            "risk": _format_bullets(explainer_result.get("risk_explanation")),
            "top_keywords": [word for word, score in explainer_result.get("top_words", [])[:5]]
        }

    if jd_match_result:
        response["jd_match"] = jd_match_result

    # ──────────────────────────────────────────────────────────
    # ROLE PROFILE — Dataset-derived intelligence
    # ──────────────────────────────────────────────────────────
    if role_knowledge_data:
        response["role_profile"] = {
            "top_skills": role_knowledge_data.get("top_skills", []),
            "industry_keywords": role_knowledge_data.get("common_keywords", []),
            "avg_skill_count": role_knowledge_data.get("avg_skill_count", 0),
            "dataset_resumes": role_knowledge_data.get("resume_count", 0),
        }
    else:
        response["role_profile"] = {
            "top_skills": [],
            "industry_keywords": [],
            "avg_skill_count": 0,
            "dataset_resumes": 0,
        }

    # ──────────────────────────────────────────────────────────
    # NEW_FEATURES block — high-impact product features
    # ──────────────────────────────────────────────────────────
    new_features = {}

    # 1. Recruiter Auto Summary
    role_expl = (explainer_result or {}).get("role_explanation", [])
    score_expl = (explainer_result or {}).get("score_explanation", [])
    role_line = role_expl[0] if role_expl else f"Predicted role: {role_result.get('predicted_role', 'Unknown')}."
    score_line = score_expl[0] if score_expl else f"Score: {score_result.get('total_score', 0)}/100."
    # Strip HTML bullet markup if present
    import re as _re
    clean = lambda s: _re.sub(r"<[^>]+>", "", str(s)).strip()
    new_features["auto_summary"] = f"{clean(role_line)} {clean(score_line)}"

    # 2. Flight Risk Flag
    risk_level_val = risk_result.get("risk_level", "")
    new_features["flight_risk_flag"] = "High Mobility Risk" if risk_level_val == "High" else ""

    # 3. Competitiveness Index (placeholder — filled by analyzer.py after DB query)
    new_features["competitiveness"] = ""

    # 4. Micro Skill Clustering — category → count
    categorized = skills_result.get("categorized", {})
    skill_clusters = {cat: len(skills) for cat, skills in categorized.items() if skills}
    new_features["skill_clusters"] = skill_clusters

    # 5. Targeted Upskill ROI — top 3 missing skills → simulated score delta
    roi_suggestions = []
    # Removed simulated ROI logic as it depends on repeated AI runs which are slow and can be inconsistent
    new_features["roi_suggestions"] = roi_suggestions

    response["NEW_FEATURES"] = new_features

    # ──────────────────────────────────────────────────────────
    # LEGACY COMPATIBILITY LAYER
    # To prevent breaking app.py, we mirror the exact keys that 
    # the old rule-based analyzer returned.
    # ──────────────────────────────────────────────────────────
    # ──────────────────────────────────────────────────────────
    # NEW V2 HIGH-IMPACT DEMO FEATURES
    # ──────────────────────────────────────────────────────────
    
    # 1. AI Resume DNA Profile
    total_skills = skills_result.get("total", 0)
    skill_strength = min(round((total_skills / 25) * 100), 100)
    score_val = score_result.get("total_score", 0)
    if score_val >= 80: score_band = "Excellent"
    elif score_val >= 60: score_band = "Good"
    elif score_val >= 40: score_band = "Average"
    else: score_band = "Low"
    
    response["dna_profile"] = {
        "role_identity": role_result.get("predicted_role", "Unknown"),
        "skill_strength": skill_strength,
        "score_band": score_band,
        "risk_flag": risk_result.get("risk_level", "Unknown")
    }

    # 2. Recruiter Decision AI Assistant
    risk_prob = risk_result.get("risk_probability", 50)
    if score_val > 75 and risk_prob < 30:
        decision, reason = "Strong Hire", "Exceptional skill match with low attrition risk."
    elif score_val >= 50:
        decision, reason = "Consider", "Baseline requirements met. Evaluate cultural fit."
    else:
        decision, reason = "Reject", "High skill deficit or elevated risk projection."
        
    response["ai_decision"] = {
        "recommendation": decision,
        "reason": reason
    }

    # 4. Future Risk Predictor
    future_prob = min(risk_prob + (20 if total_skills < 15 else 10), 100)
    future_level = "High" if future_prob > 60 else "Medium" if future_prob > 30 else "Low"
    response["future_risk"] = {
        "projected_probability": future_prob,
        "projected_level": future_level,
        "analysis": f"Projected Risk in 6 months: {future_level} ({future_prob}%)"
    }

    # 5. Smart Role Switch Advisor
    top_3 = role_result.get("top_3", [])
    switch_suggestions = []
    if len(top_3) > 1:
        for alternative in top_3[1:]:
            switch_suggestions.append({
                "role": alternative.get("role", "Alternative Role"),
                "readiness": round(alternative.get("probability", 0) * 100, 1),
                "missing_skills": []  # Removed simulated pivot gaps — only show real readiness
            })
    response["role_switch_advisor"] = switch_suggestions

    # 6. Real Data Fields for Front-end Charts
    response["score_history"] = [] # To be populated by app.py from DB
    
    # Calculate more realistic salary projection based on role baseline if knowledge available
    salary_projection = []
    if role_knowledge_data:
        # Note: In a real system, these would come from an industry dataset
        # For stabilization, we use a conservative fixed baseline based on score
        base_lpa = 6 if score_val >= 80 else 4 if score_val >= 50 else 3
        multiplier = 1.15 # Fixed 15% annual growth
        for y in range(1, 6):
            salary_projection.append({
                "year": y,
                "value": round(base_lpa * (multiplier ** (y-1)), 1),
                "label": f"Year {y}"
            })
    response["salary_projection"] = salary_projection

    # ──────────────────────────────────────────────────────────
    # FLAT LEGACY KEYS — app.py accesses these directly
    # ──────────────────────────────────────────────────────────
    response["role"] = role_result.get("predicted_role", "Unknown")
    response["score"] = score_result.get("total_score", 0)
    response["skills"] = skills_result.get("skills", [])
    response["categorized_skills"] = skills_result.get("categorized", {})
    response["risk_level"] = risk_result.get("risk_level", "Unknown")
    response["risk_icon"] = risk_result.get("risk_icon", "⚠️")

    return response

