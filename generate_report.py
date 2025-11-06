import os
import re
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from fpdf import FPDF
from fpdf.html import HTMLMixin


# ============================================================
# 📦 Configuration
# ============================================================
REPORT_DIR = Path("report")
REPORT_DIR.mkdir(exist_ok=True)
VERSION_FILE = REPORT_DIR / "version.txt"
BASE_NAME = "test_result_report"


# ============================================================
# 🧩 Helper Functions
# ============================================================
def read_version():
    """Read or initialize version counter"""
    if VERSION_FILE.exists():
        with open(VERSION_FILE) as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 1
    return 1


def increment_version():
    """Increment and persist report version"""
    version = read_version() + 1
    with open(VERSION_FILE, "w") as f:
        f.write(str(version))
    return version


def safe_read(file_path):
    """Read file safely with UTF-8 fallback"""
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def extract_summary():
    """Extract summary information from reports"""
    summary = {}

    pytest_log = safe_read(REPORT_DIR / "pytest_output.txt")
    if pytest_log:
        passed = re.findall(r"(\d+)\s+passed", pytest_log)
        failed = re.findall(r"(\d+)\s+failed", pytest_log)
        errors = re.findall(r"(\d+)\s+errors?", pytest_log)
        skipped = re.findall(r"(\d+)\s+skipped", pytest_log)
        summary["passed"] = int(passed[0]) if passed else 0
        summary["failed"] = int(failed[0]) if failed else 0
        summary["errors"] = int(errors[0]) if errors else 0
        summary["skipped"] = int(skipped[0]) if skipped else 0
        total = sum(summary.values())
        rate = (summary["passed"] / total * 100) if total else 0
        summary["rate"] = round(rate, 1)
    else:
        summary.update({"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "rate": 0})

    # Security reports
    summary["bandit_findings"] = len(re.findall(r"<tr class=\"issue\">", safe_read(REPORT_DIR / "bandit_report.html")))
    summary["dep_vuln"] = len(re.findall(r"\|", safe_read(REPORT_DIR / "dependency_vuln.txt")))
    summary["trivy_high"] = len(re.findall(r"High", safe_read(REPORT_DIR / "trivy_report.txt")))
    summary["zap_high"] = len(re.findall(r"High", safe_read(REPORT_DIR / "zap_dast_report.html")))

    return summary


# ============================================================
# 🧠 HTML Report Generator
# ============================================================
def generate_html(summary, version):
    """Generate HTML summary report"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "PASS" if summary["failed"] == 0 and summary["errors"] == 0 else "FAIL"
    emoji = "✅" if status == "PASS" else "❌"

    sec_html = f"""
    <div style="background-color:#eef7ff; border:1px solid #007bff; padding:15px; margin:15px 0;">
      <h2>🔐 DevSecOps Security Summary</h2>
      <ul>
        <li><b>SAST (Bandit):</b> {summary["bandit_findings"]} findings</li>
        <li><b>Dependency Vulnerabilities:</b> {summary["dep_vuln"]} issues</li>
        <li><b>Container Scan (Trivy):</b> {summary["trivy_high"]} High vulnerabilities</li>
        <li><b>DAST (OWASP ZAP):</b> {summary["zap_high"]} High alerts</li>
      </ul>
    </div>
    """

    html = f"""
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Automated Test & Security Report v{version}</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #007bff; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
      </style>
    </head>
    <body>
      <h1>🧪 Test & Security Report v{version}</h1>
      <p><b>Date:</b> {now}</p>
      <div class="summary">
        <h2>Test Summary</h2>
        <ul>
          <li>Passed: {summary["passed"]}</li>
          <li>Failed: {summary["failed"]}</li>
          <li>Errors: {summary["errors"]}</li>
          <li>Skipped: {summary["skipped"]}</li>
          <li>Pass Rate: {summary["rate"]}%</li>
          <li>Status: <b class="{status.lower()}">{emoji} {status}</b></li>
        </ul>
      </div>
      {sec_html}
      <p><i>Generated automatically by Jenkins DevSecOps Pipeline</i></p>
    </body>
    </html>
    """

    html_file = REPORT_DIR / f"{BASE_NAME}_v{version}.html"
    html_file.write_text(html, encoding="utf-8")
    return html_file


# ============================================================
# 🧾 PDF Report Generator (HTML Rendering - Unicode Safe)
# ============================================================
class PDF(FPDF, HTMLMixin):
    pass


def html_to_pdf(html_file, version):
    """Convert HTML report to PDF using full HTML rendering (fpdf2 HTMLMixin)"""
    pdf = PDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf")
    pdf.set_font("DejaVu", "", 12)

    html_content = html_file.read_text(encoding="utf-8")
    pdf.write_html(html_content)

    pdf_file = REPORT_DIR / f"{BASE_NAME}_v{version}.pdf"
    pdf.output(str(pdf_file))
    return pdf_file

# ============================================================
# 🚀 Main
# ============================================================
if __name__ == "__main__":
    version = increment_version()
    summary = extract_summary()
    html_file = generate_html(summary, version)
    pdf_file = html_to_pdf(html_file, version)

    print(f"✅ HTML Report generated: {html_file}")
    print(f"✅ PDF Report generated: {pdf_file}")
    print(f"🆙 Version updated: {version}")
