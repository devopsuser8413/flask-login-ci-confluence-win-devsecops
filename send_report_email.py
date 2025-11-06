import os
import smtplib
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

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
CONFLUENCE_USER  = os.getenv("CONFLUENCE_USER")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")

REPORT_DIR = Path("report")

AUTH = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)

# ============================================================
# 🧩 Helper Functions
# ============================================================
def get_report_files():
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
        files.extend(REPORT_DIR.glob(pattern))
    return [f for f in files if f.is_file()]


def detect_version():
    vf = REPORT_DIR / "version.txt"
    return vf.read_text().strip() if vf.exists() else "N/A"


def detect_status():
    po = REPORT_DIR / "pytest_output.txt"
    if po.exists():
        content = po.read_text(encoding="utf-8", errors="ignore").lower()
        if "failed" in content:
            return "FAIL"
        return "PASS"
    return "UNKNOWN"


def get_latest_confluence_page_link(version, status):
    """Get the latest created Confluence child page URL for this version"""
    try:
        search_url = f"{CONFLUENCE_BASE}/rest/api/content/search"
        query = f'title ~ "Test Result Report v{version} ({status})" and space="{CONFLUENCE_SPACE}"'
        params = {"cql": query, "expand": "version"}
        r = requests.get(search_url, params=params, auth=AUTH)
        if r.status_code == 200 and r.json().get("results"):
            page_id = r.json()["results"][0]["id"]
            title = r.json()["results"][0]["title"]
            link = f"{CONFLUENCE_BASE}/pages/{page_id}/{title.replace(' ', '+')}"
            print(f"🔗 Found Confluence page link: {link}")
            return link
        else:
            print(f"⚠️ No matching Confluence page found for version v{version}")
    except Exception as e:
        print(f"⚠️ Confluence link fetch failed: {e}")

    # Fallback: space homepage link
    return f"{CONFLUENCE_BASE}/wiki/spaces/{CONFLUENCE_SPACE}/pages"


def build_email_body(version, status, report_links, confluence_link):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
      <h2>📊 DevSecOps Test & Security Report v{version} ({status})</h2>
      <p><b>Generated:</b> {timestamp}</p>
      <p>The latest reports from Jenkins are attached below.</p>
      <h3>📎 Attached Files</h3>
      <ul>
        {''.join(f'<li>{Path(f).name}</li>' for f in report_links)}
      </ul>
      <h3>🔗 View in Confluence</h3>
      <p><a href="{confluence_link}" target="_blank">Open Test Result Report v{version} in Confluence</a></p>
      <p><i>This email was generated automatically by Jenkins DevSecOps Pipeline.</i></p>
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
    confluence_link = get_latest_confluence_page_link(version, status)

    if not files_to_attach:
        print("❌ No report files found to attach. Check the 'report' directory.")
        exit(1)

    msg = EmailMessage()
    msg["From"] = REPORT_FROM
    msg["To"] = REPORT_TO
    msg["Subject"] = f"📊 DevSecOps Test & Security Report v{version} ({status})"

    html_body = build_email_body(version, status, files_to_attach, confluence_link)
    msg.add_alternative(html_body, subtype="html")

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

    print(f"📤 Sending report email for v{version} ({status}) to {REPORT_TO} ...")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("✅ Email sent successfully with all report attachments.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
