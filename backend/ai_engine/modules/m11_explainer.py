# m11_explainer.py — Explainable AI (XAI) Engine (Module 11)
# Generates human-readable explanations for AI decisions (role, score, risk).

from .m3_features import get_top_tfidf_words

def explain(resume_text, role_result, score_result, risk_result):
    """
    Generate human-readable explanations for the AI's predictions.

    Args:
        resume_text (str): Raw resume text.
        role_result (dict): Output from M4.
        score_result (dict): Output from M6.
        risk_result (dict): Output from M7.

    Returns:
        dict: {
            "role_explanation": str,
            "score_explanation": str,
            "risk_explanation": str,
            "top_words": list of tuples (word, score)
        }
    """
    # 1. Top Keywords (TF-IDF Feature Importance)
    top_words = get_top_tfidf_words(resume_text, n=15)
    word_list = [w for w, _ in top_words[:5]]

    # 2. Role Explanation (Bullet points)
    predicted = role_result.get("predicted_role", "Unknown")
    confidence = role_result.get("confidence_pct", 0)
    top_3 = role_result.get("top_3", [])
    
    role_expl = [
        f"Role Match: Classified as '{predicted}' with {confidence}% confidence."
    ]
    if word_list:
        role_expl.append(f"Key Drivers: Prediction influenced by TF-IDF keywords: {', '.join(word_list)}.")
    
    if len(top_3) > 1:
        competitor = top_3[1]["role"]
        competitor_prob = top_3[1]["probability"] * 100
        if competitor_prob > 15:
            role_expl.append(f"Hybrid Traits: Secondary alignment with {competitor} ({competitor_prob:.1f}%).")

    # 3. Score Explanation (Bullet points)
    score_expl = []
    score = score_result.get("total_score", 0)
    level = score_result.get("level", "Average")
    percentile = score_result.get("percentile_rank", 50)
    
    score_expl.append(f"Overall Score: {score}/100 ({level}) — top {100-percentile}% of applicants.")
    
    dims = score_result.get("dimensions", {})
    if dims:
        best_dim = max(dims, key=dims.get)
        worst_dim = min(dims, key=dims.get)
        score_expl.append(f"Strongest Asset: {best_dim.replace('_', ' ').title()} ({dims[best_dim]}/100).")
        if dims[worst_dim] < 60:
            score_expl.append(f"Action Required: Improve {worst_dim.replace('_', ' ').title()} ({dims[worst_dim]}/100).")

    # 4. Risk Explanation (Bullet points)
    risk_level = risk_result.get("risk_level", "Unknown")
    risk_prob = risk_result.get("risk_probability", 0)
    factors = risk_result.get("risk_factors", [])
    
    risk_expl = [
        f"Rejection Risk: {risk_prob}% ({risk_level} Risk Level)."
    ]
    
    if factors:
        for factor in factors[:3]:  # Top 3 risk factors
            risk_expl.append(f"Flag: {factor}.")
    else:
        risk_expl.append("Clearance: No major algorithmic red flags detected.")

    return {
        "role_explanation": role_expl,
        "score_explanation": score_expl,
        "risk_explanation": risk_expl,
        "top_words": top_words,
        "summary": "AI explanations generated via TF-IDF feature importance and multi-dimensional analysis."
    }
