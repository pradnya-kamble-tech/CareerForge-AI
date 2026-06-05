⚡ CareerForge AI — AI-Powered Resume Intelligence System

An intelligent resume analysis platform that parses PDF resumes, extracts skills, scores them, predicts career paths, identifies skill gaps, and generates downloadable PDF reports.

🚀 Features

- **PDF Resume Parsing** — Upload a PDF and extract text automatically
- **Skill Mining** — Keyword-based skill detection across 8+ categories
- **Resume Scoring** — 0-100 scoring with explainable breakdown
- **Risk Analysis** — Resume risk assessment with actionable suggestions
- **Career Prediction** — Role matching with percentage-based predictions
- **Skill Gap Analysis** — Identify missing skills for your target role
- **Resume Evolution Simulator** — Digital twin to simulate skill additions
- **PDF Report Download** — Generate professional analysis reports
- **Authentication** — Login/Register with Student, Recruiter, Admin roles

---

📁 Project Structure

```
careerforge/
├── app.py                 # Flask application (routes, auth, API)
├── resume_parser.py       # PDF text extraction (pdfplumber)
├── analyzer.py            # Skill extraction, scoring, risk, career prediction
├── report_generator.py    # PDF report generation (fpdf2)
├── requirements.txt       # Python dependencies
├── Procfile               # Production server command (gunicorn)
├── templates/
│   ├── index.html         # Main dashboard
│   ├── login.html         # Login page
│   └── register.html      # Registration page
├── static/
│   ├── style.css          # Styling
│   └── script.js          # Frontend logic
└── data/
    ├── skills.json        # Skills database
    └── users.json         # Registered users (file-based storage)
```

---


## 🛠️ Setup in 3 Quick Steps

Follow these steps to get the platform running with real AI analysis:

1. **Configure Environment**: Copy `.env.example` to a new file named `.env`.
   ```bash
   cp .env.example .env
   ```
2. **Add API Key**: Open `.env` and add your free **Anthropic API Key** (get it at [console.anthropic.com](https://console.anthropic.com/)).
3. **Run App**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   python backend/app.py
   ```

---

## 🛠️ Full Local Development Setup

```bash
# 1. Clone / navigate to the project
cd careerforge
...
```

### Test with Production Settings (locally)

```bash
# Windows PowerShell
$env:FLASK_ENV="production"; $env:PORT="8000"; python app.py

# macOS / Linux
FLASK_ENV=production PORT=8000 python app.py
```

---

## ☁️ Deploy on Render (Free Tier)

### Step-by-step:

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "CareerForge AI - ready for deployment"
   git remote add origin https://github.com/YOUR_USERNAME/careerforge.git
   git push -u origin main
   ```

2. **Go to [render.com](https://render.com)** and sign in with GitHub

3. **Create a New Web Service**
   - Click **"New +"** → **"Web Service"**
   - Connect your **careerforge** repository

4. **Configure the service**

   | Setting | Value |
   |---------|-------|
   | **Name** | `careerforge-ai` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |
   | **Plan** | `Free` |

5. **Add Environment Variable**
   - Key: `FLASK_ENV` → Value: `production`

6. **Click "Create Web Service"** — Render will build and deploy automatically

7. **Your app is live** at `https://careerforge-ai.onrender.com` 🎉

---

## ☁️ Deploy on Railway (Alternative)

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
2. Select the `careerforge` repository
3. Railway auto-detects `Procfile` and `requirements.txt`
4. Add environment variable: `FLASK_ENV=production`
5. Click **Deploy** — your app is live!

---

## 📋 Key Files Explained

| File | Purpose |
|------|---------|
| `requirements.txt` | Lists all pip packages needed |
| `Procfile` | Tells the cloud platform how to start the app |
| `app.py` | Reads `PORT` from environment so cloud platforms can assign a port |
| `data/users.json` | File-based user storage (no database needed) |

---

## ⚠️ Notes

- **gunicorn** is Linux-only. On Windows, local dev uses `python app.py` (Flask dev server). Gunicorn runs on Render/Railway (Linux).
- User data is stored in `data/users.json`. On free-tier platforms, this resets on redeploy (file system is ephemeral).
- For persistent storage, consider upgrading to a database in a future step.

---

Built with ❤️ as a Final Year Project — **CareerForge AI**
