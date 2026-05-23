# m9_trajectory.py — Career Trajectory Predictor (Module 9)
# Forecasts logical next career steps based on current role and skills.

_NEXT_ROLES_MAP = {
    "software engineer": ["Senior Software Engineer", "Technical Lead", "Engineering Manager", "Software Architect"],
    "information technology": ["Senior IT Consultant", "IT Manager", "Systems Architect", "CTO"],
    "backend developer": ["Senior Backend Developer", "Software Architect", "Technical Lead"],
    "frontend developer": ["Senior Frontend Developer", "UI/UX Designer", "Frontend Tech Lead"],
    "full stack developer": ["Senior Full Stack Developer", "Software Architect", "Engineering Manager"],
    "data scientist": ["Senior Data Scientist", "Machine Learning Engineer", "Director of Data Science"],
    "machine learning engineer": ["Senior ML Engineer", "AI Architect", "Head of AI"],
    "devops engineer": ["Senior DevOps Engineer", "Cloud Architect", "Site Reliability Engineer"],
    "hr": ["Senior HR Manager", "Director of Human Resources", "VP of HR"],
    "designer": ["Senior Designer", "Art Director", "Creative Director", "UX/UI Lead"],
    "teacher": ["Senior Educator", "Curriculum Director", "Principal", "Education Administrator"],
    "business development": ["Senior BD Manager", "Director of Business Development", "VP of Sales"],
    "sales": ["Sales Manager", "Regional Sales Director", "VP of Sales"],
    "healthcare": ["Healthcare Administrator", "Clinical Director", "Medical Director"],
    "finance": ["Senior Financial Analyst", "Finance Manager", "VP of Finance", "CFO"],
    "accountant": ["Senior Accountant", "Audit Manager", "Controller", "CFO"],
    "engineering": ["Senior Engineer", "Engineering Manager", "Lead Engineer"],
    "consultant": ["Senior Consultant", "Principal Consultant", "Partner"],
    "digital media": ["Digital Media Manager", "Director of Digital Strategy", "CMO"],
    "public relations": ["PR Manager", "Director of Public Relations", "VP of Communications"],
}

_ROLE_TRANSITION_SKILLS = {
    "Technical Lead": ["Leadership", "System Architecture", "Mentoring", "Agile"],
    "Engineering Manager": ["Team Management", "Project Management", "Budgeting", "Leadership"],
    "Software Architect": ["System Architecture", "Cloud Computing", "Microservices", "Security"],
    "Machine Learning Engineer": ["Deep Learning", "TensorFlow", "PyTorch", "Model Deployment"],
    "Cloud Architect": ["AWS", "Azure", "Kubernetes", "System Architecture", "Cost Optimization"],
    "Data Scientist": ["Machine Learning", "Statistical Analysis", "Python", "Data Visualization"],
    "Senior Financial Analyst": ["Financial Modeling", "Forecasting", "Data Analysis", "Risk Management"],
    "Finance Manager": ["Team Management", "Budgeting", "Strategic Planning", "Leadership"],
    "Senior HR Manager": ["Employee Relations", "Strategic Planning", "Leadership", "Talent Acquisition"],
    "Art Director": ["Creative Direction", "Leadership", "Project Management", "Team Management"]
}

def predict_trajectory(predicted_role, skills_result):
    """
    Predict next roles and required skills for career progression.

    Args:
        predicted_role (str): The current predicted role (e.g., from M4).
        skills_result (dict): Currently possessed skills (e.g., from M5).

    Returns:
        dict: {
            "current_role": str,
            "next_roles": list of str,
            "skill_gaps": dict mapping next_role to list of missing skills
        }
    """
    role_lower = predicted_role.lower()
    
    # Exact match or find the closest sub-match
    next_roles = _NEXT_ROLES_MAP.get(role_lower)
    if not next_roles:
        # Fallback if the role isn't exactly mapped
        next_roles = ["Senior " + predicted_role, "Lead " + predicted_role, "Manager"]

    current_skills = set(s.lower() for s in skills_result.get("skills", []))
    
    skill_gaps = {}
    for next_role in next_roles:
        required_skills = _ROLE_TRANSITION_SKILLS.get(next_role, ["Leadership", "Strategic Planning", "Project Management"])
        missing = [skill for skill in required_skills if skill.lower() not in current_skills]
        skill_gaps[next_role] = missing

    return {
        "current_role": predicted_role,
        "next_roles": next_roles,
        "skill_gaps": skill_gaps,
        "path_analysis": f"Based on your profile as an {predicted_role}, your logical next steps focus on leadership or specialization."
    }
