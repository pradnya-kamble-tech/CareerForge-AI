# role_knowledge.py — Dataset-Driven Role Intelligence Engine
# Extracts real skill knowledge for each role from the Kaggle resume dataset.
# This converts the static dataset into a live role intelligence layer.

import os
import re
import json
from collections import Counter

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_BASE_DIR, "data", "resume_dataset.csv")
_CACHE_PATH = os.path.join(_BASE_DIR, "models", "role_knowledge_cache.json")

# ──────────────────── Skill vocabulary (aligned with m5_skill_extractor) ────────────────────
_SKILL_VOCAB = [
    # Programming
    "python", "java", "javascript", "c++", "c#", "typescript", "go", "rust",
    "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "perl", "dart",
    "shell", "bash", "powershell", "visual basic",
    # Web
    "html", "css", "react", "angular", "vue", "next.js", "node.js", "express",
    "flask", "django", "spring boot", "bootstrap", "tailwind", "jquery", "sass",
    "rest api", "graphql", "websocket", "fastapi", "laravel",
    # Data / AI / ML
    "machine learning", "deep learning", "nlp", "computer vision", "data analysis",
    "data visualization", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "keras", "matplotlib", "seaborn", "opencv", "nltk", "spacy",
    "artificial intelligence", "neural networks", "data mining",
    "big data", "hadoop", "spark", "tableau", "power bi",
    "statistical analysis", "regression", "classification", "clustering",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "redis", "firebase",
    "oracle", "cassandra", "dynamodb", "elasticsearch",
    # Cloud / DevOps
    "aws", "azure", "google cloud", "docker", "kubernetes",
    "ci/cd", "jenkins", "github actions", "terraform", "linux",
    "nginx", "apache", "heroku", "ansible",
    # Soft Skills
    "leadership", "communication", "teamwork", "problem solving",
    "time management", "critical thinking", "project management",
    "agile", "scrum", "kanban", "mentoring", "negotiation",
    "public speaking", "presentation", "decision making", "creativity",
    "analytical thinking", "innovation", "customer service", "research", "writing",
    # Tools
    "git", "github", "gitlab", "jira", "postman", "figma", "slack", "trello",
    "jupyter", "android studio", "xcode", "intellij", "eclipse", "pycharm",
    "microsoft office", "excel", "word", "powerpoint", "photoshop",
    "illustrator", "canva", "autocad", "solidworks",
    "sap", "salesforce", "hubspot", "maven", "gradle",
    # Domain
    "financial analysis", "risk management", "accounting", "budgeting",
    "forecasting", "auditing", "tax", "investment banking",
    "business intelligence", "market research", "supply chain",
    "operations management", "quality assurance", "six sigma",
    "lean manufacturing", "patient care", "clinical research", "medical records",
    "healthcare management", "nursing", "public health",
    "curriculum development", "lesson planning", "e-learning", "teaching",
    "training", "content creation", "legal research", "contract law",
    "corporate law", "compliance", "regulatory affairs",
    "digital marketing", "seo", "sem", "social media marketing",
    "content marketing", "email marketing", "google analytics",
    "brand management", "public relations", "advertising",
    "sales strategy", "crm", "lead generation",
    "mechanical engineering", "electrical engineering", "civil engineering",
    "structural analysis", "thermodynamics", "circuit design", "cad",
    "recruitment", "talent acquisition", "employee relations",
    "performance management", "compensation", "onboarding", "hris",
    "logistics", "procurement", "import export",
    "food safety", "nutrition", "hospitality", "event management",
    "fashion design", "textile", "agriculture technology",
    "embedded systems", "microservices", "api development",
    "web scraping", "automation", "data engineering", "etl", "data warehousing",
    "blockchain", "iot", "cybersecurity", "penetration testing",
    "network security", "encryption", "tcp/ip", "firewall", "vpn",
    "unit testing", "integration testing", "selenium", "pytest", "jest",
]

# Canonical skill name map (lowercase keyword → display name)
_SKILL_DISPLAY = {
    "python": "Python", "java": "Java", "javascript": "JavaScript",
    "c++": "C++", "c#": "C#", "typescript": "TypeScript", "go": "Go",
    "rust": "Rust", "kotlin": "Kotlin", "swift": "Swift",
    "ruby": "Ruby", "php": "PHP", "scala": "Scala", "r": "R",
    "matlab": "MATLAB", "perl": "Perl", "dart": "Dart",
    "bash": "Bash", "shell": "Shell", "powershell": "PowerShell",
    "html": "HTML", "css": "CSS", "react": "React",
    "angular": "Angular", "vue": "Vue.js", "next.js": "Next.js",
    "node.js": "Node.js", "express": "Express.js", "flask": "Flask",
    "django": "Django", "spring boot": "Spring Boot", "bootstrap": "Bootstrap",
    "tailwind": "Tailwind CSS", "jquery": "jQuery",
    "rest api": "REST API", "graphql": "GraphQL", "fastapi": "FastAPI",
    "machine learning": "Machine Learning", "deep learning": "Deep Learning",
    "nlp": "NLP", "computer vision": "Computer Vision",
    "data analysis": "Data Analysis", "data visualization": "Data Visualization",
    "pandas": "Pandas", "numpy": "NumPy", "scikit-learn": "Scikit-learn",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras",
    "artificial intelligence": "Artificial Intelligence",
    "statistical analysis": "Statistical Analysis",
    "big data": "Big Data", "hadoop": "Hadoop", "spark": "Spark",
    "tableau": "Tableau", "power bi": "Power BI",
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL",
    "mongodb": "MongoDB", "redis": "Redis", "firebase": "Firebase",
    "oracle": "Oracle", "elasticsearch": "Elasticsearch",
    "aws": "AWS", "azure": "Azure", "google cloud": "Google Cloud",
    "docker": "Docker", "kubernetes": "Kubernetes",
    "ci/cd": "CI/CD", "jenkins": "Jenkins", "terraform": "Terraform",
    "linux": "Linux", "nginx": "Nginx",
    "leadership": "Leadership", "communication": "Communication",
    "teamwork": "Teamwork", "problem solving": "Problem Solving",
    "time management": "Time Management", "critical thinking": "Critical Thinking",
    "project management": "Project Management", "agile": "Agile",
    "scrum": "Scrum", "negotiation": "Negotiation", "creativity": "Creativity",
    "analytical thinking": "Analytical Thinking", "research": "Research",
    "writing": "Writing", "customer service": "Customer Service",
    "git": "Git", "github": "GitHub", "jira": "Jira",
    "figma": "Figma", "excel": "Excel", "powerpoint": "PowerPoint",
    "photoshop": "Photoshop", "illustrator": "Illustrator", "canva": "Canva",
    "autocad": "AutoCAD", "solidworks": "SolidWorks",
    "sap": "SAP", "salesforce": "Salesforce", "hubspot": "HubSpot",
    "financial analysis": "Financial Analysis", "risk management": "Risk Management",
    "accounting": "Accounting", "budgeting": "Budgeting",
    "auditing": "Auditing", "tax": "Tax",
    "business intelligence": "Business Intelligence",
    "market research": "Market Research", "quality assurance": "Quality Assurance",
    "six sigma": "Six Sigma", "supply chain": "Supply Chain",
    "patient care": "Patient Care", "clinical research": "Clinical Research",
    "healthcare management": "Healthcare Management", "nursing": "Nursing",
    "curriculum development": "Curriculum Development",
    "lesson planning": "Lesson Planning", "teaching": "Teaching",
    "e-learning": "E-Learning", "content creation": "Content Creation",
    "training": "Training",
    "legal research": "Legal Research", "corporate law": "Corporate Law",
    "compliance": "Compliance",
    "digital marketing": "Digital Marketing", "seo": "SEO", "sem": "SEM",
    "social media marketing": "Social Media Marketing",
    "content marketing": "Content Marketing",
    "google analytics": "Google Analytics", "brand management": "Brand Management",
    "public relations": "Public Relations", "advertising": "Advertising",
    "sales strategy": "Sales Strategy", "crm": "CRM",
    "lead generation": "Lead Generation",
    "mechanical engineering": "Mechanical Engineering",
    "electrical engineering": "Electrical Engineering",
    "civil engineering": "Civil Engineering",
    "structural analysis": "Structural Analysis",
    "circuit design": "Circuit Design", "cad": "CAD",
    "recruitment": "Recruitment", "talent acquisition": "Talent Acquisition",
    "employee relations": "Employee Relations", "hris": "HRIS",
    "performance management": "Performance Management", "onboarding": "Onboarding",
    "food safety": "Food Safety", "nutrition": "Nutrition",
    "hospitality": "Hospitality", "fashion design": "Fashion Design",
    "blockchain": "Blockchain", "iot": "IoT", "cybersecurity": "Cybersecurity",
    "network security": "Network Security", "encryption": "Encryption",
    "vpn": "VPN", "firewall": "Firewall",
    "selenium": "Selenium", "pytest": "PyTest", "jest": "Jest",
    "microservices": "Microservices", "etl": "ETL",
    "data engineering": "Data Engineering", "automation": "Automation",
}

# Category name normalizer (dataset spelling → clean name)
_CAT_NORMALIZE = {
    "HR": "HR",
    "Designer": "Designer",
    "Information-Technology": "Information Technology",
    "Information Technology": "Information Technology",
    "Teacher": "Teacher",
    "Advocate": "Advocate",
    "Business-Development": "Business Development",
    "Business Development": "Business Development",
    "Healthcare": "Healthcare",
    "Fitness": "Fitness",
    "Agriculture": "Agriculture",
    "BPO": "BPO",
    "Sales": "Sales",
    "Consultant": "Consultant",
    "Digital-Media": "Digital Media",
    "Digital Media": "Digital Media",
    "Automobile": "Automobile",
    "Chef": "Chef",
    "Finance": "Finance",
    "Apparel": "Apparel",
    "Engineering": "Engineering",
    "Accountant": "Accountant",
    "Construction": "Construction",
    "Public-Relations": "Public Relations",
    "Public Relations": "Public Relations",
    "Banking": "Banking",
    "Arts": "Arts",
    "Aviation": "Aviation",
}


def _extract_skills_from_text(text: str) -> list:
    """Match skill vocab against a text blob, return list of canonical display names."""
    text_lower = text.lower()
    found = []
    for kw in _SKILL_VOCAB:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text_lower):
            display = _SKILL_DISPLAY.get(kw, kw.title())
            found.append(display)
    return found


def _extract_keywords(text: str, top_n: int = 20) -> list:
    """Extract frequent meaningful tokens (4+ chars, not in stopwords)."""
    _STOPS = {
        "this", "that", "with", "from", "have", "been", "they",
        "which", "will", "about", "also", "more", "were", "their",
        "into", "than", "then", "when", "where", "would", "could",
        "should", "your", "able", "make", "over", "such", "some",
        "work", "used", "well", "good", "team", "through", "other",
    }
    text_lower = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
    tokens = [t for t in text_lower.split() if len(t) >= 4 and t not in _STOPS]
    freq = Counter(tokens)
    return [w for w, _ in freq.most_common(top_n)]


def _build_knowledge_base() -> dict:
    """
    Read resume_dataset.csv and build per-role knowledge.
    Returns dict: role_name → {top_skills, common_keywords, avg_skill_count, resume_count}
    """
    import csv
    knowledge = {}
    role_texts = {}  # role → list of resume strings

    try:
        with open(_DATA_PATH, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_cat = row.get("Category", "").strip()
                # Support multiple common column name variants
                resume_text = (
                    row.get("Resume_str", "").strip()
                    or row.get("resume_str", "").strip()
                    or row.get("Resume", "").strip()
                    or row.get("resume", "").strip()
                )
                if not raw_cat or not resume_text:
                    continue
                clean_role = _CAT_NORMALIZE.get(raw_cat, raw_cat)
                if clean_role not in role_texts:
                    role_texts[clean_role] = []
                role_texts[clean_role].append(resume_text)
    except FileNotFoundError:
        return {}

    for role, texts in role_texts.items():
        # Combine all resumes for this role
        combined = " ".join(texts)

        # Extract skills per resume for avg count
        skill_counts = []
        skill_freq = Counter()
        for t in texts:
            skills = _extract_skills_from_text(t)
            skill_counts.append(len(skills))
            skill_freq.update(skills)

        # Top skills = most frequent across all resumes in this role
        top_skills = [s for s, _ in skill_freq.most_common(20)]

        # Common keywords from raw text
        common_keywords = _extract_keywords(combined, top_n=15)

        avg_skill_count = round(sum(skill_counts) / max(len(skill_counts), 1), 1)

        knowledge[role] = {
            "top_skills": top_skills,
            "common_keywords": common_keywords,
            "avg_skill_count": avg_skill_count,
            "resume_count": len(texts),
        }

    return knowledge


# ──────────────────── Cached access ────────────────────

_KNOWLEDGE: dict = {}


def _normalize_key(raw: str) -> str:
    """Convert cache keys like 'INFORMATION-TECHNOLOGY' → 'Information Technology'."""
    return raw.replace("-", " ").title()


def _load_knowledge() -> dict:
    """Load knowledge from cache or rebuild from dataset.
    Always returns keys in Title Case with spaces (e.g. 'Information Technology').
    """
    global _KNOWLEDGE
    if _KNOWLEDGE:
        return _KNOWLEDGE

    # Try cache first
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if raw:
                # Normalize all keys to consistent Title Case format
                _KNOWLEDGE = {_normalize_key(k): v for k, v in raw.items()}
                return _KNOWLEDGE
        except Exception:
            pass

    # Build from CSV (one-time; ~1-3 sec for 56MB)
    print("[RoleKnowledge] Building knowledge base from dataset...")
    _KNOWLEDGE = _build_knowledge_base()
    # Normalize keys from build too
    _KNOWLEDGE = {_normalize_key(k): v for k, v in _KNOWLEDGE.items()}

    # Persist cache
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_KNOWLEDGE, f, indent=2, ensure_ascii=False)
        print(f"[RoleKnowledge] Cached {len(_KNOWLEDGE)} roles.")
    except Exception as e:
        print(f"[RoleKnowledge] Cache write failed: {e}")

    return _KNOWLEDGE


def get_role_knowledge(role_name: str) -> dict:
    """
    Return dataset-derived knowledge for a given role.

    Args:
        role_name: Role name (e.g., "Teacher", "Information Technology").

    Returns:
        dict with keys: top_skills, common_keywords, avg_skill_count, resume_count
        Falls back to empty-safe defaults if role not found.
    """
    kb = _load_knowledge()

    # Direct match
    if role_name in kb:
        return kb[role_name]

    # Case-insensitive partial match
    role_lower = role_name.lower()
    for key in kb:
        if key.lower() == role_lower or key.lower() in role_lower or role_lower in key.lower():
            return kb[key]

    # Remove "Hybrid (X / Y)" prefix if present
    if role_name.startswith("Hybrid ("):
        inner = role_name[8:].rstrip(")")
        for part in inner.split(" / "):
            result = get_role_knowledge(part.strip())
            if result.get("top_skills"):
                return result

    # Fallback: return empty-safe defaults
    return {
        "top_skills": ["Communication", "Problem Solving", "Teamwork",
                        "Time Management", "Leadership", "Project Management"],
        "common_keywords": ["experience", "skills", "management", "team", "work"],
        "avg_skill_count": 10,
        "resume_count": 0,
    }


def get_skill_gap(extracted_skills: list, role_name: str) -> dict:
    """
    Compute data-driven skill gap between user skills and role requirements.
    Aligns with frontend script.js expectations.

    Args:
        extracted_skills: List of skill names found in the resume.
        role_name: Predicted role.

    Returns:
        {
            "missing_skills": [{"skill": str, "reason": str, "priority": str}, ...],
            "recommended_skills": [{"skill": str, "reason": str}, ...],
            "gap_percentage": int,
            "match_percentage": float,
            "summary": str,
            "target_role": str
        }
    """
    role_data = get_role_knowledge(role_name)
    top_skills = role_data.get("top_skills", [])

    extracted_lower = {s.lower() for s in extracted_skills}
    
    missing_list = []
    present_list = []
    
    for i, skill in enumerate(top_skills):
        if skill.lower() in extracted_lower:
            present_list.append(skill)
        else:
            priority = "High" if i < 5 else "Medium" if i < 12 else "Low"
            missing_list.append({
                "skill": skill,
                "reason": f"Required for {role_name} profiles.",
                "priority": priority
            })

    total = len(top_skills)
    match_pct = round((len(present_list) / total) * 100, 1) if total else 0.0
    gap_pct = round(100 - match_pct)

    # Recommendations: top 3 missing skills
    recommended = [{"skill": m["skill"], "reason": "High impact on score."} for m in missing_list[:3]]

    return {
        "missing": missing_list[:10],            # Alias for tests
        "missing_skills": missing_list[:10],     # Cap for UI
        "recommended_skills": recommended,
        "gap_percentage": gap_pct,
        "match_percentage": match_pct,
        "top_skills": top_skills,
        "matched": present_list,
        "summary": f"{len(present_list)}/{total} role-critical skills found ({match_pct}% match)",
        "target_role": role_name
    }


def get_simulator_skills(role_name: str, extracted_skills: list) -> list:
    """
    Return the skills the simulator should offer: role's top skills minus already possessed.
    Always returns at least a handful of skills.
    """
    role_data = get_role_knowledge(role_name)
    top_skills = role_data.get("top_skills", [])
    extracted_lower = {s.lower() for s in extracted_skills}
    missing = [s for s in top_skills if s.lower() not in extracted_lower]
    # If nothing is missing (very complete resume), return all top skills
    if not missing:
        missing = top_skills[:10]
    return missing


def get_all_roles() -> list:
    """Return list of all roles with knowledge data."""
    return list(_load_knowledge().keys())


# Pre-warm the cache on module import (non-blocking in practice since it's fast after caching)
def preload():
    """Called once at server startup to warm the cache."""
    _load_knowledge()
