import os
import json
from pathlib import Path
import requests

CONFLUENCE_BASE  = os.getenv("CONFLUENCE_BASE", "").rstrip("/")
CONFLUENCE_USER  = os.getenv("CONFLUENCE_USER", "")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "")
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE", "DEMO")
CONFLUENCE_TITLE = os.getenv("CONFLUENCE_TITLE", "DevSecOps Report")

REPORT_DIR = Path("report")
AUTH = (CONFLUENCE_USER, CONFLUENCE_TOKEN)
HEADERS_JSON = {"Content-Type": "application/json"}

def get_page(space, title):
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"title": title, "spaceKey": space, "expand": "version"}
    resp = requests.get(url, headers=HEADERS_JSON, auth=AUTH, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("size", 0) > 0:
        return data["results"][0]["id"], data["results"][0]["version"]["number"]
    return None, None

def update_or_create_page(space, title, body_html):
    pid, ver = get_page(space, title)
    if pid:
        url = f"{CONFLUENCE_BASE}/rest/api/content/{pid}"
        payload = {
            "id": pid,
            "type": "page",
            "title": title,
            "version": {"number": ver + 1},
            "body": {"storage": {"value": body_html, "representation": "storage"}},
        }
        resp = requests.put(url, headers=HEADERS_JSON, auth=AUTH, data=json.dumps(payload))
        resp.raise_for_status()
        print(f"✅ Updated Confluence page (v{ver+1})")
        return pid
    else:
        url = f"{CONFLUENCE_BASE}/rest/api/content"
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {"storage": {"value": body_html, "representation": "storage"}},
        }
        resp = requests.post(url, headers=HEADERS_JSON, auth=AUTH, data=json.dumps(payload))
        resp.raise_for_status()
        pid = resp.json()["id"]
        print(f"✅ Created new Confluence page: {pid}")
        return pid

def upload_or_update_attachment(page_id, file_path):
    name = file_path.name
    check = requests.get(f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment",
                         params={"filename": name, "expand": "version"},
                         headers=HEADERS_JSON, auth=AUTH)
    with open(file_path, "rb") as f:
        files = {"file": (name, f)}
        if check.status_code == 200 and check.json().get("size", 0) > 0:
            attach_id = check.json()["results"][0]["id"]
            r = requests.put(f"{CONFLUENCE_BASE}/rest/api/content/{attach_id}/data", files=files, auth=AUTH)
        else:
            r = requests.post(f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment", files=files, auth=AUTH)
    if r.status_code in (200, 201):
        print(f"📄 Uploaded/Updated: {name}")
    else:
        print(f"⚠️ Failed {name}: {r.status_code} - {r.text}")

def build_page_body():
    # Include summary metrics inline
    version_txt = (REPORT_DIR / "version.txt").read_text().strip() if (REPORT_DIR / "version.txt").exists() else "N/A"
    return f"""
    <h1>DevSecOps Test & Security Reports</h1>
    <p><b>Version:</b> {version_txt}</p>
    <p>This page is auto-updated by Jenkins with the latest reports.</p>
    <p>Artifacts include test results, SAST, dependency scan, Trivy, and ZAP findings.</p>
    <p><i>Generated automatically by the Jenkins DevSecOps Pipeline.</i></p>
    """

def main():
    pid = update_or_create_page(CONFLUENCE_SPACE, CONFLUENCE_TITLE, build_page_body())
    import glob
    for p in ["bandit_report.html","dependency_vuln.txt","report.html",
              "test_result_report_v*.html","trivy_report.txt","version.txt",
              "zap_dast_report.html","test_result_report_v*.pdf"]:
        for file in glob.glob(str(REPORT_DIR / p)):
            upload_or_update_attachment(pid, Path(file))
    print("✅ Report successfully published to Confluence.")

if __name__ == "__main__":
    main()
