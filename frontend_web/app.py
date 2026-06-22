import os
import requests
import threading
import time
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "xai_super_secret_key_12345")

# Configuration
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000")

# Supabase DB Configuration for Auth (REST API)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nceokvawdzxwjzqitszd.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jZW9rdmF3ZHp4d2p6cWl0c3pkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMzM3MjYsImV4cCI6MjA5NzcwOTcyNn0.fNqf3Lq8MkpAwFW3yRFJ2jhHgar1NeDXZ1eLnjYOIJo")

# ==========================================================================
# Keep-Alive Pinger (Render)
# ==========================================================================
def keep_alive_pinger():
    time.sleep(30)
    self_url = os.environ.get("RENDER_EXTERNAL_URL")
    while True:
        if self_url:
            try:
                requests.get(self_url, timeout=10)
            except:
                pass
        if BACKEND_API_URL:
            try:
                requests.get(f"{BACKEND_API_URL}/health", timeout=10)
            except:
                pass
        time.sleep(10 * 60)

if os.environ.get("RENDER"):
    threading.Thread(target=keep_alive_pinger, daemon=True).start()

# ==========================================================================
# Authentication Decorator & Helper
# ==========================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("You must be logged in to access the underwriting suite.", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

def supabase_request(method, endpoint, json_data=None, params=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    
    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, headers=headers, json=json_data)
    return None

# ==========================================================================
# Routes
# ==========================================================================
@app.route("/", methods=["GET"])
def index():
    """Serves the Unified Landing and Architecture Page."""
    if "user" in session:
        return redirect(url_for("app_dashboard"))
    return render_template("landing.html")

@app.route("/signup", methods=["POST"])
def signup():
    """Handles User Registration."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    if len(username) < 3 or len(password) < 6:
        flash("Username must be 3+ chars and password 6+ chars.", "danger")
        return redirect(url_for("index"))

    # 1. Check if user already exists
    check_resp = supabase_request("GET", "logins", params={"username": f"eq.{username}", "select": "id"})
    if check_resp and check_resp.status_code == 200 and len(check_resp.json()) > 0:
        flash("Username already exists. Please log in instead.", "warning")
        return redirect(url_for("index"))

    # 2. Insert new user (Note: we use a dummy email since we dropped it from UI to simplify, or you can add it back)
    # We hash the password for security.
    pw_hash = generate_password_hash(password)
    
    insert_data = {
        "username": username,
        "email": f"{username}@lendverify.local", # placeholder
        "password_hash": pw_hash
    }
    
    insert_resp = supabase_request("POST", "logins", json_data=insert_data)
    
    if insert_resp and insert_resp.status_code in (200, 201):
        session["user"] = username
        flash(f"Welcome, {username}! Account created successfully.", "success")
        return redirect(url_for("app_dashboard"))
    else:
        # Fallback for dev/missing column
        print(f"Supabase error: {insert_resp.text if insert_resp else 'None'}")
        flash("Database configuration required: Missing 'password_hash' column in Supabase.", "danger")
        return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    """Handles User Login."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Query Supabase for the user
    resp = supabase_request("GET", "logins", params={"username": f"eq.{username}", "select": "username,password_hash"})
    
    if resp and resp.status_code == 200:
        data = resp.json()
        if len(data) == 1:
            user_record = data[0]
            # Verify password hash
            stored_hash = user_record.get("password_hash")
            if stored_hash and check_password_hash(stored_hash, password):
                session["user"] = username
                flash("Authentication successful.", "success")
                return redirect(url_for("app_dashboard"))
            else:
                flash("Invalid password.", "danger")
                return redirect(url_for("index"))
        else:
            flash("User not found.", "danger")
            return redirect(url_for("index"))
    
    flash("Database connection error.", "danger")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been securely logged out.", "info")
    return redirect(url_for("index"))


@app.route("/app", methods=["GET"])
@login_required
def app_dashboard():
    """Displays the loan applicant application form."""
    return render_template("form.html", username=session.get("user"))


@app.route("/result", methods=["POST"])
@login_required
def result():
    """Processes the submitted form data and queries the FastAPI backend."""
    try:
        # Numeric continuous inputs
        payload = {
            "age": int(request.form.get("age", 35)),
            "income": float(request.form.get("income", 55000.0)),
            "loanamount": float(request.form.get("loanamount", 15000.0)),
            "creditscore": int(request.form.get("creditscore", 680)),
            "monthsemployed": int(request.form.get("monthsemployed", 60)),
            "numcreditlines": int(request.form.get("numcreditlines", 5)),
            "interestrate": float(request.form.get("interestrate", 12.0)),
            "loanterm": int(request.form.get("loanterm", 36)),
            "dtiratio": float(request.form.get("dtiratio", 0.35)),
            "education": request.form.get("education", "Bachelor's"),
            "employmenttype": request.form.get("employmenttype", "Full-time"),
            "maritalstatus": request.form.get("maritalstatus", "Married"),
            "loanpurpose": request.form.get("loanpurpose", "Home"),
            "hasmortgage": request.form.get("hasmortgage", "No"),
            "hasdependents": request.form.get("hasdependents", "No"),
            "hascosigner": request.form.get("hascosigner", "No")
        }

        model_type = request.form.get("model_type", "lightgbm")

        predict_url = f"{BACKEND_API_URL}/api/v1/predict"
        response = requests.post(predict_url, json=payload, params={"model_type": model_type}, timeout=10.0)
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "Invalid input data.")
            flash(f"Input Validation Error: {error_detail}", "danger")
            return redirect(url_for("app_dashboard"))
            
        elif response.status_code != 200:
            error_detail = response.json().get("detail", "Backend service error.")
            flash(f"Inference Engine Error ({response.status_code}): {error_detail}", "danger")
            return redirect(url_for("app_dashboard"))

        return render_template("dashboard.html", result=response.json(), inputs=payload, username=session.get("user"))

    except requests.exceptions.Timeout:
        flash("The inference engine took too long to respond. Please try again later.", "danger")
        return redirect(url_for("app_dashboard"))
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for("app_dashboard"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
