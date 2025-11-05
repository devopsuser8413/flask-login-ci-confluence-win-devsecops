from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
import os
import re

# ============================================================
# 🔐 Flask App Initialization with Security & Config Hardening
# ============================================================
app = Flask(__name__)

# Use environment secret for production
app.secret_key = os.environ.get("FLASK_SECRET", os.urandom(24))

# Restrict session lifetime and cookie behavior
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=bool(os.environ.get("FLASK_SECURE_COOKIES", True)),
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    TEMPLATES_AUTO_RELOAD=True,
)

# In-memory user store (for demo only)
USERS = {
    "alice": generate_password_hash("password123"),
    "admin": generate_password_hash("Admin@12345")
}

# ==================================
# 🧩 Security & Utility Functions
# ==================================

def sanitize_input(value: str) -> str:
    """Basic sanitization to prevent injection/XSS."""
    if value:
        return re.sub(r"[<>\"']", "", value.strip())
    return ""

def is_authenticated():
    """Check if user is logged in."""
    return bool(session.get("user"))

def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        flash("Please log in to continue.", "warning")
        return redirect(url_for("login"))

# ==================================
# 📋 Routes
# ==================================

@app.route("/", methods=["GET"])
def index():
    if is_authenticated():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = sanitize_input(request.form.get("username"))
        password = sanitize_input(request.form.get("password"))
        pw_hash = USERS.get(username)

        if pw_hash and check_password_hash(pw_hash, password):
            session["user"] = username
            session.permanent = True
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not is_authenticated():
        return require_auth()
    username = session.get("user")
    return render_template("dashboard.html", username=username)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

# ============================================================
# 🚫 Error Handlers & Secure Headers
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.after_request
def apply_security_headers(response):
    """Add standard OWASP-recommended HTTP security headers."""
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline';"
    return response

# ============================================================
# 🧪 Health Check (for CI/CD and DAST verification)
# ============================================================
@app.route("/health")
def health():
    return {"status": "ok", "app": "flask-login-demo"}, 200

# ============================================================
# 🚀 Application Entry Point
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
