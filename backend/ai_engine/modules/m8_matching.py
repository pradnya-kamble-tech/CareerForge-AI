# m8_matching.py — Job Description Matching Engine (Module 8)
# Analyzes how well a resume matches a specific job description.

from sklearn.metrics.pairwise import cosine_similarity
from .m3_features import extract_tfidf
from .m5_skill_extractor import extract_skills

def match_resume_to_jd(resume_text, jd_text):
    """
    Match a resume against a job description.

    Args:
        resume_text (str): The candidate's resume text.
        jd_text (str): The job description text.

    Returns:
        dict: {
            "match_percentage": float,
            "matching_skills": list,
            "missing_skills": list,
            "analysis": str
        }
    """
    if not resume_text or not jd_text:
        return {
            "match_percentage": 0.0,
            "matching_skills": [],
            "missing_skills": [],
            "analysis": "Provide both resume and job description texts to match."
        }

    # 1. Cosine Similarity via TF-IDF
    resume_vec = extract_tfidf(resume_text)
    jd_vec = extract_tfidf(jd_text)
    
    # Cosine similarity returns [[score]]. Normalize it assuming 0.30 is a very strong match.
    raw_sim = cosine_similarity(resume_vec, jd_vec)[0][0]
    similarity_score = min((raw_sim / 0.30) * 100, 100.0)

    # 2. Skill Overlap Analysis
    resume_skills_result = extract_skills(resume_text)
    jd_skills_result = extract_skills(jd_text)

    resume_skills = set(s.lower() for s in resume_skills_result.get("skills", []))
    jd_skills = set(s.lower() for s in jd_skills_result.get("skills", []))

    matching_skills = list(resume_skills.intersection(jd_skills))
    missing_skills = list(jd_skills.difference(resume_skills))

    # Boost score slightly based on critical skill overlap
    jd_skill_count = len(jd_skills)
    skill_match_pct = (len(matching_skills) / jd_skill_count) * 100 if jd_skill_count > 0 else 0
    
    # Final blended score: 60% text similarity, 40% exact skill match
    final_score = (similarity_score * 0.6) + (skill_match_pct * 0.4)
    final_score = min(round(final_score, 1), 100.0)

    # Convert matching/missing sets back to original casings by looking up in the JD skills result
    orig_matching = [s for s in jd_skills_result.get("skills", []) if s.lower() in matching_skills]
    orig_missing = [s for s in jd_skills_result.get("skills", []) if s.lower() in missing_skills]

    if final_score >= 80:
        analysis = "Excellent match! You possess the key skills and experience outlined in the job description."
    elif final_score >= 60:
        analysis = "Good match. You have many of the required skills, but addressing the missing skills will strengthen your application."
    elif final_score >= 40:
        analysis = "Fair match. Consider highlighting experiences relevant to the job and acquiring the missing skills."
    else:
        analysis = "Low match. This job requires significant skills that are missing from your current profile."

    return {
        "match_percentage": final_score,
        "matching_skills": orig_matching,
        "missing_skills": orig_missing[:10], # Cap at top 10 missing to avoid overwhelming
        "analysis": analysis
    }
