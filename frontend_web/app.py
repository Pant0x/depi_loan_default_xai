import os
import json
import requests
import threading
import time
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "xai_super_secret_key_12345")

# Configuration
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000")

# Supabase DB Configuration for Auth (REST API)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nceokvawdzxwjzqitszd.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jZW9rdmF3ZHp4d2p6cWl0c3pkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMzM3MjYsImV4cCI6MjA5NzcwOTcyNn0.fNqf3Lq8MkpAwFW3yRFJ2jhHgar1NeDXZ1eLnjYOIJo")

CHATBOT_MODEL = os.environ.get("GEMINI_MODEL", "models/gemini-3.5-flash")
CHATBOT_HISTORY_LIMIT = 12
CHATBOT_HISTORY_MAX_CHARS = 240

PROJECT_CHATBOT_SYSTEM_PROMPT = """
You are the official LOAN XAI SYSTEM assistant.

Scope rules:
- Only answer questions about this project: loan default prediction, underwriting workflow, FastAPI backend, Flask frontend, LightGBM, SHAP explainability, form fields, and dashboard interpretation.
- If the user asks about anything outside this project, politely refuse and redirect to project-related help.
- Never claim external facts as certain unless they are provided in the user context.

Behavior rules:
- Be concise, practical, and user-friendly.
- On result pages, explain the current applicant result using provided context (risk level, probability, features, and top drivers).
- Do not expose secrets or environment variables.
- If context is missing, ask one targeted follow-up question.
""".strip()

PROJECT_CHATBOT_KNOWLEDGE = """
Project facts:
- The system predicts loan default risk and shows explainability artifacts.
- Frontend: Flask app with pages for landing, architecture, form, and dashboard results.
- Backend: FastAPI endpoint /api/v1/predict for inference.
- Inference uses LightGBM with SHAP explanations exclusively.
- Result view includes: probability, prediction class, risk level, SHAP plot, and text explanations.
""".strip()

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


def _extract_genai_text(response_obj):
    """Extract text across multiple google-genai response shapes."""
    if response_obj is None:
        return None

    text = getattr(response_obj, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response_obj, "candidates", None)
    if candidates:
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None)
            if parts:
                out = []
                for part in parts:
                    piece = getattr(part, "text", None)
                    if isinstance(piece, str) and piece.strip():
                        out.append(piece.strip())
                if out:
                    return "\n".join(out)

    if isinstance(response_obj, dict):
        maybe_text = response_obj.get("text")
        if isinstance(maybe_text, str) and maybe_text.strip():
            return maybe_text.strip()

    return None


def _call_gemini(user_message, page_context, history):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return (
            "Chatbot is not configured yet. Please set GEMINI_API_KEY in the frontend environment "
            "to enable project assistant responses."
        )

    from google import genai

    history_lines = []
    for msg in history[-CHATBOT_HISTORY_LIMIT:]:
        role = msg.get("role", "user")
        content = str(msg.get("content", "")).strip()
        if content:
            history_lines.append(f"{role.upper()}: {content}")

    serialized_context = json.dumps(page_context or {}, ensure_ascii=True)
    prompt = (
        f"{PROJECT_CHATBOT_SYSTEM_PROMPT}\n\n"
        f"{PROJECT_CHATBOT_KNOWLEDGE}\n\n"
        f"PAGE_CONTEXT_JSON:\n{serialized_context}\n\n"
        f"RECENT_CHAT:\n" + ("\n".join(history_lines) if history_lines else "(empty)") + "\n\n"
        f"USER_MESSAGE:\n{user_message}\n\n"
        "Return only the assistant answer text."
    )

    client = genai.Client(api_key=api_key)

    candidate_models = [
        CHATBOT_MODEL,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    # Keep model order but remove duplicates.
    seen = set()
    ordered_models = []
    for model_name in candidate_models:
        if model_name and model_name not in seen:
            seen.add(model_name)
            ordered_models.append(model_name)

    last_error = None
    for model_name in ordered_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.4,
                    "top_p": 0.95,
                    "max_output_tokens": 768,
                },
            )
            final_text = _extract_genai_text(response)
            if final_text:
                return final_text
        except Exception as model_error:
            last_error = model_error
            print(f"Chatbot model call failed for {model_name}: {model_error}")

    if last_error:
        return (
            "I cannot reach the Gemini model right now. Check GEMINI_API_KEY validity, "
            "model access, and billing/quota in Google AI Studio."
        )

    return "I could not generate a response right now. Please try rephrasing your question about this project."

# ==========================================================================
# Routes
# ==========================================================================
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                               "favicon.svg", mimetype="image/svg+xml")

@app.route("/", methods=["GET"])
def index():
    """Serves the Landing Page."""
    if "user" in session:
        return redirect(url_for("app_dashboard"))
    return render_template("landing.html")

@app.route("/architecture", methods=["GET"])
def architecture():
    """Serves the Architecture Page."""
    return render_template("architecture.html")

@app.route("/signup", methods=["POST"])
def signup():
    """Handles User Registration."""
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    
    # Validate email has standard domain indicators like gmail or .com
    email_lower = email.lower()
    if len(username) < 3 or "@" not in email_lower or ("gmail" not in email_lower and ".com" not in email_lower):
        flash("Username must be 3+ chars and you must provide a valid email (e.g. @gmail.com).", "danger")
        return redirect(url_for("index"))

    # 1. Check if user already exists
    check_resp = supabase_request("GET", "logins", params={"username": f"eq.{username}", "select": "id"})
    if check_resp and check_resp.status_code == 200 and len(check_resp.json()) > 0:
        flash("Username already exists. Please log in instead.", "warning")
        return redirect(url_for("index"))

    # 2. Hash the email to store it in the password_hash column for RLS compatibility
    email_hash = generate_password_hash(email)
    
    insert_data = {
        "username": username,
        "email": email,
        "password_hash": email_hash
    }
    
    insert_resp = supabase_request("POST", "logins", json_data=insert_data)
    
    if insert_resp and insert_resp.status_code in (200, 201):
        session["user"] = username
        flash(f"Welcome, {username}! Account created successfully.", "success")
        return redirect(url_for("app_dashboard"))
    else:
        # Fallback for dev/missing column
        error_msg = insert_resp.text if insert_resp is not None else 'None'
        print(f"Supabase error: {error_msg}")
        flash(f"Database error: {error_msg}", "danger")
        return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    """Handles User Login."""
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()

    # Query Supabase for the user's password_hash
    resp = supabase_request("GET", "logins", params={"username": f"eq.{username}", "select": "username,password_hash"})
    
    if resp and resp.status_code == 200:
        data = resp.json()
        if len(data) == 1:
            user_record = data[0]
            # Verify the "email" matches the stored "password_hash"
            stored_hash = user_record.get("password_hash")
            if stored_hash and check_password_hash(stored_hash, email):
                session["user"] = username
                flash("Authentication successful.", "success")
                return redirect(url_for("app_dashboard"))
            else:
                flash("Invalid email for this username.", "danger")
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

        predict_url = f"{BACKEND_API_URL}/api/v1/predict"
        response = requests.post(predict_url, json=payload, timeout=10.0)
        
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


@app.route("/api/chatbot/message", methods=["POST"])
def chatbot_message():
    """Project-scoped chatbot endpoint backed by Gemini."""
    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()
    page_context = data.get("page_context", {})

    if not user_message:
        return jsonify({"error": "Message is required."}), 400

    chat_history = session.get("chat_history", [])
    if not isinstance(chat_history, list):
        chat_history = []

    # Keep a tiny bounded history to avoid oversized cookie/session headers.
    slim_history = []
    for msg in chat_history[-4:]:
        role = str(msg.get("role", "user"))
        content = str(msg.get("content", ""))[:CHATBOT_HISTORY_MAX_CHARS]
        slim_history.append({"role": role, "content": content})

    try:
        reply = _call_gemini(user_message, page_context, slim_history)
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            "reply": "I hit a temporary issue while answering. Please try again in a few seconds.",
            "error": "chat_processing_failed",
        }), 200

    slim_history.append({"role": "user", "content": user_message[:CHATBOT_HISTORY_MAX_CHARS]})
    slim_history.append({"role": "assistant", "content": str(reply)[:CHATBOT_HISTORY_MAX_CHARS]})
    session["chat_history"] = slim_history[-4:]

    return jsonify({"reply": reply})


@app.route("/api/chatbot/reset", methods=["POST"])
def chatbot_reset():
    session.pop("chat_history", None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
