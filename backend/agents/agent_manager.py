import os
import json
import logging
from extensions import db
from models.resume import Resume
from agents.resume_parser_agent import parse_resume_with_ai
from agents.ats_scorer_agent import score_resume_ai
from agents.skill_gap_agent import analyze_skill_gaps

logger = logging.getLogger("CareerForge")

def run_full_analysis(resume_text, domain, user_id, filename):
    """
    Orchestrate the AI analysis pipeline:
    Parse -> Score -> Gaps -> Save
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or api_key in ["your_key_here", "get-yours-free-at-console.anthropic.com"]:
        return {
            "success": False,
            "status_code": 503,
            "error": "API key not configured",
            "message": "Please set ANTHROPIC_API_KEY in your .env file",
            "docs": "Get your free key at console.anthropic.com"
        }

    try:
        logger.info(f"Starting real AI analysis for user {user_id}, file {filename}")
        
        # 1. Load domain-specific keywords for context
        keyword_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "keywords", f"{domain.lower()}_keywords.json")
        keyword_library = {}
        if os.path.exists(keyword_file):
            with open(keyword_file, "r") as f:
                keyword_library = json.load(f)
        
        # 2. Parse Resume
        parsed_data = parse_resume_with_ai(resume_text, domain)
        
        # 3. Comprehensive ATS Scoring
        scoring_results = score_resume_ai(parsed_data, domain, keyword_library)
        
        # 4. Skill Gap Analysis
        gap_results = analyze_skill_gaps(parsed_data, domain, f"Mid-level {domain} Professional")
        
        # 5. Assemble final results
        final_analysis = {
            "parsed_data": parsed_data,
            "scoring": scoring_results,
            "skill_gaps": gap_results,
            "domain": domain
        }
        
        # 6. Save to Database
        resume_record = Resume()
        resume_record.user_id = user_id
        resume_record.filename = filename
        resume_record.ats_score = scoring_results.get("score", 0)
        resume_record.domain = domain
        resume_record.parsed_data = json.dumps(final_analysis)
        
        db.session.add(resume_record)
        db.session.commit()
        
        logger.info(f"AI analysis complete and saved for {filename}")
        return {
            "success": True,
            "resume_id": resume_record.id,
            "results": final_analysis
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Full AI analysis fail: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }
