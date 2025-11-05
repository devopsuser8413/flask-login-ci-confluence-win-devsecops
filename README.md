# 🔐 Flask DevSecOps CI/CD Pipeline — End-to-End Setup Guide

A complete **DevSecOps-driven Jenkins CI/CD pipeline** integrating:
- Flask web app with authentication
- Automated testing (Pytest + HTML/PDF reporting)
- Static code analysis (Bandit)
- Dependency vulnerability scanning (Safety)
- Container security scanning (Trivy)
- Dynamic security testing (OWASP ZAP)
- Email and Confluence report publishing

---

## 🧩 1. System Requirements & Software Installation

### ☕ 1.1 Install Java (Jenkins Dependency)

#### Step 1: Download Java JDK 17+
🔗 [Oracle JDK Downloads](https://www.oracle.com/java/technologies/downloads/)

#### Step 2: Install and Verify
```bash
java -version
```

#### Step 3: Set Environment Variable (Windows)
**Option A — GUI Method:**
1. Press `Win + R` → type `sysdm.cpl` → Enter.
2. Go to **Advanced → Environment Variables**.
3. Add a new System variable:
   - **Variable name:** `JAVA_HOME`
   - **Value:** `C:\Program Files\Java\jdk-17`
4. Edit `Path` → Add:
   ```
   %JAVA_HOME%\bin
   ```

**Option B — PowerShell (Admin):**
```powershell
setx JAVA_HOME "C:\Program Files\Java\jdk-17"
setx PATH "%PATH%;%JAVA_HOME%\bin"
```

✅ **Verify:**
```bash
echo %JAVA_HOME%
java -version
```

---

### 🐍 1.2 Install Python 3.10+

#### Step 1: Download
🔗 [Python Official Downloads](https://www.python.org/downloads/)

During installation, check:
✅ “Add Python to PATH”.

#### Step 2: Verify Installation
```bash
python --version
pip --version
```

#### Step 3: If PATH not set
```powershell
setx PATH "%PATH%;C:\Users\<username>\AppData\Local\Programs\Python\Python310;C:\Users\<username>\AppData\Local\Programs\Python\Python310\Scripts" /M
```

---

### ⚙️ 1.3 Install Jenkins LTS

#### Step 1: Download Jenkins
🔗 [Jenkins LTS for Windows/Linux](https://www.jenkins.io/download/)

#### Step 2: Installation Options
- **Windows Service**: Run the installer and start automatically.
- **Manual (CLI)**:
  ```bash
  java -jar jenkins.war
  ```

#### Step 3: Access Jenkins
👉 [http://localhost:8080](http://localhost:8080)

#### Step 4: Retrieve Initial Password
```
C:\ProgramData\Jenkins\.jenkins\secrets\initialAdminPassword
```

Copy and paste into Jenkins unlock screen.

#### Step 5: Install Suggested Plugins
Choose “Install Suggested Plugins” during initial setup.

---

## 🧰 2. Jenkins Configuration

### 🧩 2.1 Install Required Plugins
Go to **Manage Jenkins → Manage Plugins → Available tab**, and install:

| Category | Plugin Name |
|-----------|--------------|
| Source Control | GitHub Plugin |
| Build Management | Pipeline Plugin |
| Email | Email Extension Plugin |
| Python | ShiningPanda or Python Plugin |
| Security | Warnings Next Generation Plugin |
| Documentation | Confluence Publisher Plugin |
| Visualization | HTML Publisher Plugin |

Restart Jenkins after installation.

---

### 🔑 2.2 Configure Jenkins Credentials

Go to: **Manage Jenkins → Credentials → Global → Add Credentials**

| ID | Description | Example |
|----|--------------|----------|
| `github-credentials` | GitHub Personal Access Token | `<username> / ghp_xxxxxxx` |
| `smtp-user` | Email Username | `noreply@company.com` |
| `smtp-pass` | Email App Password | `abcdxyz123` |
| `confluence-user` | Atlassian Account Email | `your.email@company.com` |
| `confluence-token` | Confluence API Token | `ATAT-xxxxxx` |
| `confluence-base` | Confluence Base URL | `https://yourcompany.atlassian.net/wiki` |

---

## 📘 3. Confluence Setup

### 3.1 Create Confluence Space
1. Login to Confluence → **Spaces → Create Space**
2. Select **Blank Space** or **Documentation Space**
3. Provide a **space key** (e.g., `DEMO`)
4. Assign permissions to your Jenkins user (view/edit).

### 3.2 Generate Confluence API Token
1. Go to [https://id.atlassian.com/manage/api-tokens](https://id.atlassian.com/manage/api-tokens)
2. Click **Create API Token**
3. Copy token → store securely in Jenkins credentials (`confluence-token`).

### 3.3 Verify Permissions
Ensure the Confluence user has:
- **View** and **Add Pages** permissions in the target space.
- Access to the Confluence REST API.

---

## 🔐 4. GitHub Integration

### 4.1 Create GitHub Personal Access Token
1. Go to: **Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**  
2. Click **Generate new token**:
   - Select scopes: `repo`, `workflow`, `admin:repo_hook`
3. Copy the token.
4. Add to Jenkins credentials as `github-credentials`.

### 4.2 Repository Setup
Ensure your GitHub repo has:
- Jenkinsfile at root
- Requirements.txt
- Flask app and tests committed

---

## ✉️ 5. App Email Setup (SMTP)

If using Gmail:
1. Enable **2-Step Verification**
2. Go to **Manage Google Account → Security → App Passwords**
3. Generate password → name as “Jenkins CI”
4. Save generated 16-character password.
5. Use as `SMTP_PASS` in Jenkins credentials.

---

## 🧱 6. Project Architecture

```
flask-login-ci-confluence-win-devsecops/
├── app.py
├── test_app.py
├── requirements.txt
├── templates/
│   ├── login.html
│   └── dashboard.html
├── report/
│   ├── report.html
│   ├── bandit_report.html
│   ├── dependency_vuln.txt
│   └── test_result_report.pdf
├── publish_report_confluence.py
├── send_report_email.py
├── generate_report.py
├── Dockerfile
├── Jenkinsfile
└── README.md
```

---

## 🧪 7. Jenkins Pipeline Setup

### Create a New Pipeline Job
1. Open Jenkins → **New Item → Pipeline**
2. Name: `Flask-DevSecOps-Pipeline`
3. Choose: **Pipeline from SCM**
4. Set SCM: `Git`
   - Repository URL: `https://github.com/devopsuser8413/flask-login-ci-confluence-win-devsecops.git`
   - Credentials: `github-credentials`
5. Script Path: `Jenkinsfile`

---

## 🧩 8. Jenkinsfile Overview

Each stage represents a DevSecOps layer:

| Stage | Tool | Purpose |
|--------|------|----------|
| Checkout GitHub | Git | Pull latest code |
| Setup Python Env | pip/venv | Install dependencies |
| SAST | Bandit | Scan for insecure code |
| Dependency Scan | Safety | Check vulnerable packages |
| Unit Tests | Pytest | Run test cases |
| Docker Build | Docker | Build app container |
| Container Scan | Trivy | Scan for CVEs in image |
| DAST | OWASP ZAP | Runtime scan of app |
| Reports | ReportLab + Confluence API | Publish results |
| Notification | SMTP | Email summary |

---

## 🧠 9. Detailed Explanation of Jenkins Stages

### **Stage 1: Checkout GitHub**
- Uses Jenkins `git` plugin.
- Fetches main branch source code.

### **Stage 2: Setup Python Environment**
- Creates `.venv` folder.
- Installs packages from `requirements.txt`.

### **Stage 3: Static Code Analysis (SAST)**
- Runs `bandit -r .`.
- Generates `report/bandit_report.html`.

### **Stage 4: Dependency Scan (Safety)**
- Runs `python -m safety check`.
- Outputs `report/dependency_vuln.txt`.

### **Stage 5: Run Unit Tests**
- Executes `pytest --html=report/report.html`.
- Produces HTML report for test results.

### **Stage 6: Build Docker Image**
- Builds image `flask-ci-app:latest`.
- Pushes to registry if configured.

### **Stage 7: Container Security Scan (Trivy)**
- Scans Docker image for vulnerabilities.
- Exports results to `report/trivy_report.txt`.

### **Stage 8: DAST - OWASP ZAP Scan**
- Runs dynamic web app scan.
- Detects OWASP Top 10 vulnerabilities.

### **Stage 9: Generate & Publish Reports**
- Consolidates Bandit, Safety, and Pytest outputs.
- Uploads to Confluence using API.

### **Stage 10: Send Email Notification**
- Uses SMTP credentials to email report summary.

---

## 📄 10. Jenkinsfile Sample

(See previous code block in the earlier message for full Groovy pipeline content.)

---

## 📈 11. Outputs Generated

| File | Description |
|------|--------------|
| `report/report.html` | Pytest test results |
| `report/bandit_report.html` | Static code analysis report |
| `report/dependency_vuln.txt` | Dependency vulnerability summary |
| `report/test_result_report.pdf` | Final summary report |
| Confluence Page | Auto-generated report page |
| Email | Summary with links and attachments |

---

## 🧠 12. Security Layers Implemented

| Layer | Tool | Description |
|--------|------|--------------|
| **SAST** | Bandit | Static Python code scan |
| **DAST** | OWASP ZAP | Dynamic runtime scan |
| **Dependency** | Safety | Python package CVE detection |
| **Container** | Trivy | Docker image vulnerability scan |
| **Secrets** | Jenkins Credentials | Encrypted storage of sensitive data |

---

## 📘 13. References
- Jenkins: [https://www.jenkins.io](https://www.jenkins.io)
- Bandit: [https://bandit.readthedocs.io](https://bandit.readthedocs.io)
- Safety: [https://pyup.io/safety](https://pyup.io/safety)
- Trivy: [https://aquasecurity.github.io/trivy](https://aquasecurity.github.io/trivy)
- Confluence REST API: [https://developer.atlassian.com/cloud/confluence/rest](https://developer.atlassian.com/cloud/confluence/rest)

---

## 🏁 Maintainer Info

**Author:** Your Name  
**Department:** DevSecOps Engineering  
**Organization:** Your Company  
**Email:** you@company.com  
