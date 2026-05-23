# report_generator.py — Generate a professional PDF report of the resume analysis

from fpdf import FPDF
from datetime import datetime


def _sanitize(text):
    """Replace Unicode characters unsupported by Helvetica with ASCII equivalents."""
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "\u2014": "-",   # em-dash
        "\u2013": "-",   # en-dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2022": "-",   # bullet
        "\u2026": "...", # ellipsis
        "\u00b7": "-",   # middle dot
        "\u2192": "->",  # right arrow
        "\u2190": "<-",  # left arrow
        "\u2713": "[x]", # checkmark
        "\u2717": "[ ]", # cross
        "\u00a0": " ",   # non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Strip any remaining non-latin1 chars
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ResumeReport(FPDF):
    """Custom PDF class with header/footer for CareerForge reports."""

    def header(self):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(63, 81, 181)
        self.cell(0, 12, "CareerForge AI", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, "AI-Powered Resume Intelligence Report", align="C",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        ts = datetime.now().strftime("%d %b %Y, %I:%M %p")
        self.cell(0, 10, f"Generated on {ts}  |  Page {self.page_no()}", align="C")


def _heading(pdf, text):
    """Render a section heading."""
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(63, 81, 181)
    pdf.cell(0, 10, _sanitize(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _label(pdf, text):
    """Render a single line of text."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, _sanitize(text), new_x="LMARGIN", new_y="NEXT")


def _para(pdf, text):
    """Render a paragraph that may wrap."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, _sanitize(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _bold(pdf, text):
    """Render bold text."""
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 7, _sanitize(text), new_x="LMARGIN", new_y="NEXT")


def generate_report(data):
    """Build and return a PDF report (as bytes) from the analysis data dict."""
    pdf = ResumeReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ---- 1. Overview ----
    _heading(pdf, "1. Resume Overview")
    _label(pdf, f"File Analysed:  {data.get('filename', 'N/A')}")
    _label(pdf, f"Skills Detected:  {data.get('skills_total', 0)}")
    _label(pdf, f"Resume Score:  {data.get('score', 0)} / 100  ({data.get('score_level', '-')})")
    _label(pdf, f"Risk Level:  {data.get('risk_level', '-')}")
    pdf.ln(4)

    # ---- 2. Detected Skills ----
    _heading(pdf, "2. Detected Skills")
    categorized = data.get("skills_categorized", {})
    if categorized:
        for category, skills in categorized.items():
            _bold(pdf, category)
            _label(pdf, "    " + ", ".join(skills))
            pdf.ln(1)
    else:
        _label(pdf, "No skills detected.")
    pdf.ln(2)

    # ---- 3. Resume Score ----
    _heading(pdf, "3. Resume Score Analysis")
    _label(pdf, f"Score:  {data.get('score', 0)} / 100")
    _label(pdf, f"Level:  {data.get('score_level', '-')}")
    bd = data.get("score_breakdown", {})
    if bd:
        _label(pdf, f"Skill Score:  {bd.get('skill_score', 0)}")
        _label(pdf, f"Diversity Bonus:  +{bd.get('diversity_bonus', 0)}")
        _label(pdf, f"Categories Covered:  {bd.get('categories_covered', 0)}")
    reason = data.get("score_reason", "")
    if reason:
        pdf.ln(2)
        _para(pdf, f"Explanation: {reason}")
    pdf.ln(2)

    # ---- 4. Risk Analysis ----
    _heading(pdf, "4. Risk Analysis")
    _label(pdf, f"Risk Level:  {data.get('risk_level', '-')}")
    risk_reason = data.get("risk_reason", "")
    if risk_reason:
        pdf.ln(2)
        _para(pdf, risk_reason)
    suggestions = data.get("risk_suggestions", [])
    if suggestions:
        _bold(pdf, "Suggestions:")
        for s in suggestions:
            _label(pdf, f"  ->  {s}")
    pdf.ln(4)

    # ---- 5. Career Predictions ----
    _heading(pdf, "5. Career Predictions")
    predictions = data.get("career_predictions", [])
    if predictions:
        for p in predictions[:5]:
            _bold(pdf, f"{p.get('role', '')}  -  {p.get('match_percentage', 0)}% match")
            matched = p.get("matched_skills", [])
            if matched:
                _label(pdf, f"    Matched: {', '.join(matched)}")
            pdf.ln(1)
    else:
        _label(pdf, "No career matches found.")
    pdf.ln(2)

    # ---- 6. Skill Gap Analysis ----
    gap = data.get("skill_gap", {})
    if gap:
        _heading(pdf, "6. Skill Gap Analysis")
        _label(pdf, f"Target Role:  {gap.get('target_role', '-')}")
        _label(pdf, f"Gap:  {gap.get('gap_percentage', 0)}%  ({gap.get('matched_count', 0)}/{gap.get('total_role_skills', 0)} matched)")
        summary = gap.get("summary", "").replace("**", "")
        if summary:
            pdf.ln(2)
            _para(pdf, summary)

        missing = gap.get("missing_skills", [])
        if missing:
            _bold(pdf, "Missing Skills:")
            for item in missing:
                _label(pdf, f"  [{item.get('priority', '')}]  {item['skill']}  -  {item.get('reason', '')}")

        recommended = gap.get("recommended_skills", [])
        if recommended:
            pdf.ln(2)
            _bold(pdf, "Recommended Skills:")
            for item in recommended:
                _label(pdf, f"  {item['skill']}  -  {item.get('reason', '')}")

    return pdf.output()
