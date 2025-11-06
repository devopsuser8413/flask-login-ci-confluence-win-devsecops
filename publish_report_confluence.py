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
CONFLUENCE_PARENT_TITLE = os.getenv("CONFLUENCE_TITLE", "DevSecOps Test Result Report")

REPORT_DIR = Path("report")
AUTH = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)
HEADERS = {"Content-Type": "application/json"}


# ============================================================
# 🔍 Helper Functions
# ============================================================
def safe_read(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def get_page(title, space):
    """Return page ID and version if it exists."""
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"spaceKey": space, "title": title, "expand": "version"}
    r = requests.get(url, params=params, auth=AUTH)
    if r.status_code == 200 and r.json().get("results"):
        result = r.json()["results"][0]
        return result["id"], result["version"]["number"]
    return None, 0


def create_page(title, body, space, parent_id=None):
    """Create a new Confluence page."""
    url = f"{CONFLUENCE_BASE}/rest/api/content/"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    r = requests.post(url, json=payload, auth=AUTH, headers=HEADERS)
    if r.status_code in (200, 201):
        page_id = r.json()["id"]
        print(f"✅ Created page: {title} (ID: {page_id})")
        return page_id
    elif "already exists" in r.text:
        existing_id, _ = get_page(title, space)
        print(f"ℹ️ Page '{title}' already exists (ID: {existing_id}), will update instead.")
        return existing_id
    else:
        print(f"❌ Failed to create page '{title}': {r.status_code} - {r.text}")
        return None


def update_page(page_id, title, body):
    """Update an existing Confluence page (auto-increment version)."""
    # Get current version
    version_url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}?expand=version"
    r = requests.get(version_url, auth=AUTH)
    if r.status_code == 200:
        current_ver = r.json()["version"]["number"]
    else:
        current_ver = 1

    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": current_ver + 1},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    update_url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}"
    r = requests.put(update_url, json=payload, auth=AUTH, headers=HEADERS)
    if r.status_code in (200, 201):
        print(f"✅ Updated page '{title}' to version {current_ver + 1}")
    else:
        print(f"❌ Failed to update page '{title}': {r.status_code} - {r.text}")


# ============================================================
# 📎 Attachment Upload (Fixed for Cloud)
# ============================================================
def upload_attachment(page_id, file_path):
    """Attach or replace files on a Confluence page."""
    file_name = os.path.basename(file_path)
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment"
    headers = {"X-Atlassian-Token": "no-check"}

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/octet-stream")}
        r = requests.post(url, files=files, auth=AUTH, headers=headers)

    if r.status_code in (200, 201):
        print(f"📎 Uploaded: {file_name}")
        return

    if "same file name" in r.text or r.status_code in (400, 409):
        attach_url = f"{url}?filename={file_name}"
        get_resp = requests.get(attach_url, auth=AUTH)
        if get_resp.status_code == 200 and get_resp.json().get("results"):
            attach_id = get_resp.json()["results"][0]["id"]
            update_url = f"{CONFLUENCE_BASE}/rest/api/content/{attach_id}/data"
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                update_resp = requests.post(update_url, files=files, auth=AUTH, headers=headers)
                if update_resp.status_code in (200, 201):
                    print(f"↻ Updated attachment: {file_name}")
                else:
                    print(f"⚠️ Failed updating {file_name}: {update_resp.status_code}")
    else:
        print(f"❌ Failed upload {file_name}: {r.status_code} - {r.text}")


# ============================================================
# 🧠 Page Builders
# ============================================================
def build_child_body(version):
    return f"""
    <h2>DevSecOps Test & Security Report v{version}</h2>
    <p><b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>This page contains all test & security reports generated from Jenkins.</p>
    <p><i>All related artifacts are attached below.</i></p>
    <p><ac:structured-macro ac:name="attachments"></ac:structured-macro></p>
    """


def build_parent_body():
    """Rebuild parent page with all child links."""
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"spaceKey": CONFLUENCE_SPACE, "limit": 200}
    r = requests.get(url, params=params, auth=AUTH)
    links = ""
    if r.status_code == 200:
        for page in r.json().get("results", []):
            title = page["title"]
            if title.startswith("Test Result Report v"):
                page_id = page["id"]
                links += f'<li><a href="{CONFLUENCE_BASE}/pages/{page_id}/{title.replace(" ", "+")}">{title}</a></li>'
    return f"""
    <h1>DevSecOps Test & Security Reports</h1>
    <p>Automatically updated by Jenkins.</p>
    <ul>{links}</ul>
    <p><i>Generated automatically by the Jenkins DevSecOps Pipeline.</i></p>
    """


# ============================================================
# 🚀 Main Execution
# ============================================================
if __name__ == "__main__":
    version = "N/A"
    vf = REPORT_DIR / "version.txt"
    if vf.exists():
        version = vf.read_text().strip()

    pytest_output = safe_read(REPORT_DIR / "pytest_output.txt").lower()
    status = "PASS" if "failed" not in pytest_output else "FAIL"

    parent_id, _ = get_page(CONFLUENCE_PARENT_TITLE, CONFLUENCE_SPACE)
    if not parent_id:
        parent_id = create_page(CONFLUENCE_PARENT_TITLE, "<p>DevSecOps index page.</p>", CONFLUENCE_SPACE)

    child_title = f"Test Result Report v{version} ({status})"
    child_body = build_child_body(version)

    child_id, child_ver = get_page(child_title, CONFLUENCE_SPACE)
    if child_id:
        update_page(child_id, child_title, child_body)
    else:
        child_id = create_page(child_title, child_body, CONFLUENCE_SPACE, parent_id)

    if child_id:
        print("📤 Uploading artifacts...")
        for f in REPORT_DIR.glob("*"):
            if f.is_file():
                upload_attachment(child_id, str(f))

    if parent_id:
        parent_body = build_parent_body()
        update_page(parent_id, CONFLUENCE_PARENT_TITLE, parent_body)
        print("✅ Parent page updated successfully.")
