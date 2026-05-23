import sys
import os
import pytest
import gc
import json

# Ensure backend is on the path so all modules import consistently
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app as flask_app
from extensions import db
from models.user import User
from models.resume import Resume
from models.recruiter_pipeline import RecruiterPipeline
from flask_jwt_extended import create_access_token

@pytest.fixture(autouse=True)
def force_gc():
    gc.collect()

@pytest.fixture
def test_client():
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["RATELIMIT_ENABLED"] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def setup_users(test_client):
    with flask_app.app_context():
        user_cred = User(name="Test User", email="user@test.com", role="user", job_domain="Engineering")
        user_cred.set_password("pass123")

        rec_cred = User(name="Recruiter", email="rec@test.com", role="recruiter", job_domain="Engineering")
        rec_cred.set_password("pass123")

        candidate = User(name="Candidate", email="cand@test.com", role="user", job_domain="Engineering")
        candidate.set_password("pass123")

        db.session.add_all([user_cred, rec_cred, candidate])
        db.session.commit()

        resume = Resume(
            user_id=candidate.id,
            filename="test.pdf",
            ats_score=85,
            domain="Engineering",
            parsed_data=json.dumps({"score": 85, "skills": ["Python", "Flask"]})
        )
        db.session.add(resume)
        db.session.commit()

        return {
            "user": {"id": user_cred.id, "email": user_cred.email},
            "recruiter": {"id": rec_cred.id, "email": rec_cred.email},
            "candidate": {"id": candidate.id, "email": candidate.email}
        }


def get_token(email, role):
    with flask_app.app_context():
        return create_access_token(identity=email, additional_claims={"role": role})


# ===== TEST 1: Recruiter can search anonymized candidates =====
def test_recruiter_search(test_client, setup_users):
    token = get_token(setup_users["recruiter"]["email"], "recruiter")
    response = test_client.get(
        "/recruiter/api/search?domain=Engineering&min_score=80",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["candidates"]) == 1

    cand = data["candidates"][0]
    assert cand["candidate_id"] == setup_users["candidate"]["id"]
    assert cand["ats_score"] == 85
    # Verify no PII is returned
    assert "name" not in cand
    assert "email" not in cand
    assert "phone" not in cand


# ===== TEST 2: User-role cannot access recruiter endpoints -> 403 =====
def test_user_cannot_access_recruiter(test_client, setup_users):
    token = get_token(setup_users["user"]["email"], "user")
    response = test_client.get(
        "/recruiter/api/search",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


# ===== TEST 3: Shortlist candidate -> pipeline insertion =====
def test_shortlist_adds_to_pipeline(test_client, setup_users):
    token = get_token(setup_users["recruiter"]["email"], "recruiter")
    headers = {"Authorization": f"Bearer {token}"}
    cid = setup_users["candidate"]["id"]

    response = test_client.post(f"/recruiter/api/pipeline/shortlist/{cid}", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # Verify the pipeline record
    response = test_client.get("/recruiter/api/pipeline", headers=headers)
    data = response.get_json()
    assert data["success"] is True
    assert len(data["pipeline"]["Sourced"]) == 1
    assert data["pipeline"]["Sourced"][0]["candidate_id"] == cid


# ===== TEST 4: Pipeline stage update =====
def test_pipeline_stage_update(test_client, setup_users):
    token = get_token(setup_users["recruiter"]["email"], "recruiter")
    headers = {"Authorization": f"Bearer {token}"}
    cid = setup_users["candidate"]["id"]

    # First shortlist
    test_client.post(f"/recruiter/api/pipeline/shortlist/{cid}", headers=headers)

    # Now move to Reviewed
    response = test_client.put(
        f"/recruiter/api/pipeline/{cid}/stage",
        json={"stage": "Reviewed"},
        headers=headers,
        content_type='application/json'
    )
    assert response.status_code == 200

    # Confirm movement
    response = test_client.get("/recruiter/api/pipeline", headers=headers)
    data = response.get_json()
    assert len(data["pipeline"]["Sourced"]) == 0
    assert len(data["pipeline"]["Reviewed"]) == 1
