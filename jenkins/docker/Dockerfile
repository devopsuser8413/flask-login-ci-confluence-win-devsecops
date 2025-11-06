# ================================================
# 🐋 Secure Flask Application - Jenkins-based Dockerfile
# Location: jenkins/docker/Dockerfile
# ================================================

# Base Python image (lightweight & stable)
FROM python:3.11-slim AS base

# --------------------------------
# 🧩 Environment Setup
# --------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# --------------------------------
# 🧰 System Dependencies
# --------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# --------------------------------
# 📦 Install Python Dependencies
# --------------------------------
# Copy requirements from /jenkins/scripts/
COPY ../../jenkins/scripts/requirements.txt .

# Upgrade pip & install dependencies securely
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --------------------------------
# 📁 Copy Flask Application Code
# --------------------------------
COPY ../../app/ $APP_HOME/

# --------------------------------
# 👤 Security Hardening
# --------------------------------
RUN useradd -m flaskuser
USER flaskuser

# --------------------------------
# ⚙️ Flask Runtime Configuration
# --------------------------------
ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_ENV=production \
    FLASK_DEBUG=False

# Flask default port
EXPOSE 5000

# --------------------------------
# 🩺 Healthcheck (used in CI/CD)
# --------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:5000/health || exit 1

# --------------------------------
# 🚀 Run Flask Application
# --------------------------------
CMD ["python", "app.py"]
