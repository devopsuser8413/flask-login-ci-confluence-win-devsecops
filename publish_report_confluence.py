import os
import sys
import time
import datetime
import smtplib
import json
import requests
from email.message import EmailMessage
from requests.auth import HTTPBasicAuth

# ============================================================
# 🔧 Environment Configuration
# ============================================================
CONFLUENCE_BASE  = os.getenv("CONFLUENCE_BASE")
CONFLUENCE_USER  = os.getenv("CONFLUENCE_USER")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE")
CONFLUENCE_TITLE = os.getenv("CONFLUENCE_TITLE", "Test Result Report")

SMTP_HOST  = os.getenv("SMTP_HOST")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER")
SMTP_PASS  = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("REPORT_FROM")
EMAIL_TO   = os.getenv("REPORT_TO")

REPORT_DIR   = "report"
VERSION_FILE = os.path.join(REPORT_DIR, "version.txt")
BASE_NAME    = "test_result_report"

auth    = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)
headers = {"Content-Type": "application/json", "X-Atlassian-Token": "no-check"}


# ============================================================
# 🧩 Helper Functions
# ============================================================
def read_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            return int(f.read().strip())
    return 1


def safe_read(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def extract_test_summary():
    """Extract test summary from pytest_output.txt"""
    import re
    text = safe_read(os.path.join(REPORT_DIR, "pytest_output.txt"))
    passed = failed = errors = skipped = 0
    if m := re.search(r"(\d+)\s+passed", text, re.I): passed = int(m.group(1))
    if m := re.search(r"(\d+)\s+failed", text, re.I): failed = int(m.group(1))
    if m := re.search(r"(\d+)\s+errors?", text, re.I): errors = int(m.group(1))
    if m := re.search(r"(\d+)\s+skipped", text, re.I): skipped = int(m.group(1))
    total = passed + failed + errors + skipped
    rate = (passed / total * 100) if total else 0
    status = "PASS" if failed == 0 and errors == 0 else "FAIL"
    emoji = "✅" if status == "PASS" else "❌"
    return f"{emoji} {passed} passed, {failed} failed, {errors} errors, {skipped} skipped (Pass Rate: {rate:.1f}%)", status


def extract_security_summary():
    """Read findings from Bandit, Safety, Trivy, and ZAP reports"""
    import re
    summary = {}
    bandit_html = safe_read(os.path.join(REPORT_DIR, "bandit_report.html"))
    safety_txt  = safe_read(os.path.join(REPORT_DIR, "dependency_vuln.txt"))
    trivy_html  = safe_read(os.path.join(REPORT_DIR, "trivy_report.html"))
    zap_html    = safe_read(os.path.join(REPORT_DIR, "zap_dast_report.html"))

    summary["SAST_Bandit"] = len(re.findall(r"<tr class=\"issue\">", bandit_html)) if bandit_html else "N/A"
    summary["Dependency_Safety"] = len(re.findall(r"\|", safety_txt)) if safety_txt else "N/A"

    if trivy_html:
        critical = len(re.findall(r"Critical", trivy_html, re.I))
        high = len(re.findall(r"High", trivy_html, re.I))
        summary["Container_Trivy"] = f"{critical} Critical / {high} High"
    else:
        summary["Container_Trivy"] = "N/A"

    if zap_html:
        high = len(re.findall(r"High", zap_html))
        medium = len(re.findall(r"Medium", zap_html))
        summary["DAST_ZAP"] = f"{high} High / {medium} Medium"
    else:
        summary["DAST_ZAP"] = "N/A"

    # Compute Risk Badge
    total_high = 0
    for key, value in summary.items():
        if isinstance(value, str) and "High" in value:
            try:
                total_high += int(re.findall(r"(\d+)", value.split("High")[0])[0])
            except Exception:
                pass
    if total_high == 0:
        summary["Risk_Level"] = "🟢 Low"
    elif total_high < 5:
        summary["Risk_Level"] = "🟠 Medium"
    else:
        summary["Risk_Level"] = "🔴 High"

    return summary


def create_confluence_page(title, html_body):
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE},
        "body": {"storage": {"value": html_body, "representation": "storage"}},
    }
    res = requests.post(url, headers=headers, json=payload, auth=auth)
    res.raise_for_status()
    data = res.json()
    return data["id"]


def upload_attachment(page_id, file_path):
    """Upload report attachments to Confluence"""
    file_name = os.path.basename(file_path)
    mime_type = "application/pdf" if file_name.endswith(".pdf") else "text/html"
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment"
    files = {"file": (file_name, open(file_path, "rb"), mime_type)}
    res = requests.post(url, headers={"X-Atlassian-Token": "no-check"}, files=files, auth=auth)
    if res.status_code not in [200, 204]:
        print(f"⚠️ Failed to upload {file_name}: {res.status_code} - {res.text}")
    else:
        print(f"📎 Uploaded: {file_name}")


def update_confluence_page(page_id, new_html):
    """Update an existing Confluence page with new HTML"""
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/"
    get_res = requests.get(url, auth=auth)
    get_res.raise_for_status()
    page_data = get_res.json()
    current_version = page_data["version"]["number"]

    payload = {
        "id": page_id,
        "type": "page",
        "title": CONFLUENCE_TITLE,
        "space": {"key": CONFLUENCE_SPACE},
        "version": {"number": current_version + 1},
        "body": {"storage": {"value": new_html, "representation": "storage"}},
    }

    res = requests.put(url, headers=headers, json=payload, auth=auth)
    res.raise_for_status()
    print(f"✅ Updated Confluence page (v{current_version + 1})")


# ============================================================
# 🚀 Main Logic
# ============================================================
if __name__ == "__main__":
    version = read_version()
    test_summary, test_status = extract_test_summary()
    security_summary = extract_security_summary()

    # Generate combined HTML report body
    html_body = f"""
    <h1>🧪 Automated Test & Security Report v{version}</h1>
    <p><b>Date:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p><b>Test Summary:</b> {test_summary}</p>
    <p><b>Risk Level:</b> {security_summary['Risk_Level']}</p>
    <hr/>
    <h2>🔍 Detailed Findings</h2>
    <ul>
        <li><b>SAST (Bandit):</b> {security_summary['SAST_Bandit']} findings</li>
        <li><b>Dependency Scan (Safety):</b> {security_summary['Dependency_Safety']} findings</li>
        <li><b>Container Scan (Trivy):</b> {security_summary['Container_Trivy']}</li>
        <li><b>DAST (OWASP ZAP):</b> {security_summary['DAST_ZAP']}</li>
    </ul>
    <hr/>
    <p>Generated automatically by Jenkins DevSecOps Pipeline.</p>
    """

    # Create or update Confluence page
    try:
        page_id = create_confluence_page(f"{CONFLUENCE_TITLE} v{version}", html_body)
        print(f"📝 Created new Confluence page: {page_id}")
    except requests.exceptions.HTTPError as e:
        # If page already exists, find it and update
        print("ℹ️ Page may already exist, attempting update...")
        search_url = f"{CONFLUENCE_BASE}/rest/api/content?title={CONFLUENCE_TITLE}&spaceKey={CONFLUENCE_SPACE}"
        res = requests.get(search_url, auth=auth)
        if res.ok and res.json()["results"]:
            page_id = res.json()["results"][0]["id"]
            update_confluence_page(page_id, html_body)
        else:
            print("❌ Unable to find or update Confluence page:", e)

    # Upload generated artifacts
    for file in os.listdir(REPORT_DIR):
        if file.endswith((".html", ".pdf")):
            upload_attachment(page_id, os.path.join(REPORT_DIR, file))

    print("✅ Report successfully published to Confluence.")
