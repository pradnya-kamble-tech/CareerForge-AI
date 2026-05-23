"""
CareerForge AI - Automated UI Testing (Playwright)
Run this script to automatically open a browser and test the application visually.
Ideal for Viva demonstrations!

Requirements:
pip install pytest playwright pytest-playwright
playwright install chromium
"""

import os
import uuid
import time
from playwright.sync_api import sync_playwright

def create_valid_dummy_pdf():
    # A perfectly valid RAW PDF structure without external libraries!
    pdf_content = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 81 >>
stream
BT
/F1 12 Tf
100 700 Td
(Python, Machine Learning, Data Science, Flask, React, SQL, HTML, CSS) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000213 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
343
%%EOF
'''
    with open("dummy_resume.pdf", "wb") as f:
        f.write(pdf_content)

def run_automated_test():
    with sync_playwright() as p:
        # Launch browser in non-headless mode (visible to you)
        # slow_mo=500 creates a 0.5 sec delay between actions so the examiner can see what's happening
        print("🚀 Starting Automated Browser Test...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        # 1. Open App
        print("🌐 Opening CareerForge AI...")
        page.goto("http://127.0.0.1:5000/")
        assert "CareerForge" in page.title()
        
        # 2. Register a temporary test user
        test_email = f"test_{uuid.uuid4().hex[:6]}@demo.com"
        print(f"👤 Registering new test user: {test_email}")
        page.goto("http://127.0.0.1:5000/register")
        page.fill("input[name='email']", test_email)
        page.fill("input[name='password']", "viva2026")
        page.select_option("select[name='role']", "Student")
        page.click("button[type='submit']")
        
        # 3. Login Flow
        print("🔑 Logging into the dashboard...")
        page.fill("input[name='email']", test_email)
        page.fill("input[name='password']", "viva2026")
        page.click("button[type='submit']")
        
        # 4. Automate File Upload
        print("📄 Generating test PDF & Uploading Resume...")
        create_valid_dummy_pdf()
        
        # We are now on the student portal /student page
        page.wait_for_selector("input#resume")
        page.set_input_files("input#resume", "dummy_resume.pdf")
        
        # Click the "Analyze Resume" button (which has class .upload-btn)
        page.click("button.upload-btn")
        
        print("⏳ Waiting for AI Analysis to complete... (This might take a moment)")
        
        # 5. Dashboard Verification
        print("📊 Verifying Student Dashboard Results...")
        page.wait_for_selector(".overview-grid", timeout=15000) # Wait up to 15 seconds for analysis
        
        # Check if ATS Score card appears
        assert "ATS Compatibility" in page.content(), "ATS Compatibility score was not found!"
        
        print("✅ ALL TESTS & UPLOADS PASSED SUCCESSFULLY!")
        
        # Clean up the dummy file
        if os.path.exists("dummy_resume.pdf"):
            os.remove("dummy_resume.pdf")
        
        # Pause for 5 seconds at the end so you can see the final state
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    run_automated_test()
