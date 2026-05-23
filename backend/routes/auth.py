import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, jwt_required, get_jwt
)
from functools import wraps
from models.user import User
from extensions import db, limiter
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

JOB_DOMAINS = [
    'Engineering', 'Healthcare', 'Finance', 'Marketing', 
    'Design', 'Legal', 'HR', 'Operations', 
    'Education', 'Sales', 'Hospitality', 'Construction'
]

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def role_required(role):
    """Decorator to restrict access to specific roles via JWT claims."""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != role and claims.get('role') != 'admin':
                return jsonify({"msg": "Forbidden: Requires {} role".format(role)}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    name = data.get('name')
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    role = data.get('role', 'user').lower()
    job_domain = data.get('job_domain')

    # Validations
    if not all([name, email, password, job_domain]):
        return jsonify({"msg": "Missing required fields"}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({"msg": "Invalid email format"}), 400

    if len(password) < 8 or not any(char.isdigit() for char in password):
        return jsonify({"msg": "Password must be at least 8 characters and contains a number"}), 400

    if job_domain not in JOB_DOMAINS:
        return jsonify({"msg": "Invalid job domain"}), 400

    if role not in ['user', 'recruiter']:
        return jsonify({"msg": "Invalid role"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exists"}), 400

    # Create User
    new_user = User()
    new_user.name = name
    new_user.email = email
    new_user.role = role
    new_user.job_domain = job_domain
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    from flask import session
    session['user'] = email
    session['role'] = role

    # Create Token
    access_token = create_access_token(
        identity=email,
        additional_claims={"role": role},
        expires_delta=timedelta(minutes=15)
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "job_domain": new_user.job_domain
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "Bad email or password"}), 401

    from flask import session
    session['user'] = email
    session['role'] = user.role

    access_token = create_access_token(
        identity=email,
        additional_claims={"role": user.role},
        expires_delta=timedelta(minutes=15)
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "job_domain": user.job_domain
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "job_domain": user.job_domain
        }
    }), 200
