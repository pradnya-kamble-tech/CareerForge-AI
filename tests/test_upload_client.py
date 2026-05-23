from app import app, db_get_resumes
import io
from unittest.mock import patch

print("--- TESTING UPLOAD PERSISTENCE ---")
app.config['TESTING'] = True
client = app.test_client()

with client.session_transaction() as sess:
    sess['user'] = 'demo_student'
    sess['role'] = 'Student'

dummy_pdf = io.BytesIO(b'%PDF-1.4\n% Test\n')
dummy_pdf.name = "test_resume.pdf"

data = {
    'resume': (dummy_pdf, 'test_resume.pdf')
}

with patch('app.extract_text_from_pdf', return_value="Senior Software Engineer skilled in Python, Kubernetes, AWS, and Agile."):
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    
print("Status Code:", response.status_code)

if response.status_code == 200:
    res_data = response.get_json()
    print("Success:", res_data.get("success"))
    print("Analysis ID created.")
    
    db_resumes = db_get_resumes('demo_student')
    found = any(r['filename'].endswith('test_resume.pdf') for r in db_resumes)
    print("Persisted to DB:", found)
else:
    print("Upload Failed:", response.data[:500])
