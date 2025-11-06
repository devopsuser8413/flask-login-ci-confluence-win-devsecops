import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from pathlib import Path

# ============================================================
# ⚙️ Configuration
# ============================================================
CONFLUENCE_BASE  = os.getenv("CONFLUENCE_BASE")
CONFLUENCE_USER  = os.getenv("CONFLUENCE_USER")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE", "DEMO")
CONFLUENCE_TITLE = os.getenv("CONFLUENCE_TITLE", "DevSecOps Test Result Report")

REPORT_DIR = Path("report")
AUTH = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)
HEADERS = {"Content-Type": "application/json"}


# ============================================================
# 🔍 Helper Functions
# ============================================================
def safe_read(path):
    return Path(path).read_text(encoding="utf-8", errors="ignore") if Path(path).exists() else ""


def read_version():
    """Get version number from version.txt"""
    version_file = REPORT_DIR / "version.txt"
    if not version_file.exists():
        version_file.write_text("1")
        return 1
    try:
        return int(version_file.read_text().strip())
    except ValueError:
        return 1


def increment_version():
    """Increment and store new version"""
    current = read_version() + 1
    (REPORT_DIR / "version.txt").write_text(str(current))
    return current


def get_page_id(title):
    """Return Confluence page ID by title"""
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"spaceKey": CONFLUENCE_SPACE, "title": title}
    r = requests.get(url, params=params, auth=AUTH)
    if r.status_code == 200 and r.json().get("results"):
        return r.json()["results"][0]["id"]
    return None


def create_page(title, body, parent_id=None):
    """Always create new page"""
    url = f"{CONFLUENCE_BASE}/rest/api/content/"
    data = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if parent_id:
        data["ancestors"] = [{"id": parent_id}]
    r = requests.post(url, json=data, auth=AUTH, headers=HEADERS)
    if r.status_code in (200, 201):
        pid = r.json()["id"]
        print(f"✅ Created new page: {title} (ID: {pid})")
        return pid
    else:
        print(f"❌ Failed to create page {title}: {r.status_code} - {r.text}")
        return None


def update_page(page_id, title, body):
    """Update existing parent page index"""
    r = requests.get(f"{CONFLUENCE_BASE}/rest/api/content/{page_id}?expand=version", auth=AUTH)
    if r.status_code == 200:
        current_version = r.json()["version"]["number"]
    else:
        current_version = 1
    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": current_version + 1},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    r = requests.put(f"{CONFLUENCE_BASE}/rest/api/content/{page_id}", json=payload, auth=AUTH, headers=HEADERS)
    if r.status_code in (200, 201):
        print(f"✅ Updated parent page '{title}' to version {current_version + 1}")
    else:
        print(f"❌ Failed to update parent page: {r.status_code} - {r.text}")


def upload_attachment(page_id, file_path):
    """Attach artifacts to Confluence page"""
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment"
    headers = {"X-Atlassian-Token": "no-check"}
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        r = requests.post(url, files=files, auth=AUTH, headers=headers)
    if r.status_code in (200, 201):
        print(f"📎 Uploaded: {file_path}")
    else:
        print(f"⚠️ Failed to upload {file_path}: {r.status_code} - {r.text}")


# ============================================================
# 🚀 Main Execution
# ============================================================
if __name__ == "__main__":
    version = increment_version()
    pytest_log = safe_read(REPORT_DIR / "pytest_output.txt").lower()
    status = "PASS" if "failed" not in pytest_log else "FAIL"

    parent_id = get_page_id(CONFLUENCE_TITLE)
    if not parent_id:
        print("ℹ️ Parent page not found, creating...")
        parent_id = create_page(CONFLUENCE_TITLE, "<h1>DevSecOps Test Report Index</h1>")

    child_title = f"Test Result Report v{version} ({status})"
    body = f"""
    <h2>DevSecOps Test & Security Report v{version}</h2>
    <p><b>Status:</b> {status}</p>
    <p><b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>This page contains all reports for version {version}.</p>
    <p><ac:structured-macro ac:name="attachments"></ac:structured-macro></p>
    """
    page_id = create_page(child_title, body, parent_id)

    if page_id:
        for f in REPORT_DIR.glob("*"):
            if f.is_file():
                upload_attachment(page_id, str(f))
        print(f"✅ Uploaded all artifacts to child page {child_title}")

        # Update parent index
        parent_links = ""
        r = requests.get(f"{CONFLUENCE_BASE}/rest/api/content/{parent_id}/child/page", auth=AUTH)
        if r.status_code == 200:
            for p in r.json().get("results", []):
                parent_links += f'<li><a href="{CONFLUENCE_BASE}/pages/{p["id"]}/{p["title"].replace(" ", "+")}">{p["title"]}</a></li>'
        parent_body = f"<h1>DevSecOps Test & Security Reports</h1><ul>{parent_links}</ul>"
        update_page(parent_id, CONFLUENCE_TITLE, parent_body)

        print(f"✅ Parent page updated successfully with new child link.")
