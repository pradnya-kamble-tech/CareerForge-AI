import os
import re
import time
import json
import threading
from datetime import datetime, timedelta
from uuid import uuid4
import logging
from io import BytesIO
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   send_file, session, redirect, url_for, flash)
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from resume_parser import extract_text_from_pdf
from analyzer import (extract_skills, calculate_score, score_resume, detect_weaknesses,
                      risk_analysis, career_prediction, skill_gap_analysis,
                      simulate_evolution, get_all_skills,
                      parse_resume_structured, sanitize_resume_text)
from report_generator import generate_report
from extensions import db, migrate, jwt, limiter
from models.user import User
from models.resume import Resume
from models.recruiter_pipeline import RecruiterPipeline
from routes.auth import auth_bp
from routes.recruiter import recruiter_bp
from agents.agent_manager import run_full_analysis
from agents.cover_letter_agent import generate_cover_letter

app = Flask(__name__, 
            template_folder="../frontend/templates", 
            static_folder="../frontend/static")
app.secret_key = os.environ.get("SECRET_KEY", "careerforge-dev-secret-key-2026")

# ---------- Logging Configuration ----------
LOG_FILE = os.path.join(os.path.dirname(__file__), "system.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("CareerForge")
logger.info("CareerForge AI server starting up...")

# ---------- Database Configuration ----------
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///careerforge.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-super-secret-key-2026')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_TOKEN_LOCATION'] = ['headers']

db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    enabled=os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
)
limiter.init_app(app)

# Apply rate limit to login specifically will be done in auth.py
# by importing limiter or passing it.
# To avoid circular imports, we can use the extension directly from the blueprint or app.

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(recruiter_bp, url_prefix='/recruiter')

logger.info("SQLAlchemy, Migrate, JWT and Limiter initialised.")

# Global jobs store for async analysis
ANALYSIS_JOBS = {}

# ---------- Configuration ----------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB Limit
# Data is now in ../data relative to backend/app.py
ANALYSES_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "analyses.json"))

# Create uploads/ folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Validation Config ----------
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
RESUME_KEYWORDS = re.compile(
    r"\b(education|experience|skills|summary|objective|projects|certifications|achievements|work\s*history)\b",
    re.IGNORECASE,
)

def validate_resume_content(text):
    """Return True if extracted text looks like a resume (>= 2 keyword matches)."""
    matches = set(RESUME_KEYWORDS.findall(text.lower()))
    return len(matches) >= 2


# ---------- JSON Helpers (kept for analyses only) ----------

def _load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_analyses():
    return _load_json(ANALYSES_FILE)


def save_analyses(data):
    _save_json(ANALYSES_FILE, data)


from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt

def login_required(f):
    """Decorator to protect routes that require authentication (Session or JWT)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Check Session
        if "user" in session:
            return f(*args, **kwargs)
        
        # 2. Check JWT
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity:
                return f(*args, **kwargs)
        except Exception:
            pass
            
        flash("Please login to access this page.", "error")
        return redirect(url_for("login"))
    return decorated


def role_required(*allowed_roles):
    """Decorator to restrict access to specific roles (Session or JWT)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_role = None
            
            # 1. Check Session
            if "user" in session:
                user_role = session.get("role", "")
            
            # 2. Check JWT
            if not user_role:
                try:
                    verify_jwt_in_request(optional=True)
                    claims = get_jwt()
                    if claims:
                        user_role = claims.get("role", "")
                except Exception:
                    pass

            if not user_role:
                flash("Please login to access this page.", "error")
                return redirect(url_for("login"))
                
            if user_role.lower() not in [r.lower() for r in allowed_roles] and user_role.lower() != 'admin':
                return redirect(url_for("access_denied"))
                
            return f(*args, **kwargs)
        return decorated
    return decorator


def allowed_file(filename):
    """Return True if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Auth Routes ----------

# Legacy Auth Routes removed in favor of JWT API


# ---------- Main Routes ----------

@app.route("/")
def landing():
    """Render the landing page."""
    return render_template("landing.html")


@app.route("/login")
def login():
    """Render the login page."""
    return render_template("login.html")


@app.route("/register")
def register():
    """Render the registration page."""
    return render_template("register.html")


@app.route("/access-denied")
def access_denied():
    """Render the access denied page."""
    return render_template("error.html", 
                           error_code=403, 
                           error_msg="Access Denied")


@app.route("/logout")
def logout():
    """Clear session and redirect to landing."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))


# ---------- Dashboard Routes ----------

@app.route("/dashboard")
@login_required
def dashboard_overview():
    """Render the main dashboard overview."""
    user_email = session.get("user")
    if not user_email:
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
        except Exception:
            pass
    user = User.query.filter_by(email=user_email).first() if user_email else None
    return render_template("dashboard/overview.html",
                           active_page="overview",
                           user=user.name if user else (user_email or "Demo User"),
                           domain=user.job_domain if user else "Engineering",
                           role=user.role if user else "Student")

@app.route("/dashboard/resume")
@login_required
def dashboard_resume():
    """Render the resume analysis details page."""
    user_email = session.get("user")
    if not user_email:
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
        except Exception:
            pass
    user = User.query.filter_by(email=user_email).first() if user_email else None
    return render_template("dashboard/resume.html",
                           active_page="resume",
                           user=user.name if user else (user_email or "Demo User"),
                           domain=user.job_domain if user else "Engineering",
                           role=user.role if user else "Student")

@app.route("/dashboard/jobs")
@login_required
def dashboard_jobs():
    """Render the job matcher page."""
    user_email = session.get("user")
    if not user_email:
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
        except Exception:
            pass
    user = User.query.filter_by(email=user_email).first() if user_email else None
    return render_template("dashboard/job_matcher.html",
                           active_page="jobs",
                           user=user.name if user else (user_email or "Demo User"),
                           domain=user.job_domain if user else "Engineering",
                           role=user.role if user else "Student")

@app.route("/api/dashboard/stats")
@login_required
def dashboard_stats():
    """JSON endpoint for dashboard stats (stub)."""
    return jsonify({"success": True})


@app.route("/student")
def student_dashboard():
    """Render the student dashboard (role-guarded, demo bypass)."""
    demo_mode = request.args.get("demo") == "1"
    if not demo_mode:
        user_email = session.get("user")
        user_role = session.get("role")
        
        if not user_email:
            try:
                verify_jwt_in_request(optional=True)
                user_email = get_jwt_identity()
                user_role = get_jwt().get("role")
            except Exception:
                pass
                
        if not user_email:
            flash("Please login to access this page.", "error")
            return redirect(url_for("login"))
            
        if user_role not in ("Student", "Admin", "user"):
            return redirect(url_for("access_denied"))
            
    return render_template("index.html",
                           user=user_email or "demo@careerforge.com",
                           role=user_role or "Student",
                           demo_mode=demo_mode)


@app.route("/api/analyze", methods=["POST"])
@app.route("/upload", methods=["POST"])
@login_required
def upload_resume():
    """Handle PDF resume upload and initiate AI analysis."""
    if "resume" not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Only PDF files are allowed."}), 400

    # Save file
    raw_name = secure_filename(file.filename)
    filename = f"{uuid4().hex[:8]}_{raw_name}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)
    
    try:
        extracted_text = extract_text_from_pdf(save_path)
        if not validate_resume_content(extracted_text):
            os.remove(save_path)
            return jsonify({"success": False, "message": "Invalid resume content."}), 400

        user_email = session.get("user") or get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()
        domain = user.job_domain if user and user.job_domain else "Engineering"
        user_id = user.id if user else None

        # Start Async AI Analysis
        job_id = str(uuid4())
        ANALYSIS_JOBS[job_id] = {"status": "processing", "start_time": time.time()}

        def background_analysis(app_context, text, dom, uid, fname, jid):
            with app_context:
                try:
                    result = run_full_analysis(text, dom, uid, fname)
                    if result.get("success"):
                        ANALYSIS_JOBS[jid]["status"] = "completed"
                        ANALYSIS_JOBS[jid]["result"] = result
                    else:
                        ANALYSIS_JOBS[jid]["status"] = "failed"
                        ANALYSIS_JOBS[jid]["result"] = {
                            "success": False,
                            "message": result.get("message") or result.get("error") or "AI Pipeline failed."
                        }
                except Exception as ex:
                    logger.error(f"Background analysis error: {str(ex)}")
                    ANALYSIS_JOBS[jid]["status"] = "failed"
                    ANALYSIS_JOBS[jid]["result"] = {"success": False, "message": str(ex)}
                
                ANALYSIS_JOBS[jid]["end_time"] = time.time()

        thread = threading.Thread(
            target=background_analysis,
            args=(app.app_context(), extracted_text, domain, user_id, filename, job_id)
        )
        thread.start()

        return jsonify({
            "success": True, 
            "message": "Analysis started.",
            "job_id": job_id
        }), 202

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during upload."}), 500


@app.route("/api/status")
def status():
    """Simple API endpoint to verify the server is running."""
    return jsonify({"status": "ok", "project": "CareerForge AI"})


@app.route("/api/demo-data")
def demo_data():
    """Return pre-analysed sample resume data for demo mode."""
    sample_text = """
    PRIYA SHARMA
    Full Stack Developer | Mumbai, India
    Email: priya.sharma@email.com | LinkedIn: linkedin.com/in/priyasharma

    SUMMARY
    Passionate computer science graduate with hands-on experience in web development
    and data analysis. Seeking a challenging role to leverage my skills in Python,
    machine learning, and cloud computing.

    EDUCATION
    B.E. Computer Science, University of Mumbai (2022-2026) – CGPA: 8.5/10

    SKILLS
    Python, Java, JavaScript, HTML, CSS, SQL, React, Node.js, Flask, Git,
    Machine Learning, Data Analysis, REST API, MongoDB, Docker, AWS, Linux

    EXPERIENCE
    Software Development Intern – TechSolutions Pvt. Ltd. (June 2025 - Dec 2025)
    - Developed RESTful APIs using Flask and Node.js
    - Built responsive frontends with React and JavaScript
    - Implemented CI/CD pipelines using Docker and AWS

    PROJECTS
    1. AI Resume Analyzer – Python, Flask, NLP
    2. E-Commerce Dashboard – React, Node.js, MongoDB
    3. Weather Prediction System – Python, Machine Learning, Data Analysis

    CERTIFICATIONS
    - AWS Cloud Practitioner
    - Google Data Analytics Certificate
    """

    try:
        # For demo data, use user's domain if logged in (session or optional JWT)
        user_email = session.get("user")
        if not user_email:
            try:
                verify_jwt_in_request(optional=True)
                user_email = get_jwt_identity()
            except Exception:
                user_email = None
        user = User.query.filter_by(email=user_email).first() if user_email else None
        domain = user.job_domain if user and user.job_domain else "Engineering"

        skill_results = extract_skills(sample_text, domain=domain)
        score_results = score_resume(sample_text, domain=domain)
        risk_results = risk_analysis(score_results["score"], skill_results["skills"])
        career_results = career_prediction(skill_results["skills"], domain=domain)
        gap_results = skill_gap_analysis(skill_results["skills"], domain=domain, text=sample_text)

        analysis_id = uuid4().hex

        explainability = {
            "score_reason": score_results["reason"],
            "risk_reason": risk_results["reason"],
            "risk_suggestions": risk_results["suggestions"],
            "career_reasons": [
                {"role": p["role"], "match": p["match_percentage"], "reason": p["reason"]}
                for p in career_results[:5]
            ],
            "skill_gap_reason": gap_results.get("summary", ""),
        }

        result = {
            "success": True,
            "analysis_id": analysis_id,
            "message": "Demo resume analysed successfully!",
            "filename": "demo_resume_priya_sharma.pdf",
            "size_kb": 142.5,
            "extracted_text": sample_text.strip(),
            "skills": skill_results["skills"],
            "skills_categorized": skill_results["categorized"],
            "skills_total": skill_results["total"],
            "score": score_results["score"],
            "score_level": score_results["level"],
            "score_reason": score_results["reason"],
            "score_breakdown": score_results["breakdown"],
            "risk_level": risk_results["risk_level"],
            "risk_icon": risk_results["risk_icon"],
            "risk_reason": risk_results["reason"],
            "risk_suggestions": risk_results["suggestions"],
            "career_predictions": career_results,
            "role": career_results[0]["role"] if career_results else "Student",
            "skill_gap": gap_results,
            "explainability": explainability,
        }

        # Persist for safe PDF download in demo mode
        analyses = load_analyses()
        analyses.append({"id": analysis_id, **result})
        if len(analyses) > 200:
            analyses = analyses[-200:]
        save_analyses(analyses)
        session['last_analysis_id'] = analysis_id

        logger.info("Demo mode analysis served (id=%s)", analysis_id)
        return jsonify(result)

    except Exception as e:
        logger.error("Demo data generation failed: %s", str(e))
        return jsonify({"success": False, "message": "Demo data unavailable."}), 500


@app.route("/api/all-skills")
@login_required
def all_skills():
    """Return every skill in the database for the simulator dropdown."""
    return jsonify({"skills": get_all_skills()})


@app.route("/simulate", methods=["POST"])
@login_required
def simulate():
    """Simulate adding a new skill and return before/after comparison."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request."}), 400

    current_skills = data.get("current_skills", [])
    added_skill = data.get("added_skill", "")

    if not added_skill:
        return jsonify({"success": False, "message": "No skill selected."}), 400

    result = simulate_evolution(current_skills, added_skill)
    return jsonify({"success": True, **result})


@app.route("/api/parse-resume", methods=["POST"])
def api_parse_resume():
    """Extract structured JSON from resume text using AI agent."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Request body must be JSON."}), 400

    resume_text = data.get("resume_text", "").strip()
    domain = data.get("domain", "Engineering")
    if not resume_text:
        return jsonify({"success": False, "message": "'resume_text' field is required."}), 400

    try:
        from agents.resume_parser_agent import parse_resume_with_ai
        parsed = parse_resume_with_ai(resume_text, domain)
        return jsonify({"success": True, **parsed})
    except Exception as e:
        logger.error(f"API Parse error: {str(e)}")
        return jsonify({"success": False, "message": "Parsing failed."}), 500


@app.route("/api/analysis/<job_id>/status")
@login_required
def get_analysis_status(job_id):
    """Poll for analysis job status."""
    job = ANALYSIS_JOBS.get(job_id)
    if not job:
        return jsonify({"success": False, "message": "Job not found."}), 404
        
    return jsonify({
        "success": True,
        "status": job["status"],
        "result": job.get("result")
    })


@app.route("/download-report")
@app.route("/download-report/<analysis_id>")
def download_report(analysis_id=None):
    """Generate and download a PDF report."""
    if not analysis_id:
        analysis_id = session.get('last_analysis_id')
    if not analysis_id:
        return jsonify({"success": False, "message": "No analysis ID available."}), 400

    analyses = load_analyses()
    analysis = next((a for a in analyses if a.get("id") == analysis_id), None)
    if not analysis:
        # Fallback: check if it's a resume ID from DB
        from models.resume import Resume
        resume = Resume.query.get(analysis_id)
        if resume:
            analysis = json.loads(resume.parsed_data)
        else:
            return jsonify({"success": False, "message": "Analysis not found."}), 404

    pdf_bytes = generate_report(analysis)
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="CareerForge_Report.pdf"
    )




@app.route("/recruiter")
@role_required("Recruiter", "Admin")
def recruiter_page():
    """Render the recruiter dashboard."""
    return render_template("recruiter.html",
                           user=session.get("user") or get_jwt_identity(),
                           role=session.get("role") or "Recruiter")


@app.route("/recruiter-upload", methods=["POST"])
@role_required("Recruiter", "Admin")
def recruiter_upload():
    """Handle multiple PDF resume uploads with validation."""
    files = request.files.getlist("resumes")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"success": False, "message": "No files selected."}), 400

    saved_paths = []
    skipped = 0

    for file in files:
        if file.filename == "" or not allowed_file(file.filename):
            skipped += 1
            continue

        raw_name = secure_filename(file.filename)
        filename = f"{uuid4().hex[:8]}_{raw_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        saved_paths.append((filename, save_path))

    candidates = []
    for filename, path in saved_paths:
        try:
            text = extract_text_from_pdf(path)
            if not validate_resume_content(text):
                os.remove(path)
                skipped += 1
                continue

            # Recruiter upload is synchronous for now as it's batch, but we could make it async too.
            # For simplicity, we'll keep it as is but use the AI parser if possible.
            from agents.resume_parser_agent import parse_resume_with_ai
            parsed = parse_resume_with_ai(text, "Engineering") # Default to engineering for recruiter batch
            
            candidates.append({
                "filename": filename,
                "parsed_data": parsed,
                "score": 75, # Placeholder for recruiter batch view
                "insight": "AI Parsed"
            })
        except Exception as e:
            logger.error(f"Recruiter process error: {str(e)}")
            skipped += 1

    return jsonify({
        "success": True,
        "candidates": candidates,
        "skipped": skipped
    })


@app.route("/recruiter-decision", methods=["POST"])
@role_required("Recruiter", "Admin")
def recruiter_decision():
    """Track shortlist/reject decisions — persisted to SQLite."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False}), 400

    owner = session.get("user", "unknown")
    decision = data.get("decision", "")
    record = {
        "filename": data.get("filename", "unknown"),
        "score": data.get("score", 0),
        "risk_level": data.get("risk_level", "unknown"),
        "insight": data.get("insight", ""),
        "owner": owner,
        "decision": decision,
    }
    # db_add_decision(record) - Stuffed for now
    logger.info("Recruiter decision: %s (user=%s)", decision, owner)
    return jsonify({"success": True, "decision": decision})


@app.route("/recruiter-results")
@role_required("Recruiter", "Admin")
def recruiter_results():
    """Show shortlisted and rejected candidates — filtered by owner."""
    owner = session.get("user", "unknown")
    shortlisted = [] # db_get_decisions(owner, "shortlisted") - Stuffed
    rejected = [] # db_get_decisions(owner, "rejected") - Stuffed
    return render_template("recruiter_results.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           shortlisted=shortlisted,
                           rejected=rejected)


# ---------- Admin Routes ----------

@app.route("/admin")
@role_required("Admin")
def admin_page():
    """Render the admin dashboard with system-wide statistics from SQLite."""
    total_resumes = Resume.query.count()
    return render_template("admin.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           total=total_resumes,
                           avg_score=0,
                           highest_score=0,
                           lowest_score=0,
                           unique_skills=0,
                           top_skills=[],
                           risk_dist={"Low": 0, "Medium": 0, "High": 0},
                           score_dist={"0-39": 0, "40-69": 0, "70-100": 0},
                           total_users=User.query.count(),
                           total_logs=0,
                           trend_labels=[],
                           trend_data=[],
                           all_users=User.query.all(),
                           db_logs=[])

# ---------- Logs Route (Admin only) ----------

@app.route("/admin/logs")
@role_required("Admin")
def view_logs():
    """Show the last 50 log entries."""
    lines = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
    return render_template("logs.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           log_lines=lines)


# ---------- Global Error Handlers ----------

# ---------- Database Helpers for Tests/Admin ----------

def init_db():
    """Initialize the database (create tables)."""
    with app.app_context():
        db.create_all()
    logger.info("Database tables created.")

def db_add_user(email, password, role="Student", name=None, domain="Engineering"):
    """Add a user to the database manually (for testing/setup)."""
    with app.app_context():
        if User.query.filter_by(email=email).first():
            return False
        user = User(
            email=email,
            name=name or email.split("@")[0],
            role=role,
            job_domain=domain
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return True

def db_user_exists(email):
    """Check if a user exists in the database."""
    with app.app_context():
        return User.query.filter_by(email=email).first() is not None


@app.errorhandler(404)
def page_not_found(e):
    logger.warning("404 Not Found: %s", request.path)
    return render_template("error.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           error_code=404,
                           error_msg="Page Not Found"), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error("500 Internal Server Error: %s", str(e))
    return render_template("error.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           error_code=500,
                           error_msg="Internal Server Error"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        logger.info("Database tables verified/created.")
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
