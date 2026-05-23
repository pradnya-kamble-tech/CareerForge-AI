import os
import sys
import json
import unittest
from io import BytesIO

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import app, init_db, db_add_user, db_user_exists
from extensions import db

TEST_EMAIL = "testQA@careerforge.com"
TEST_PASS = "Password123"
TEST_RECRUITER_EMAIL = "recruiterQA@careerforge.com"


class TestCareerForgeAI_QA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["JWT_SECRET_KEY"] = "qa-test-secret"
        app.config["RATELIMIT_ENABLED"] = False
        app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "test_uploads")
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        # Create all tables in memory DB
        with app.app_context():
            db.create_all()

        # Register test users via the API
        client = app.test_client()
        client.post('/api/auth/register', data=json.dumps({
            'name': 'QA User', 'email': TEST_EMAIL,
            'password': TEST_PASS, 'role': 'user', 'job_domain': 'Engineering'
        }), content_type='application/json')
        client.post('/api/auth/register', data=json.dumps({
            'name': 'QA Recruiter', 'email': TEST_RECRUITER_EMAIL,
            'password': TEST_PASS, 'role': 'recruiter', 'job_domain': 'Engineering'
        }), content_type='application/json')

    def setUp(self):
        self.client = app.test_client()
        # Get JWT token for standard user
        resp = self.client.post('/api/auth/login', data=json.dumps({
            'email': TEST_EMAIL, 'password': TEST_PASS
        }), content_type='application/json')
        data = resp.get_json() or {}
        self.token = data.get('access_token', '')
        self.auth_headers = {'Authorization': f'Bearer {self.token}'}

    # ─────────────────────────────────────────────
    # UPLOAD EDGE CASE TESTS
    # ─────────────────────────────────────────────

    def test_01_empty_pdf(self):
        """Edge Case 1: Empty PDF should be caught by content validator."""
        data = {"resume": (BytesIO(b"%PDF-1.4\n%EOF"), "empty.pdf")}
        response = self.client.post(
            "/upload", data=data, content_type="multipart/form-data",
            headers=self.auth_headers
        )
        json_resp = response.get_json()
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {json_resp}")
        self.assertIn("message", json_resp)

    def test_02_non_pdf_file(self):
        """Edge Case 2: Extension validation."""
        data = {"resume": (BytesIO(b"Hello World"), "text.txt")}
        response = self.client.post(
            "/upload", data=data, content_type="multipart/form-data",
            headers=self.auth_headers
        )
        json_resp = response.get_json()
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {json_resp}")

    def test_03_no_file(self):
        """Edge Case 3: No file part."""
        response = self.client.post(
            "/upload", data={}, content_type="multipart/form-data",
            headers=self.auth_headers
        )
        json_resp = response.get_json()
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {json_resp}")
        self.assertIn("No file", json_resp.get("message", ""))

    def test_04_ai_demo_flow(self):
        """Validate AI logic end-to-end using the demo-data endpoint (simulates perfect resume)."""
        response = self.client.get("/api/demo-data", headers=self.auth_headers)
        json_resp = response.get_json()
        self.assertEqual(response.status_code, 200, f"Got {response.status_code}: {json_resp}")
        self.assertTrue(json_resp.get("success"), f"success=False: {json_resp}")
        self.assertIn("score", json_resp)
        self.assertIn("skills_categorized", json_resp)
        self.assertIn("career_predictions", json_resp)
        # Verify Risk vs Score correlation
        score = json_resp["score"]
        risk_level = json_resp["risk_level"]
        if score > 80:
            self.assertIn(risk_level, ["Low", "Very Low"])

    def test_05_digital_twin(self):
        """Digital Twin edge case simulation — Format B."""
        current_skills = ["Python", "Machine Learning"]
        added_skill = "Docker"
        response = self.client.post(
            "/simulate",
            json={"current_skills": current_skills, "added_skill": added_skill},
            content_type="application/json",
            headers=self.auth_headers
        )
        rj = response.get_json()
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {rj}")
        self.assertTrue(rj.get("success"), f"Success was False: {rj}")

    # ─────────────────────────────────────────────
    # ROLE INTELLIGENCE UNIT TESTS
    # ─────────────────────────────────────────────

    def test_06_role_knowledge_teacher(self):
        """TASK 7 – Teacher: role knowledge returns relevant skills, gap is non-empty."""
        from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap

        kb = get_role_knowledge("Teacher")
        top_skills = kb.get("top_skills", [])

        self.assertGreater(len(top_skills), 0, "No top_skills for Teacher.")
        self.assertGreater(kb.get("resume_count", 0), 0, "resume_count is 0 for Teacher.")

        skill_names_lower = [s.lower() for s in top_skills]
        teacher_specific = {"teaching", "lesson planning", "curriculum development", "e-learning", "training"}
        found = teacher_specific & set(skill_names_lower)
        self.assertGreater(len(found), 0, f"Teacher top_skills don't contain teaching-specific skills. Got: {top_skills}")

        gap = get_skill_gap([], "Teacher")
        self.assertGreater(len(gap["missing"]), 0, "Skill gap missing list is empty for Teacher with no skills.")
        self.assertEqual(gap["match_percentage"], 0.0)
        print(f"\n[Teacher] top_skills: {top_skills[:5]}")

    def test_07_role_knowledge_hr(self):
        """TASK 7 – HR: role knowledge returns relevant skills, gap is role-specific."""
        from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap

        kb = get_role_knowledge("Hr")
        top_skills = kb.get("top_skills", [])

        self.assertGreater(len(top_skills), 0, "No top_skills for HR.")
        self.assertGreater(kb.get("resume_count", 0), 0, "resume_count is 0 for HR.")

        skill_names_lower = [s.lower() for s in top_skills]
        hr_specific = {"recruitment", "employee relations", "hris", "onboarding",
                       "talent acquisition", "performance management", "compensation"}
        found = hr_specific & set(skill_names_lower)
        self.assertGreater(len(found), 0, f"HR top_skills don't include HR-specific skills. Got: {top_skills}")

        partial_skills = ["Communication", "Excel"]
        gap = get_skill_gap(partial_skills, "Hr")
        self.assertGreater(len(gap["missing"]), 0, "Skill gap missing list is empty for HR with minimal skills.")
        self.assertLess(gap["match_percentage"], 100.0)
        print(f"\n[HR] top_skills: {top_skills[:5]}")

    def test_08_role_knowledge_engineering(self):
        """TASK 7 – Engineering: role knowledge returns relevant skills, score is non-zero."""
        from ai_engine.role_knowledge import get_role_knowledge, get_skill_gap
        from analyzer import analyze_resume_ai

        kb = get_role_knowledge("Engineering")
        top_skills = kb.get("top_skills", [])

        self.assertGreater(len(top_skills), 0, "No top_skills for Engineering.")
        self.assertGreater(kb.get("resume_count", 0), 0, "resume_count is 0 for Engineering.")

        skill_names_lower = [s.lower() for s in top_skills]
        eng_specific = {"autocad", "mechanical engineering", "cad", "lean manufacturing",
                        "matlab", "automation", "quality assurance"}
        found = eng_specific & set(skill_names_lower)
        self.assertGreater(len(found), 0, f"Engineering top_skills don't include engineering-specific skills. Got: {top_skills}")

        # End-to-end: run a short engineering resume through the full AI pipeline
        eng_resume = (
            "MECHANICAL ENGINEER\n"
            "SKILLS: AutoCAD, SolidWorks, CAD, MATLAB, Mechanical Engineering, "
            "Project Management, Quality Assurance, Lean Manufacturing\n"
            "EXPERIENCE: 3 years as a Mechanical Design Engineer at ABC Corp.\n"
            "EDUCATION: B.E. Mechanical Engineering, XYZ University."
        )
        result = analyze_resume_ai(eng_resume)
        self.assertNotIn("error", result, f"AI pipeline error: {result.get('error')}")
        self.assertGreater(result.get("score", 0), 0, "Score is 0 for Engineering resume.")
        print(f"\n[Engineering] score: {result.get('score')}")

    def test_09_simulator_format_a(self):
        """Simulator Format A: extracted_text + added_skill (frontend format)."""
        resume_text = (
            "Python Developer with experience in Django, Flask, REST API, Git, Linux. "
            "3 years experience. B.E. Computer Science."
        )
        response = self.client.post(
            "/simulate",
            json={"extracted_text": resume_text, "added_skill": "Docker"},
            content_type="application/json",
            headers=self.auth_headers
        )
        rj = response.get_json()
        self.assertEqual(response.status_code, 200, f"Simulate Format A failed: {rj}")
        self.assertTrue(rj.get("success"))
        print(f"\n[Simulator Format A] result: {rj}")

    def test_10_skill_gap_never_empty(self):
        """Skill gap should NEVER be empty, even for unknown roles."""
        from ai_engine.role_knowledge import get_skill_gap
        gap = get_skill_gap([], "UnknownRole_XYZ")
        self.assertGreater(len(gap["missing"]), 0, "Skill gap returned empty for unknown role — fallback broken.")
        self.assertEqual(gap["match_percentage"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
