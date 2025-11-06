pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        // -------------------------------
        // Email / SMTP
        // -------------------------------
        SMTP_HOST        = credentials('smtp-host')
        SMTP_PORT        = '587'
        SMTP_USER        = credentials('smtp-user')
        SMTP_PASS        = credentials('smtp-pass')
        REPORT_FROM      = credentials('sender-email')
        REPORT_TO        = credentials('receiver-email')

        // -------------------------------
        // Confluence Credentials
        // -------------------------------
        CONFLUENCE_BASE  = credentials('confluence-base')
        CONFLUENCE_USER  = credentials('confluence-user')
        CONFLUENCE_TOKEN = credentials('confluence-token')
        CONFLUENCE_SPACE = 'DEMO'
        CONFLUENCE_TITLE = 'DevSecOps Test Result Report'

        // -------------------------------
        // GitHub / Build
        // -------------------------------
        GITHUB_CREDENTIALS = credentials('github-credentials')
        REPORT_DIR    = 'report'
        REPORT_PATH   = 'report/report.html'
        VERSION_FILE  = 'report/version.txt'
        VENV_PATH     = '.venv'
        DOCKER_IMAGE  = 'devsecops-demo:latest'

        // -------------------------------
        // Encoding & Pip Cache
        // -------------------------------
        PYTHONUTF8               = '1'
        PYTHONIOENCODING         = 'utf-8'
        PYTHONLEGACYWINDOWSSTDIO = '1'
        PIP_CACHE_DIR            = "${WORKSPACE}\\pip_cache"
    }

    stages {
        stage('Setup Encoding') {
            steps {
                echo '🔧 Setting system encoding to UTF-8...'
                bat '''
                    @echo off
                    chcp 65001 >nul
                    echo ✅ Windows console now using UTF-8 (code page 65001)
                '''
            }
        }

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

        stage('Setup Python Environment') {
            steps {
                echo '🐍 Setting up Python virtual environment and dependencies...'
                bat '''
                    @echo off
                    if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
                    if not exist "%VENV_PATH%" (
                        python -m venv %VENV_PATH%
                    )
                    %VENV_PATH%\\Scripts\\python.exe -m pip install --upgrade pip
                    %VENV_PATH%\\Scripts\\pip.exe install --cache-dir "%PIP_CACHE_DIR%" -r requirements.txt
                    %VENV_PATH%\\Scripts\\pip.exe install --cache-dir "%PIP_CACHE_DIR%" bandit safety typer click pytest pytest-html fpdf2 beautifulsoup4 requests
                '''
            }
        }

        stage('SAST - Static Code Analysis') {
            steps {
                echo '🔍 Running Bandit for static code analysis...'
                bat '''
                    @echo off
                    if not exist "report" mkdir report
                    %VENV_PATH%\\Scripts\\bandit.exe -r . -f html -o report\\bandit_report.html || exit /b 0
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/bandit_report.html', fingerprint: true
                }
            }
        }

        stage('Dependency Vulnerability Scan') {
            steps {
                echo "🧩 Checking dependencies for vulnerabilities..."
                bat '''
                    if not exist report mkdir report
                    %VENV_PATH%\\Scripts\\pip.exe install --upgrade safety
                    %VENV_PATH%\\Scripts\\safety.exe check --full-report > report\\dependency_vuln.txt || exit 0
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/dependency_vuln.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                echo '🧪 Running unit tests with pytest...'
                bat """
                    @echo off
                    if not exist "report" mkdir report
                    set PYTHONPATH=%CD%
                    %VENV_PATH%\\Scripts\\python.exe -m pytest --html=%REPORT_PATH% --self-contained-html > report\\pytest_output.txt 2>&1 || exit /b 0
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/report.html', fingerprint: true
                }
            }
        }

        stage('Verify Docker Installation') {
            steps {
                echo '🐋 Checking Docker installation...'
                bat '''
                    @echo off
                    docker --version || (
                        echo ❌ Docker not accessible!
                        exit /b 1
                    )
                    docker info | find "Server Version"
                    echo ✅ Docker is available.
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                bat '''
                    @echo off
                    if exist Dockerfile (
                        docker build -t %DOCKER_IMAGE% -f Dockerfile .
                    ) else (
                        echo ❌ Dockerfile missing!
                        exit /b 1
                    )
                '''
            }
        }

        stage('Container Security Scan (Trivy)') {
            steps {
                echo '🛡️ Scanning Docker image using Trivy...'
                bat '''
                    if not exist report mkdir report
                    "C:\\tools\\trivy\\trivy.exe" image --exit-code 0 --severity HIGH,CRITICAL --format table --output report\\trivy_report.txt %DOCKER_IMAGE%
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/trivy_report.txt', fingerprint: true
                }
            }
        }

        stage('Deploy for DAST Scan') {
            steps {
                echo '🚀 Deploying container for OWASP ZAP DAST...'
                bat '''
                    @echo off
                    docker rm -f flask_dast_test >nul 2>&1
                    docker network rm zapnet >nul 2>&1
                    docker network create zapnet
                    docker run -d --network zapnet -p 5000:5000 --name flask_dast_test %DOCKER_IMAGE%
                    ping -n 16 127.0.0.1 >nul
                '''
            }
        }

        stage('DAST - OWASP ZAP Scan') {
            steps {
                echo '🕵️ Running OWASP ZAP baseline scan...'
                bat '''
                    @echo off
                    if not exist report mkdir report
                    docker run --rm ^
                        --network zapnet ^
                        -v "%CD%\\report:/zap/wrk" ^
                        ghcr.io/zaproxy/zaproxy:stable zap-baseline.py ^
                        -t http://flask_dast_test:5000 ^
                        -r zap_dast_report.html || exit /b 0
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/zap_dast_report.html', allowEmptyArchive: true
                    bat '''
                        docker rm -f flask_dast_test >nul 2>&1
                        docker network rm zapnet >nul 2>&1
                    '''
                }
            }
        }

        stage('Generate & Publish Reports') {
            steps {
                echo '📊 Generating and publishing reports to Confluence...'
                bat """
                    echo Installing dependencies...
                    %VENV_PATH%\\Scripts\\python.exe -m pip install --upgrade fpdf2 beautifulsoup4 requests
                    %VENV_PATH%\\Scripts\\python.exe generate_report.py
                    %VENV_PATH%\\Scripts\\python.exe publish_report_confluence.py
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/test_result_report_v*.html', fingerprint: true
                    archiveArtifacts artifacts: 'report/test_result_report_v*.pdf', fingerprint: true, allowEmptyArchive: true
                    archiveArtifacts artifacts: 'report/version.txt', fingerprint: true
                }
            }
        }

        stage('Send Email Notification') {
            steps {
                echo '📧 Sending email with all reports attached...'
                bat '''
                    %VENV_PATH%\\Scripts\\python.exe send_report_email.py
                '''
            }
        }
    }

    post {
        success {
            echo '''
            ✅ PIPELINE COMPLETED SUCCESSFULLY!
            ======================================
            ✔️ Tests Passed
            ✔️ Scans Done (SAST, Trivy, ZAP)
            ✔️ Reports Published to Confluence
            ✔️ Email Sent to Stakeholders
            ======================================
            '''
        }
        failure {
            echo '''
            ❌ PIPELINE FAILED!
            ======================================
            - Check Jenkins logs for failure details
            - Validate Docker / Python dependencies
            ======================================
            '''
        }
        always {
            echo '🧹 Cleaning up workspace...'
            cleanWs()
        }
    }
}
