# m5_skill_extractor.py — Skill Intelligence Engine (Module 5)
# AI-driven skill extraction with categorization and proficiency hints.

import os
import re
import json
import functools

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SKILL_DB_PATH = os.path.join(_BASE_DIR, "models", "skill_db.json")

# ──────────────────── Comprehensive Skill Database ────────────────────

_SKILL_DATABASE = {
    "technical": [
        # Programming Languages
        "Python", "Java", "JavaScript", "C", "C++", "C#", "TypeScript", "Go",
        "Rust", "Kotlin", "Swift", "Ruby", "PHP", "Scala", "R", "MATLAB",
        "Perl", "Dart", "Lua", "Objective-C", "Shell", "Bash", "PowerShell",
        "Visual Basic", "Assembly", "Fortran", "COBOL", "Haskell", "Elixir",
        # Web Development
        "HTML", "CSS", "React", "Angular", "Vue.js", "Next.js", "Node.js",
        "Express.js", "Flask", "Django", "Spring Boot", "Bootstrap",
        "Tailwind CSS", "jQuery", "SASS", "REST API", "GraphQL", "WebSocket",
        "FastAPI", "Laravel", "Ruby on Rails", "ASP.NET", "Svelte",
        # Data Science / AI / ML
        "Machine Learning", "Deep Learning", "Natural Language Processing",
        "Computer Vision", "Data Analysis", "Data Visualization",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
        "Matplotlib", "Seaborn", "OpenCV", "NLTK", "SpaCy",
        "Artificial Intelligence", "Neural Networks", "Data Mining",
        "Big Data", "Hadoop", "Spark", "Tableau", "Power BI",
        "Statistical Analysis", "Regression", "Classification", "Clustering",
        # Databases
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis",
        "Firebase", "Oracle", "Cassandra", "DynamoDB", "Elasticsearch",
        "MariaDB", "Neo4j", "CouchDB", "InfluxDB",
        # Cloud & DevOps
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
        "CI/CD", "Jenkins", "GitHub Actions", "Terraform", "Linux",
        "Nginx", "Apache", "Heroku", "Netlify", "Vercel",
        "Ansible", "Puppet", "Chef", "Vagrant", "CloudFormation",
        # Mobile Development
        "Android", "iOS", "React Native", "Flutter", "Swift UI",
        "Kotlin Multiplatform", "Xamarin", "Ionic",
        # Security
        "Cybersecurity", "Penetration Testing", "Ethical Hacking",
        "Network Security", "Encryption", "OWASP", "SSL/TLS",
        # Networking
        "TCP/IP", "DNS", "DHCP", "VPN", "Firewall", "Load Balancing",
        # Testing
        "Unit Testing", "Integration Testing", "Selenium", "JUnit",
        "PyTest", "Mocha", "Jest", "Cypress", "TestNG",
        # Other Technical
        "Blockchain", "IoT", "Embedded Systems", "Microservices",
        "API Development", "Web Scraping", "Automation",
        "Data Engineering", "ETL", "Data Warehousing",
    ],
    "soft_skills": [
        "Leadership", "Communication", "Teamwork", "Problem Solving",
        "Time Management", "Critical Thinking", "Project Management",
        "Agile", "Scrum", "Kanban", "Mentoring", "Negotiation",
        "Public Speaking", "Presentation", "Decision Making",
        "Conflict Resolution", "Adaptability", "Creativity",
        "Emotional Intelligence", "Strategic Planning", "Collaboration",
        "Attention to Detail", "Analytical Thinking", "Innovation",
        "Customer Service", "Interpersonal Skills", "Work Ethic",
        "Self-Motivation", "Flexibility", "Multitasking",
        "Organizational Skills", "Research", "Writing",
    ],
    "tools": [
        "Git", "GitHub", "GitLab", "Bitbucket", "VS Code",
        "Jira", "Postman", "Figma", "Slack", "Trello",
        "Jupyter Notebook", "Android Studio", "Xcode",
        "IntelliJ IDEA", "Eclipse", "Visual Studio", "PyCharm",
        "Sublime Text", "Vim", "Emacs", "Notion", "Confluence",
        "Asana", "Monday.com", "Microsoft Office", "Google Workspace",
        "Photoshop", "Illustrator", "Canva", "Sketch", "Adobe XD",
        "Blender", "AutoCAD", "SOLIDWORKS", "CATIA",
        "SAP", "Salesforce", "HubSpot", "Zendesk",
        "Webpack", "Babel", "npm", "yarn", "pip", "Maven", "Gradle",
        "Excel", "Word", "PowerPoint",
    ],
    "domain": [
        # Finance & Business
        "Financial Analysis", "Risk Management", "Accounting",
        "Budgeting", "Forecasting", "Auditing", "Tax",
        "Investment Banking", "Portfolio Management",
        "Business Intelligence", "Market Research", "Supply Chain",
        "Operations Management", "Quality Assurance", "Six Sigma",
        "Lean Manufacturing", "Total Quality Management",
        # Healthcare
        "Patient Care", "Clinical Research", "Medical Records",
        "Healthcare Management", "Nursing", "Pharmacy",
        "Public Health", "Epidemiology", "Telemedicine",
        # Education
        "Curriculum Development", "Lesson Planning", "E-Learning",
        "Training Development", "Content Creation", "Teaching",
        # Legal
        "Legal Research", "Contract Law", "Corporate Law",
        "Intellectual Property", "Compliance", "Regulatory Affairs",
        # Marketing & Sales
        "Digital Marketing", "SEO", "SEM", "Social Media Marketing",
        "Content Marketing", "Email Marketing", "Google Analytics",
        "Brand Management", "Public Relations", "Advertising",
        "Sales Strategy", "CRM", "Lead Generation",
        # Engineering
        "Mechanical Engineering", "Electrical Engineering",
        "Civil Engineering", "Chemical Engineering",
        "Structural Analysis", "Thermodynamics", "Fluid Mechanics",
        "Circuit Design", "CAD", "3D Modeling",
        # HR
        "Recruitment", "Talent Acquisition", "Employee Relations",
        "Performance Management", "Compensation", "Benefits Administration",
        "HRIS", "Onboarding", "Training",
        # Other Domains
        "Agriculture Technology", "Food Safety", "Nutrition",
        "Fashion Design", "Textile", "Hospitality",
        "Event Management", "Tourism", "Real Estate",
        "Logistics", "Procurement", "Import Export",
    ],
    "certifications": [
        "AWS Certified", "Azure Certified", "Google Cloud Certified",
        "PMP", "PRINCE2", "Scrum Master", "Product Owner",
        "CISSP", "CEH", "CompTIA", "CCNA", "CCNP",
        "CPA", "CFA", "FRM", "ACCA",
        "Six Sigma Green Belt", "Six Sigma Black Belt",
        "ITIL", "TOGAF", "COBIT",
        "Google Analytics Certified", "HubSpot Certified",
        "Salesforce Certified", "Oracle Certified",
        "Microsoft Certified", "Red Hat Certified",
        "Tableau Certified", "SAS Certified",
    ],
}

# Advanced Abbreviation & Synonym mapping for extraction refinement.
_SYNONYM_MAP = {
    "ml": "Machine Learning", "machine learning algorithms": "Machine Learning", "predictive modeling": "Machine Learning",
    "dl": "Deep Learning", "neural nets": "Deep Learning", "dnn": "Deep Learning",
    "nlp": "Natural Language Processing", "text mining": "Natural Language Processing",
    "cv": "Computer Vision", "image processing": "Computer Vision",
    "ai": "Artificial Intelligence",
    "js": "JavaScript", "ecmascript": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "rb": "Ruby",
    "db": "Database", "relational databases": "SQL", "rdbms": "SQL",
    "api": "API Development", "restful apis": "REST API", "micro-services": "Microservices",
    "ci/cd": "CI/CD", "continuous integration": "CI/CD", "continuous deployment": "CI/CD",
    "devops": "DevOps",
    "oop": "Object-Oriented Programming", "object oriented": "Object-Oriented Programming",
    "seo": "SEO", "search engine optimization": "SEO",
    "sem": "SEM", "search engine marketing": "SEM",
    "crm": "CRM", "customer relationship management": "CRM",
    "erp": "ERP", "enterprise resource planning": "ERP",
    "etl": "ETL", "extract transform load": "ETL",
    "bi": "Business Intelligence",
    "qa": "Quality Assurance", "software testing": "Quality Assurance",
    "ui": "User Interface", "ui design": "User Interface",
    "ux": "User Experience", "ux design": "User Experience",
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "Google Cloud", "google cloud platform": "Google Cloud",
    "k8s": "Kubernetes",
    "rn": "React Native",
    "k8": "Kubernetes",
    "k8s cluster": "Kubernetes",
    "golang": "Go"
}

# Pre-compile patterns (initialized once)
_patterns = {}


def _build_patterns():
    """Build regex patterns for all skills (done once)."""
    global _patterns
    if _patterns:
        return _patterns

    for category, skills in _SKILL_DATABASE.items():
        for skill in skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            _patterns[skill] = {
                "regex": re.compile(pattern, re.IGNORECASE),
                "category": category,
            }
    return _patterns


@functools.lru_cache(maxsize=256)
def extract_skills(resume_text):
    """
    Extract and categorize skills from resume text using pattern matching.

    Args:
        resume_text (str): Raw resume text.

    Returns:
        dict: {
            "skills": [flat list of matched skills],
            "categorized": {category: [skills], ...},
            "total": int,
            "category_distribution": {category: count},
            "proficiency_hints": {skill: level}
        }
    """
    if not resume_text:
        return {"skills": [], "categorized": {}, "total": 0,
                "category_distribution": {}, "proficiency_hints": {}}

    patterns = _build_patterns()
    text_lower = resume_text.lower()

    matched = []
    categorized = {}
    proficiency = {}

    for skill, info in patterns.items():
        if info["regex"].search(text_lower):
            if skill not in matched:
                matched.append(skill)
                cat_name = info["category"].replace("_", " ").title()
                if cat_name not in categorized:
                    categorized[cat_name] = []
                categorized[cat_name].append(skill)

                # Proficiency hint based on frequency
                count = len(info["regex"].findall(text_lower))
                if count >= 5:
                    proficiency[skill] = "Expert"
                elif count >= 3:
                    proficiency[skill] = "Advanced"
                elif count >= 2:
                    proficiency[skill] = "Intermediate"
                else:
                    proficiency[skill] = "Beginner"

    # Check synonyms/abbreviations
    for abbr, full_skill in _SYNONYM_MAP.items():
        # Space-separated phrases shouldn't be bounded strictly as words on both sides if they are multi-word, 
        # but for safety against partial matches, \b is still best.
        abbr_pattern = r"\b" + re.escape(abbr) + r"s?\b"
        if re.search(abbr_pattern, text_lower) and full_skill not in matched:
            for cat, skills in _SKILL_DATABASE.items():
                if full_skill in skills:
                    cat_name = cat.replace("_", " ").title()
                    matched.append(full_skill)
                    if cat_name not in categorized:
                        categorized[cat_name] = []
                    categorized[cat_name].append(full_skill)
                    proficiency[full_skill] = "Intermediate (Inferred)"
                    break

    # Category distribution
    cat_dist = {cat: len(skills) for cat, skills in categorized.items()}

    return {
        "skills": matched,
        "categorized": categorized,
        "total": len(matched),
        "category_distribution": cat_dist,
        "proficiency_hints": proficiency,
    }


def get_all_skills():
    """Return a flat sorted list of all skills in the database."""
    all_skills = []
    for skills in _SKILL_DATABASE.values():
        all_skills.extend(skills)
    return sorted(set(all_skills))


def get_skills_for_role(role_name):
    """
    Return skills commonly associated with a role name.
    Uses keyword matching against the database.
    """
    role_lower = role_name.lower()
    relevant = []

    # Role-specific skill mappings
    _ROLE_SKILL_MAP = {
        "information technology": ["Python", "Java", "SQL", "Linux", "AWS",
                                    "Docker", "Git", "REST API", "JavaScript", "Node.js"],
        "engineering": ["MATLAB", "AutoCAD", "Python", "C++", "CAD",
                        "Mechanical Engineering", "Circuit Design", "3D Modeling"],
        "hr": ["Recruitment", "Talent Acquisition", "Employee Relations",
                "HRIS", "Communication", "Leadership", "Onboarding"],
        "finance": ["Financial Analysis", "Excel", "SQL", "Python",
                     "Risk Management", "Accounting", "Forecasting"],
        "banking": ["Financial Analysis", "Risk Management", "SQL",
                     "CRM", "Customer Service", "Compliance", "Excel"],
        "accountant": ["Accounting", "Excel", "Tax", "Auditing",
                        "Financial Analysis", "SAP", "Budgeting"],
        "designer": ["Photoshop", "Illustrator", "Figma", "CSS",
                      "Adobe XD", "Sketch", "Canva", "HTML"],
        "digital media": ["Social Media Marketing", "SEO", "Content Marketing",
                           "Google Analytics", "Photoshop", "Video Editing"],
        "sales": ["Sales Strategy", "CRM", "Lead Generation",
                   "Negotiation", "Communication", "Customer Service"],
        "business development": ["Sales Strategy", "Market Research",
                                  "Negotiation", "CRM", "Strategic Planning"],
        "healthcare": ["Patient Care", "Clinical Research", "Public Health",
                        "Medical Records", "Healthcare Management"],
        "teacher": ["Teaching", "Curriculum Development", "Lesson Planning",
                     "Communication", "E-Learning", "Content Creation"],
        "consultant": ["Project Management", "Strategic Planning", "Communication",
                        "Analytical Thinking", "PowerPoint", "Excel"],
        "advocate": ["Legal Research", "Contract Law", "Corporate Law",
                      "Communication", "Writing", "Compliance"],
        "chef": ["Food Safety", "Nutrition", "Hospitality",
                  "Creativity", "Time Management", "Leadership"],
        "agriculture": ["Agriculture Technology", "Research", "Data Analysis",
                         "Python", "Excel", "Project Management"],
        "fitness": ["Nutrition", "Communication", "Customer Service",
                     "Leadership", "Time Management", "Mentoring"],
        "bpo": ["Customer Service", "Communication", "CRM",
                 "Excel", "Time Management", "Multitasking"],
        "apparel": ["Fashion Design", "Textile", "Photoshop",
                     "Illustrator", "Creativity", "Attention to Detail"],
        "construction": ["AutoCAD", "Project Management", "Civil Engineering",
                          "CAD", "Structural Analysis", "Budgeting"],
        "public relations": ["Public Relations", "Communication", "Writing",
                              "Social Media Marketing", "Content Creation"],
        "arts": ["Creativity", "Photoshop", "Illustrator", "Canva",
                  "Content Creation", "Communication", "Writing"],
        "aviation": ["Communication", "Leadership", "Decision Making",
                      "Time Management", "Attention to Detail"],
        "automobile": ["Mechanical Engineering", "AutoCAD", "CAD",
                        "3D Modeling", "Quality Assurance", "Six Sigma"],
    }

    return _ROLE_SKILL_MAP.get(role_lower, [])


def save_skill_db():
    """Save the skill database to JSON."""
    os.makedirs(os.path.dirname(_SKILL_DB_PATH), exist_ok=True)
    with open(_SKILL_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(_SKILL_DATABASE, f, indent=2, ensure_ascii=False)


# Save on module load
save_skill_db()
