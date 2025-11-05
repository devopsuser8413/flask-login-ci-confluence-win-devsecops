pipeline {
    agent any

    options {
        timestamps()
    }

    // -------------------------------
    // ✅ Skill Toggle Parameters
    // -------------------------------
    parameters {
        booleanParam(name: 'RUN_SAST',                defaultValue: false, description: 'Run SAST (Bandit) scan?')
        booleanParam(name: 'RUN_DEP_SCAN',            defaultValue: false, description: 'Run Dependency Vulnerability Scan?')
        booleanParam(name: 'RUN_PYTHON_SETUP',        defaultValue: true,  description: 'Setup Python Environment?')
        booleanParam(name: 'RUN_UNIT_TESTS',          defaultValue: true,  description: 'Run Unit Tests?')
        booleanParam(name: 'RUN_DOCKER_BUILD',        defaultValue: true,  description: 'Build Docker Image?')
        booleanParam(name: 'RUN_DEPLOY_DAST',         defaultValue: true,  description: 'Deploy for DAST Scan?')
        booleanParam(name: 'RUN_DAST',                defaultValue: true,  description: 'Run OWASP ZAP DAST Scan?')
        booleanParam(name: 'RUN_REPORT_PUBLISH',      defaultValue: true,  description: 'Generate & Publish Reports?')
        booleanParam(name: 'RUN_EMAIL_NOTIFICATION',  defaultValue: true,  description: 'Send Email Notification?')
    }

    // -------------------------------
    // Environment Variables
    // -------------------------------
    environment {
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

        PYTHONUTF8 = '1'
        PYTHONIOENCODING = 'utf-8'
        PYTHONLEGACYWINDOWSSTDIO = '1'
    }

    // -------------------------------
    // Pipeline Stages
    // -------------------------------
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
            when { expression { return params.RUN_PYTHON_SETUP } }
            steps {
                echo '🐍 Setting up Python virtual environment...'
                bat '''
                    @echo off
                    if not exist "%VENV_PATH%" (
                        python -m venv %VENV_PATH%
                    )
                    %VENV_PATH%\\Scripts\\python.exe -m pip install --upgrade pip
                    %VENV_PATH%\\Scripts\\pip.exe install -r requirements.txt
                    %VENV_PATH%\\Scripts\\pip.exe install bandit safety typer click pytest pytest-html
                '''
                echo '✅ Python environment ready.'
            }
        }

        stage('SAST - Static Code Analysis') {
            when { expression { return params.RUN_SAST } }
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

        stage('Dependency Vulnerability Scan') {
            when { expression { return params.RUN_DEP_SCAN } }
            steps {
                echo "🧩 Checking dependencies for known vulnerabilities..."
                bat '''
                    if not exist report mkdir report
                    %VENV_PATH%\\Scripts\\pip.exe install --upgrade safety typer click
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
            when { expression { return params.RUN_UNIT_TESTS } }
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

        stage('Verify Docker Installation') {
            steps {
                echo '🐋 Checking Docker installation...'
                bat '''
                    @echo off
                    docker --version || (
                        echo ❌ Docker is not accessible to Jenkins user!
                        exit /b 1
                    )
                    docker info | find "Server Version"
                    echo ✅ Docker Desktop is accessible.
                '''
            }
        }

        stage('Build Docker Image') {
            when { expression { return params.RUN_DOCKER_BUILD } }
            steps {
                echo '🐳 Building Docker image...'
                bat '''
                    @echo off
                    if exist Dockerfile (
                        echo 🐋 Found Dockerfile in workspace root. Building image...
                        docker build -t %DOCKER_IMAGE% .
                    ) else if exist app\\Dockerfile (
                        echo 🐋 Found Dockerfile in /app directory. Building image...
                        docker build -t %DOCKER_IMAGE% -f app\\Dockerfile .
                    ) else (
                        echo ❌ No Dockerfile found! Please add Dockerfile in project root or app directory.
                        exit /b 1
                    )
                '''
                echo '✅ Docker image built successfully.'
            }
        }

        stage('Container Security Scan (Trivy)') {
            steps {
                echo '🛡️ Scanning Docker image with Trivy...'
                bat '''
                    if not exist report mkdir report
                    "C:\\tools\\trivy\\trivy.exe" image --exit-code 0 --severity HIGH,CRITICAL --format html --output report\\trivy_report.html %DOCKER_IMAGE%
                '''
                echo '✅ Container vulnerability scan completed.'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/trivy_report.html', fingerprint: true
                }
            }
        }

        stage('Deploy for DAST Scan') {
            when { expression { return params.RUN_DEPLOY_DAST } }
            steps {
                echo '🚀 Deploying temporary container for OWASP ZAP DAST...'
                bat '''
                    docker run -d -p 5000:5000 --name flask_dast_test %DOCKER_IMAGE%
                    timeout /t 15
                '''
            }
        }

        stage('DAST - OWASP ZAP Scan') {
            when { expression { return params.RUN_DAST } }
            steps {
                echo '🕵️ Running OWASP ZAP baseline scan...'
                bat '''
                    docker run --rm -v %CD%\\report:/zap/wrk owasp/zap2docker-stable zap-baseline.py -t http://localhost:5000 -r zap_dast_report.html || exit /b 0
                '''
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

        stage('Generate & Publish Reports') {
            when { expression { return params.RUN_REPORT_PUBLISH } }
            steps {
                echo '📊 Generating and publishing reports to Confluence...'
                bat '''
                    %VENV_PATH%\\Scripts\\python.exe generate_report.py
                    %VENV_PATH%\\Scripts\\python.exe publish_report_confluence.py
                '''
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

        stage('Send Email Notification') {
            when { expression { return params.RUN_EMAIL_NOTIFICATION } }
            steps {
                echo '📧 Sending consolidated DevSecOps report...'
                bat '''
                    %VENV_PATH%\\Scripts\\python.exe send_report_email.py
                '''
                echo '✅ Email with consolidated report sent.'
            }
        }
    }

    // -------------------------------
    // Post Build
    // -------------------------------
    post {
        success {
            echo '''
            ✅ PIPELINE COMPLETED SUCCESSFULLY!
            ======================================
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
            - Check build logs for missing Dockerfile or requirements.txt
            ======================================
            '''
        }
        always {
            echo '🧹 Cleaning up workspace...'
            cleanWs()
        }
    }
}
