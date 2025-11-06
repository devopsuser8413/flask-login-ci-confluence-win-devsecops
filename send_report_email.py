import os
import smtplib
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime

# ============================================================
# ⚙️ Configuration (auto-read from Jenkins environment)
# ============================================================
SMTP_HOST  = os.getenv("SMTP_HOST")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER")
SMTP_PASS  = os.getenv("SMTP_PASS")
REPORT_FROM = os.getenv("REPORT_FROM")
REPORT_TO   = os.getenv("REPORT_TO")

CONFLUENCE_BASE  = os.getenv("CONFLUENCE_BASE")
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE", "DEMO")
CONFLUENCE_TITLE = os.getenv("CONFLUENCE_TITLE", "DevSecOps Test Result Report")

REPORT_DIR = Path("report")

# ============================================================
# 🧩 Helper Functions
# ============================================================
def get_report_files():
    """Return list of report files to attach in email."""
    patterns = [
        "bandit_report.html",
        "dependency_vuln.txt",
        "report.html",
        "test_result_report_v*.html",
        "test_result_report_v*.pdf",
        "trivy_report.txt",
        "version.txt",
        "zap_dast_report.html",
    ]
    files = []
    for pattern in patterns:
        for f in REPORT_DIR.glob(pattern):
            if f.is_file():
                files.append(f)
    return files


def detect_version():
    vf = REPORT_DIR / "version.txt"
    return vf.read_text().strip() if vf.exists() else "N/A"


def detect_status():
    """Infer PASS/FAIL status from pytest output."""
    po = REPORT_DIR / "pytest_output.txt"
    if po.exists():
        content = po.read_text(encoding="utf-8", errors="ignore").lower()
        if "failed" in content:
            return "FAIL"
        return "PASS"
    return "UNKNOWN"


# ============================================================
# ✉️ Email Message Builder
# ============================================================
def build_email_body(version, status, report_links):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conf_page_url = f"{CONFLUENCE_BASE}/wiki/spaces/{CONFLUENCE_SPACE}/pages"
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
      <h2>DevSecOps Test & Security Report v{version} ({status})</h2>
      <p><b>Generated:</b> {timestamp}</p>
      <p>The latest test and security reports from Jenkins are attached.</p>
      <p>📎 <b>Attached files:</b></p>
      <ul>
        {''.join(f'<li>{Path(f).name}</li>' for f in report_links)}
      </ul>
      <p>🔗 <b>Confluence Page:</b> 
        <a href="{conf_page_url}" target="_blank">{CONFLUENCE_TITLE}</a>
      </p>
      <p><i>This email was sent automatically by Jenkins DevSecOps Pipeline.</i></p>
    </body>
    </html>
    """


# ============================================================
# 🚀 Main Logic
# ============================================================
if __name__ == "__main__":
    version = detect_version()
    status = detect_status()
    files_to_attach = get_report_files()

    if not files_to_attach:
        print("❌ No report files found to attach. Check the 'report' directory.")
        exit(1)

    msg = EmailMessage()
    msg["From"] = REPORT_FROM
    msg["To"] = REPORT_TO
    msg["Subject"] = f"📊 DevSecOps Test & Security Report v{version} ({status})"

    html_body = build_email_body(version, status, files_to_attach)
    msg.add_alternative(html_body, subtype="html")

    # Attach each file
    for file_path in files_to_attach:
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        main_type, sub_type = mime_type.split("/", 1)
        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=main_type,
                subtype=sub_type,
                filename=Path(file_path).name
            )
        print(f"📎 Attached: {Path(file_path).name}")

    print(f"📤 Sending report email to: {REPORT_TO} via {SMTP_HOST}:{SMTP_PORT}")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("✅ Email sent successfully with all report attachments.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
