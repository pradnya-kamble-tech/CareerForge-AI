import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import analyze_resume_ai

def verify_stabilization():
    test_cases = [
        {"role": "Engineering", "text": "Experienced software engineer with extensive knowledge in Python SQL Git Java Kubernetes AWS. Built many scalable applications and managed microservices architectures effectively."},
        {"role": "Teacher", "text": "Dedicated educator with 5 years experience in Communication Curriculum Classroom Pedagogy Lesson Planning. Developed structured learning paths for diverse groups of students."},
        {"role": "Healthcare", "text": "Professional nurse specializing in Nursing Patient Care Medical Records Vital Signs HIPAA. Ensured high standards of patient safety and clinical excellence in hospital settings."},
        {"role": "Finance", "text": "Analytical finance professional with expertise in Accounting Tax Auditing Payroll Excel SAP. Managed quarterly budget reports and optimized tax compliance processes."},
    ]

    print("=== CAREERFORGE V2 STABILIZATION VERIFICATION ===\n")
    
    for case in test_cases:
        print(f"Testing domain: {case['role']}")
        # Mocking role classifier response for simplicity
        # In reality, predict_role would be called, but we want to check the downstream m12 and skill_gap
        result = analyze_resume_ai(case['text'])
        
        # Check Skill Gap
        gap = result.get("skill_gap", {})
        print(f"  Skill Gap Keys: {list(gap.keys())}")
        assert "missing_skills" in gap, "missing_skills missing"
        assert "recommended_skills" in gap, "recommended_skills missing"
        assert "gap_percentage" in gap, "gap_percentage missing"
        
        # Check Domain
        domain = result.get("domain")
        print(f"  Detected Domain: {domain}")
        
        # Check Simulator (via simulate_ai wrapper)
        from ai_engine.modules.m10_simulator import simulate
        sim = simulate(case['text'], "Project Management")
        print(f"  Simulator Success: {sim.get('success')}")
        assert sim.get("success"), "Simulator failed"
        assert "gain" in sim, "Gain missing from simulator"
        assert "new_roles" in sim, "new_roles missing from simulator"
        assert "level" in sim['before'], "Score level missing from simulator"
        
        print(f"  [PASS] {case['role']}\n")

    print("ALL CORE V2 FLOWS STABILIZED.")

if __name__ == "__main__":
    try:
        verify_stabilization()
    except Exception as e:
        print(f"VERIFICATION FAILED: {str(e)}")
        sys.exit(1)
