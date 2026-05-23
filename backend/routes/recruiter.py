import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from extensions import db
from models.user import User
from models.resume import Resume
from models.recruiter_pipeline import RecruiterPipeline

logger = logging.getLogger("CareerForge")

recruiter_bp = Blueprint('recruiter', __name__)


def recruiter_required(f):
    """Decorator to require recruiter role."""
    import functools
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user_email = session.get("user")
        user_role = session.get("role")

        if not user_email:
            try:
                verify_jwt_in_request()
                user_email = get_jwt_identity()
                user_role = get_jwt().get("role")
            except Exception:
                return jsonify({"error": "Unauthorized"}), 401

        if user_role != "recruiter":
            if 'text/html' in request.accept_mimetypes:
                flash("Access Denied: Recruiter portal only.", "error")
                return redirect(url_for('landing'))
            return jsonify({"error": "Forbidden: Recruiter access required."}), 403

        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# TEMPLATE ROUTES  (under /recruiter/...)
# ==========================================

@recruiter_bp.route("/")
@recruiter_bp.route("/dashboard")
@recruiter_required
def dashboard():
    """Render the recruiter dashboard base (defaults to search)."""
    return render_template("recruiter/search.html", active_page="search", role="recruiter")


@recruiter_bp.route("/pipeline-view")
@recruiter_required
def pipeline_view():
    """Render the Kanban pipeline view."""
    return render_template("recruiter/pipeline.html", active_page="pipeline", role="recruiter")


# ==========================================
# API ROUTES  (mounted at /recruiter/api/...)
# ==========================================

@recruiter_bp.route("/api/search", methods=["GET"])
@recruiter_required
def search_candidates():
    """Returns anonymized candidate list based on filters."""
    domain_filter = request.args.get("domain")
    min_score = request.args.get("min_score", type=int, default=0)
    max_score = request.args.get("max_score", type=int, default=100)

    query = db.session.query(User, Resume).join(Resume, User.id == Resume.user_id)

    if domain_filter:
        query = query.filter(User.job_domain == domain_filter)

    results = query.all()

    candidates = []
    for user, resume in results:
        score = resume.ats_score or 0
        skills = []
        if resume.parsed_data:
            try:
                data = json.loads(resume.parsed_data)
                skills = data.get("skills", [])
            except Exception:
                pass

        if min_score <= score <= max_score:
            candidates.append({
                "candidate_id": user.id,
                "domain": user.job_domain,
                "ats_score": score,
                "top_skills": skills[:5],
                "experience_years": "N/A"
            })

    return jsonify({"success": True, "candidates": candidates})


@recruiter_bp.route("/api/rank", methods=["POST"])
@recruiter_required
def rank_candidates():
    """Ranks candidates based on provided JD (stub)."""
    content = request.json or {}
    jd = content.get("job_description")
    candidate_ids = content.get("candidate_ids", [])

    if not jd or not candidate_ids:
        return jsonify({"error": "Missing JD or candidates"}), 400

    return jsonify({"success": True, "message": "Ranked successfully (mock)"})


@recruiter_bp.route("/api/pipeline/shortlist/<int:candidate_id>", methods=["POST"])
@recruiter_required
def shortlist_candidate(candidate_id):
    """Adds a candidate to the recruiter's pipeline at stage 'Sourced'."""
    user_email = session.get("user")
    if not user_email:
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
        except Exception:
            pass

    recruiter = User.query.filter_by(email=user_email).first()
    if not recruiter:
        return jsonify({"error": "Recruiter not found"}), 404

    candidate = User.query.get(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    existing = RecruiterPipeline.query.filter_by(
        recruiter_id=recruiter.id, candidate_id=candidate.id
    ).first()
    if existing:
        return jsonify({"error": "Candidate already in pipeline"}), 400

    new_entry = RecruiterPipeline(
        recruiter_id=recruiter.id,
        candidate_id=candidate.id,
        stage="Sourced"
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"success": True, "message": "Candidate added to pipeline."})


@recruiter_bp.route("/api/pipeline", methods=["GET"])
@recruiter_required
def get_pipeline():
    """Returns pipeline candidates grouped by kanban stage."""
    user_email = session.get("user")
    if not user_email:
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
        except Exception:
            pass

    recruiter = User.query.filter_by(email=user_email).first()
    pipeline_entries = RecruiterPipeline.query.filter_by(recruiter_id=recruiter.id).all()

    stages = {
        "Sourced": [],
        "Reviewed": [],
        "Shortlisted": [],
        "Interviewed": [],
        "Hired/Rejected": []
    }

    for entry in pipeline_entries:
        candidate = User.query.get(entry.candidate_id)
        if not candidate:
            continue

        resume = Resume.query.filter_by(user_id=candidate.id).order_by(Resume.uploaded_at.desc()).first()
        score = 0
        skills = []
        if resume:
            score = resume.ats_score or 0
            if resume.parsed_data:
                try:
                    data = json.loads(resume.parsed_data)
                    skills = data.get("skills", [])
                except Exception:
                    pass

        stage_name = entry.stage if entry.stage in stages else "Sourced"
        days = (datetime.utcnow() - entry.updated_at).days if entry.updated_at else 0

        stages[stage_name].append({
            "candidate_id": candidate.id,
            "pipeline_id": entry.id,
            "domain": candidate.job_domain,
            "ats_score": score,
            "top_skills": skills[:5],
            "days_in_stage": days
        })

    return jsonify({"success": True, "pipeline": stages})


@recruiter_bp.route("/api/pipeline/<int:candidate_id>/stage", methods=["PUT"])
@recruiter_required
def update_stage(candidate_id):
    """Moves candidate to a new kanban stage."""
    user_email = session.get("user")
    if not user_email:
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
        except Exception:
            pass

    recruiter = User.query.filter_by(email=user_email).first()
    content = request.json or {}
    new_stage = content.get("stage")

    if not new_stage:
        return jsonify({"error": "Stage required"}), 400

    entry = RecruiterPipeline.query.filter_by(
        recruiter_id=recruiter.id, candidate_id=candidate_id
    ).first()
    if not entry:
        return jsonify({"error": "Candidate not in pipeline"}), 404

    entry.stage = new_stage
    db.session.commit()

    return jsonify({"success": True, "message": "Stage updated."})
