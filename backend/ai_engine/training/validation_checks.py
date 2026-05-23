# validation_checks.py — AI Engine Logic Validation
# Ensures rule systems (scoring, risk, and role prediction) are logically sound.

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.m4_role_classifier import predict_role
from modules.m5_skill_extractor import extract_skills
from modules.m6_scoring import calculate_score
from modules.m7_risk import predict_risk


def run_checks():
    """Run simulated data points through the pipeline to verify logic invariants."""
    print("🔍 Running AI Engine Logic Validations...")

    # 1. Test case: Excellent Resume
    good_text = "Experienced Senior Software Engineer with 8+ years building scalable backends using Python, Django, AWS, and PostgreSQL. Led a team of 5 developers to deliver a massive microservices rewrite. Education: B.S. in Computer Science. Certified AWS Solutions Architect. Skills: Machine Learning, Docker, Kubernetes, CI/CD, Agile, Team Management, Mentoring."
    
    print("\n[Case 1: Strong Profile]")
    role1 = predict_role(good_text)
    skills1 = extract_skills(good_text)
    score1 = calculate_score(good_text, skills1, role1)
    risk1 = predict_risk(score1, skills1, good_text)
    
    print(f"   Role: {role1['predicted_role']} ({role1['confidence_pct']}%)")
    print(f"   Skills: {skills1['total']}")
    print(f"   Score: {score1['total_score']} ({score1['level']})")
    print(f"   Risk:  {risk1['risk_probability']}% ({risk1['risk_level']})")
    
    # Invariant: Excellent resume should score high and have low risk
    assert score1['total_score'] > 55, f"Expected high score, got {score1['total_score']}"
    assert risk1['risk_level'] in ["Low", "Medium"], f"Expected Low/Medium risk, got {risk1['risk_level']}"

    # 2. Test case: Empty/Terrible Resume
    bad_text = "I want a job. I know basic HTML."
    
    print("\n[Case 2: Weak Profile]")
    role2 = predict_role(bad_text)
    skills2 = extract_skills(bad_text)
    score2 = calculate_score(bad_text, skills2, role2)
    risk2 = predict_risk(score2, skills2, bad_text)

    print(f"   Role: {role2['predicted_role']} ({role2['confidence_pct']}%)")
    print(f"   Skills: {skills2['total']}")
    print(f"   Score: {score2['total_score']} ({score2['level']})")
    print(f"   Risk:  {risk2['risk_probability']}% ({risk2['risk_level']})")
    
    # Invariant: Terrible resume should score low and have high risk
    assert score2['total_score'] < 40, f"Expected low score, got {score2['total_score']}"
    assert risk2['risk_level'] == "High", f"Expected High risk, got {risk2['risk_level']}"
    
    # Invariant: Risk must correlate inversely with score
    assert score1['total_score'] > score2['total_score'], "Score logic failed (good < bad)"
    assert risk1['risk_probability'] < risk2['risk_probability'], "Risk logic failed (good > bad)"

    print("\n✅ All logic validation checks passed successfully!")


if __name__ == "__main__":
    run_checks()
