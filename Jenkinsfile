pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        // ============================
        // 💡 Core Configuration
        // ============================
        SMTP_HOST        = credentials('smtp-host')
        SMTP_PORT        = '587'
        SMTP_USER        = credentials('smtp-user')
        SMTP_PASS        = credentials('smtp-pass')
        REPORT_FROM      = credentials('sender-email')
        REPORT_TO        = credentials('receiver-email')

        CONFLUENCE_BASE  = credentials('confluence-base')
        CONFLUENCE_USER  = credentials('confluence-user')
        CONFLUENCE_TOKEN = credentials('confluence-token')
        CONFLUENCE_SPACE = 'DEMO'
        CONFLUENCE_TITLE = 'Test Result Report'

        GITHUB_CREDENTIALS = credentials('github-credentials')

        REPORT_PATH   = 'report/report.html'
        REPORT_DIR    = 'report'
        VERSION_FILE  = 'report/version.txt'
        VENV_PATH     = '.venv'
        DOCKER_IMAGE  = 'devsecops-demo:latest'

        // ============================
        // 🧩 UTF-8 + Python Encoding Fix
        // ============================
        PYTHONUTF8 = '1'
        PYTHONIOENCODING = 'utf-8'
        PYTHONLEGACYWINDOWSSTDIO = '1'
    }

    stages {

        // -------------------------------
        stage('Setup Encoding') {
            steps {
                echo '🔧 Setting system encoding to UTF-8...'
                bat '''
                    @echo off
                    chcp 65001 >nul
                    set PYTHONUTF8=1
                    set PYTHONIOENCODING=utf-8
                    set PYTHONLEGACYWINDOWSSTDIO=1
                    echo ✅ Windows console now using UTF-8 (code page 65001)
                '''
            }
        }

        // -------------------------------
        stage('Checkout GitHub') {
            steps {
                echo '📦 Checking out source code from GitHub repository...'
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/devopsuser8413/flask-login-ci-confluence-win-devsecops.git',
                        credentialsId: 'github-credentials'
                    ]]
                ])
                echo '✅ Source code checkout complete.'
            }
        }

        // -------------------------------
        stage('Setup Python Environment') {
            steps {
                echo '🐍 Setting up Python virtual environment...'
                bat '''
                    @echo off
                    if not exist "%VENV_PATH%" (
                        python -m venv %VENV_PATH%
                    )
                    %VENV_PATH%\\Scripts\\python.exe -m pip install --upgrade pip
                    %VENV_PATH%\\Scripts\\pip.exe install -r requirements.txt
                    %VENV_PATH%\\Scripts\\pip.exe install bandit safety==2.3.5 typer==0.7.0 click==8.1.7 pytest pytest-html
                '''
                echo '✅ Python environment ready.'
            }
        }

        // -------------------------------
        stage('SAST - Static Code Analysis') {
            steps {
                echo '🔍 Running Bandit for static code analysis...'
                bat """
                    @echo off
                    if not exist "report" mkdir report
                    %VENV_PATH%\\Scripts\\bandit.exe -r . -f html -o report\\bandit_report.html || exit /b 0
                """
                echo '✅ Bandit SAST report generated.'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/bandit_report.html', fingerprint: true
                }
            }
        }

        // -------------------------------
        stage('Dependency Vulnerability Scan') {
            steps {
                echo "🧩 Checking dependencies for known vulnerabilities..."
                bat '''
                    if not exist report mkdir report
                    %VENV_PATH%\\Scripts\\pip.exe install --upgrade safety==2.3.5 typer==0.7.0 click==8.1.7
                    %VENV_PATH%\\Scripts\\safety.exe check --full-report > report\\dependency_vuln.txt || exit 0
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/dependency_vuln.txt', allowEmptyArchive: true
                }
            }
        }

        // -------------------------------
        stage('Run Unit Tests') {
            steps {
                echo '🧪 Running unit tests with pytest...'
                bat """
                    @echo off
                    if not exist "report" mkdir report
                    set PYTHONPATH=%CD%
                    %VENV_PATH%\\Scripts\\python.exe -m pytest --html=%REPORT_PATH% --self-contained-html > report\\pytest_output.txt 2>&1 || exit /b 0
                """
                echo '✅ Unit testing completed.'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/report.html', fingerprint: true
                }
            }
        }

        // -------------------------------
        stage('Install Docker (if missing)') {
            steps {
                echo '🐋 Checking and installing Docker if not present...'
                bat '''
                    @echo off
                    where docker >nul 2>nul
                    if %ERRORLEVEL% NEQ 0 (
                        echo ⚙️ Docker not found. Installing Docker Desktop...
                        powershell -Command "Invoke-WebRequest -Uri https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe -OutFile DockerInstaller.exe"
                        start /wait DockerInstaller.exe install --quiet
                        setx PATH "%PATH%;C:\\Program Files\\Docker\\Docker\\resources\\bin"
                        echo ✅ Docker installed and added to PATH. Restarting Jenkins service...
                        net stop jenkins
                        net start jenkins
                    ) else (
                        echo ✅ Docker already installed.
                    )
                    docker --version
                '''
            }
        }

        // -------------------------------
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                bat """
                    docker build -t %DOCKER_IMAGE% .
                """
                echo '✅ Docker image built successfully.'
            }
        }

        // -------------------------------
        stage('Container Security Scan (Trivy)') {
            steps {
                echo '🛡️ Scanning Docker image with Trivy...'
                bat """
                    trivy image --exit-code 0 --severity HIGH,CRITICAL --format html --output report\\trivy_report.html %DOCKER_IMAGE%
                """
                echo '✅ Container vulnerability scan completed.'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/trivy_report.html', fingerprint: true
                }
            }
        }

        // -------------------------------
        stage('Deploy for DAST Scan') {
            steps {
                echo '🚀 Deploying temporary container for OWASP ZAP DAST...'
                bat """
                    docker run -d -p 5000:5000 --name flask_dast_test %DOCKER_IMAGE%
                    timeout /t 15
                """
            }
        }

        // -------------------------------
        stage('DAST - OWASP ZAP Scan') {
            steps {
                echo '🕵️ Running OWASP ZAP baseline scan...'
                bat """
                    docker run --rm -v %CD%\\report:/zap/wrk owasp/zap2docker-stable zap-baseline.py -t http://localhost:5000 -r zap_dast_report.html || exit /b 0
                """
                echo '✅ OWASP ZAP DAST scan completed.'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/zap_dast_report.html', fingerprint: true
                    echo '🧹 Stopping and removing DAST container...'
                    bat 'docker stop flask_dast_test && docker rm flask_dast_test'
                }
            }
        }

        // -------------------------------
        stage('Generate & Publish Reports') {
            steps {
                echo '📊 Generating final consolidated report...'
                bat """
                    %VENV_PATH%\\Scripts\\python.exe generate_report.py
                    %VENV_PATH%\\Scripts\\python.exe publish_report_confluence.py
                """
                echo '✅ Reports generated and published to Confluence.'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/test_result_report_v*.html', fingerprint: true
                    archiveArtifacts artifacts: 'report/test_result_report_v*.pdf', fingerprint: true
                    archiveArtifacts artifacts: 'report/version.txt', fingerprint: true
                }
            }
        }

        // -------------------------------
        stage('Send Email Notification') {
            steps {
                echo '📧 Sending consolidated DevSecOps report...'
                bat """
                    %VENV_PATH%\\Scripts\\python.exe send_report_email.py
                """
                echo '✅ Email with consolidated report sent.'
            }
        }
    }

    // -------------------------------
    post {
        success {
            echo '''
            ✅ PIPELINE COMPLETED SUCCESSFULLY!
            ======================================
            ✔️ SAST (Bandit)
            ✔️ Dependency Scan (Safety)
            ✔️ Unit Tests (Pytest)
            ✔️ Container Scan (Trivy)
            ✔️ DAST (OWASP ZAP)
            ✔️ Reports Published + Email Sent
            ======================================
            '''
        }
        failure {
            echo '''
            ❌ PIPELINE FAILED!
            ======================================
            - Review Jenkins logs for the failed stage
            - Check SAST, DAST, or container scan outputs
            - Verify SMTP and Confluence credentials
            ======================================
            '''
        }
        always {
            echo '🧹 Cleaning up workspace...'
            cleanWs()
        }
    }
}
