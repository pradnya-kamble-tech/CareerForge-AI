import sys
import os
import json
import unittest
from unittest.mock import patch

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app import app
from extensions import db
from models.user import User
from models.resume import Resume

class SystemHealthCheck(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'health-check-secret'
        app.config['RATELIMIT_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('app.extract_text_from_pdf')
    def test_full_lifecycle_healthcare(self, mock_extract):
        mock_extract.return_value = "Professional Summary: Experienced Nurse. Skills: Patient Care, HIPAA Compliance. Experience: 10 years at General Hospital."
        
        # 1. Register as Healthcare professional
        reg_payload = {
            'name': 'Nurse Joy',
            'email': 'joy@example.com',
            'password': 'Password123',
            'role': 'user',
            'job_domain': 'Healthcare'
        }
        resp = self.client.post('/api/auth/register', 
                                data=json.dumps(reg_payload),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        
        # Logged in automatically or use session for the /upload legacy route?
        # app.py /upload uses @login_required which checks session['user']
        # Let's simulate session login too for the legacy routes.
        with self.client.session_transaction() as sess:
            sess['user'] = 'joy@example.com'
            sess['role'] = 'user'

        # 2. Upload (mocked PDF extraction)
        from io import BytesIO
        token = json.loads(resp.data)['access_token']
        data = {
            'resume': (BytesIO(b"dummy pdf content"), 'test.pdf')
        }
        # Use JWT in Header
        resp = self.client.post('/upload', 
                                data=data, 
                                content_type='multipart/form-data',
                                headers={'Authorization': f'Bearer {token}'})
        if resp.status_code != 200:
            print(f"DEBUG: Status={resp.status_code}, Location={resp.headers.get('Location')}")
            print(f"DEBUG: Body={resp.data.decode('utf-8', 'ignore')[:200]}")
        self.assertEqual(resp.status_code, 200)
        
        result = json.loads(resp.data)
        self.assertTrue(result['success'])
        # Healthcare domain keywords should be matched
        # 'Patient Care' and 'HIPAA' are critical for healthcare.
        self.assertIn('Patient Care', result['skills'])
        self.assertIn('HIPAA', result['skills'])
        
        # 3. Check DB Persistence
        with app.app_context():
            user = User.query.filter_by(email='joy@example.com').first()
            resume = Resume.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(resume)
            self.assertEqual(resume.domain, 'Healthcare Professional') # From analyzer prediction
            parsed_data = json.loads(resume.parsed_data)
            self.assertEqual(parsed_data['score'], result['score'])

    def test_unauthorized_access(self):
        # Test that recruiter route is protected
        resp = self.client.get('/recruiter')
        self.assertEqual(resp.status_code, 302) # Redirect to login

if __name__ == '__main__':
    unittest.main()
