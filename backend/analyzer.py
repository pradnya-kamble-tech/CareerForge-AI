import os
import re
import json
import logging

logger = logging.getLogger("CareerForge.analyzer")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_DIR = os.path.join(BASE_DIR, "..", "data", "keywords")

def load_domain_keywords(domain):
    """Load the JSON keyword file for a specific domain."""
    domain_map = {
        'Engineering': 'engineering',
        'Healthcare': 'healthcare',
        'Finance': 'finance',
        'Marketing': 'marketing',
        'Design': 'design',
        'Legal': 'legal',
        'HR': 'hr',
        'Operations': 'operations',
        'Education': 'education',
        'Sales': 'sales',
        'Hospitality': 'hospitality',
        'Construction': 'construction'
    }
    
    file_prefix = domain_map.get(domain, 'engineering')
    filepath = os.path.join(KEYWORDS_DIR, f"{file_prefix}_keywords.json")
    
    if not os.path.exists(filepath):
        logger.warning(f"Keyword file not found for domain: {domain}. Falling back to engineering.")
        filepath = os.path.join(KEYWORDS_DIR, "engineering_keywords.json")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading keywords for {domain}: {e}")
        return {
            "critical": [], "important": [], "bonus": [], 
            "action_verbs": [], "soft_skills": []
        }

def extract_skills(text, domain='Engineering'):
    """Extract matched and missing skills based on the domain's keyword list."""
    keywords = load_domain_keywords(domain)
    text_lower = text.lower()
    
    all_category_keys = ["critical", "important", "bonus", "soft_skills"]
    matched = []
    missing = []
    categorized = {cat: [] for cat in all_category_keys}
    
    for cat in all_category_keys:
        for kw in keywords.get(cat, []):
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
                matched.append(kw)
                categorized[cat].append(kw)
            else:
                missing.append(kw)
                
    return {
        "skills": matched,
        "missing": missing,
        "categorized": categorized,
        "total": len(matched)
    }

def score_resume(text, domain='Engineering'):
    """
    Score a resume 0-100 based on domain keywords and structural best practices.
    """
    keywords = load_domain_keywords(domain)
    text_lower = text.lower()
    score = 0
    breakdown = {}

    # 1. Critical Keywords (40 points)
    critical_kws = keywords.get("critical", [])
    if critical_kws:
        found_critical = [kw for kw in critical_kws if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)]
        crit_score = (len(found_critical) / len(critical_kws)) * 40
        score += crit_score
        breakdown["critical"] = round(crit_score, 1)

    # 2. Important Keywords (25 points)
    important_kws = keywords.get("important", [])
    if important_kws:
        found_important = [kw for kw in important_kws if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)]
        imp_score = (len(found_important) / len(important_kws)) * 25
        score += imp_score
        breakdown["important"] = round(imp_score, 1)

    # 3. Structure (20 points)
    struct_score = 0
    has_summary = bool(re.search(r'\b(summary|objective|profile)\b', text_lower))
    has_bullets = text.count('\n-') > 3 or text.count('\n*') > 3 or text.count('\u2022') > 3
    has_metrics = bool(re.search(r'\d+%', text)) or bool(re.search(r'\$\d+', text))
    
    if has_summary: struct_score += 5
    if has_bullets: struct_score += 10
    if has_metrics: struct_score += 5
    score += struct_score
    breakdown["structure"] = struct_score

    # 4. Action Verbs (10 points)
    verbs = keywords.get("action_verbs", [])
    if verbs:
        found_verbs = [v for v in verbs if re.search(r'\b' + re.escape(v.lower()) + r'\b', text_lower)]
        verb_score = (len(found_verbs) / len(verbs)) * 10
        score += verb_score
        breakdown["action_verbs"] = round(verb_score, 1)

    # 5. Length (5 points)
    word_count = len(text.split())
    length_score = 0
    if 400 <= word_count <= 800:
        length_score = 5
    elif 200 <= word_count <= 1000:
        length_score = 3
    score += length_score
    breakdown["length"] = length_score

    level = "Entry"
    if score >= 85: level = "Expert"
    elif score >= 70: level = "Advanced"
    elif score >= 50: level = "Intermediate"
    
    return {
        "score": round(score),
        "level": level,
        "breakdown": breakdown,
        "reason": f"Your resume scored {round(score)}/100 based on {domain} industry standards."
    }

def get_skill_gaps(text, domain, target_role=""):
    """Identify the most important keywords missing from the resume."""
    analysis = extract_skills(text, domain)
    missing = analysis["missing"]
    # Prioritize critical and important
    keywords = load_domain_keywords(domain)
    critical_missing = [kw for kw in keywords.get("critical", []) if kw in missing]
    important_missing = [kw for kw in keywords.get("important", []) if kw in missing]
    
    return {
        "critical_gaps": critical_missing[:5],
        "important_gaps": important_missing[:5],
        "summary": f"Missing {len(critical_missing)} critical skills identified in the {domain} domain."
    }

def detect_weaknesses(text):
    """Detect formatting and clarity issues."""
    weaknesses = []
    word_count = len(text.split())
    
    if word_count < 300:
        weaknesses.append("Resume is too short; consider expanding on your achievements.")
    elif word_count > 1200:
        weaknesses.append("Resume is too long; try to make it more concise (400-800 words is ideal).")
        
    if not re.search(r'\d+%', text) and not re.search(r'\$\d+', text):
        weaknesses.append("Lack of quantified achievements (e.g., %, $) makes it harder to measure impact.")
        
    if text.count('\n-') < 3 and text.count('\n*') < 3:
        weaknesses.append("Minimal use of bullet points; readability could be improved.")
        
    return {
        "weaknesses": weaknesses,
        "count": len(weaknesses)
    }

# Compatibility wrappers for app.py
def calculate_score(skill_results, text="", domain='Engineering'):
    return score_resume(text, domain)

def risk_analysis(score, skills):
    level = "Low"
    if score < 40: level = "High"
    elif score < 70: level = "Medium"
    
    return {
        "risk_level": level,
        "risk_icon": "⚠️" if level != "Low" else "✅",
        "reason": f"Risk level is {level} based on your ATS score.",
        "suggestions": ["Add more technical keywords.", "Quantify your achievements."]
    }

def career_prediction(skills, domain='Engineering'):
    return [{"role": f"{domain} Professional", "match_percentage": 100, "reason": "Based on your selected domain."}]

def skill_gap_analysis(skills, domain='Engineering', text=""):
    return get_skill_gaps(text, domain)

def simulate_evolution(current_skills, added_skill=""):
    return {"message": "Digital twin simulator is being updated."}

def get_all_skills():
    return ["Python", "Java", "React", "Nursing", "Accounting", "HR Management"]

def parse_resume_structured(text):
    return {"detected_domain": "Engineering", "seniority_level": "Entry"}

def sanitize_resume_text(text):
    return text.strip()

def analyze_resume_ai(text, domain=None):
    """
    Full AI analysis pipeline wrapper for testing.
    Auto-detects domain from text if not provided. 
    Returns a unified result dict compatible with the QA harness.
    """
    # Simple domain detection if not provided
    if not domain:
        text_lower = text.lower()
        if any(k in text_lower for k in ["nursing", "patient", "hipaa", "clinical"]):
            domain = "Healthcare"
        elif any(k in text_lower for k in ["marketing", "seo", "campaign", "brand"]):
            domain = "Marketing"
        elif any(k in text_lower for k in ["autocad", "mechanical", "cad", "solidworks"]):
            domain = "Engineering"
        else:
            domain = "Engineering"

    skill_results = extract_skills(text, domain=domain)
    score_results = score_resume(text, domain=domain)
    gap_results = get_skill_gaps(text, domain)

    # Role profile from ai_engine if available
    role_profile = {}
    try:
        import sys as _sys
        import os as _os
        _ai_path = _os.path.join(_os.path.dirname(__file__), "ai_engine")
        if _ai_path not in _sys.path:
            _sys.path.insert(0, _os.path.dirname(__file__))
        from ai_engine.role_knowledge import get_role_knowledge
        role_profile = get_role_knowledge(domain)
    except Exception:
        pass

    return {
        "score": score_results["score"],
        "level": score_results["level"],
        "skills": skill_results["skills"],
        "skill_gap": gap_results,
        "role_profile": role_profile,
        "domain": domain,
    }
