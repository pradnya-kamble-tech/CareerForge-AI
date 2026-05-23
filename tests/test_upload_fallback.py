import requests
import json
import os
import time

url = 'http://127.0.0.1:5000'
session = requests.Session()

print("--- TESTING STUDENT UPLOAD & DB FALLBACK ---")
# 1. Register & Login test user
email = f'test_{int(time.time())}@example.com'
session.post(f"{url}/register", data={'email':email, 'password':'pass', 'role':'Student'})
login_res = session.post(f"{url}/login", data={'email':email, 'password':'pass'})
if email not in login_res.text and 'Welcome back' not in login_res.text:
    print("Login might have failed, proceeding anyway...")

# 2. Create dummy PDF (with some text to pass validate_resume_content)
pdf_path = 'dummy_test.pdf'
with open(pdf_path, 'wb') as f:
    f.write(b'%PDF-1.4\n% dummy content with Education Skills Experience\n')

# 3. Upload PDF
files = {'resume': open(pdf_path, 'rb')}
upload_res = session.post(f"{url}/upload", files=files)
print(f"Upload Route Status: {upload_res.status_code}")
if upload_res.status_code == 200:
    try:
        print("Upload Result JSON Success:", upload_res.json().get("success"))
    except Exception as e:
        print("Upload result was not JSON. Text:", upload_res.text[:500])
else:
    print("Upload Error Payload:", upload_res.text[:500])

# 4. Test Student Dashboard (DB Fallback Simulation)
# It pulls from db_get_resumes. We just test if it returns 200 OK.
dash = session.get(f"{url}/student")
print(f"Dashboard Route Status: {dash.status_code}")
if dash.status_code == 200 and '<html' in dash.text.lower():
    print("Dashboard Fallback verification PASSED. Returned 200 HTML.")
else:
    print("Dashboard crashed!")
