import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "xai_super_secret_key_12345")

# Backend API configuration (Render friendly)
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000")

@app.route("/", methods=["GET"])
def index():
    """Displays the loan applicant application form with pre-filled default values."""
    return render_template("index.html")

@app.route("/result", methods=["POST"])
def result():
    """Processes the submitted form data and queries the FastAPI backend."""
    try:
        # 1. Parse and validate form parameters
        # Numeric continuous inputs
        age = int(request.form.get("age", 35))
        income = float(request.form.get("income", 55000.0))
        loanamount = float(request.form.get("loanamount", 15000.0))
        creditscore = int(request.form.get("creditscore", 680))
        monthsemployed = int(request.form.get("monthsemployed", 60))
        numcreditlines = int(request.form.get("numcreditlines", 5))
        interestrate = float(request.form.get("interestrate", 12.0))
        loanterm = int(request.form.get("loanterm", 36))
        dtiratio = float(request.form.get("dtiratio", 0.35))

        # Categorical string inputs
        education = request.form.get("education", "Bachelor's")
        employmenttype = request.form.get("employmenttype", "Full-time")
        maritalstatus = request.form.get("maritalstatus", "Married")
        loanpurpose = request.form.get("loanpurpose", "Home")
        
        # Binary string inputs (Yes/No)
        hasmortgage = request.form.get("hasmortgage", "No")
        hasdependents = request.form.get("hasdependents", "No")
        hascosigner = request.form.get("hascosigner", "No")

        # Model type query parameter
        model_type = request.form.get("model_type", "lightgbm")

        # 2. Package request body for FastAPI
        payload = {
            "age": age,
            "income": income,
            "loanamount": loanamount,
            "creditscore": creditscore,
            "monthsemployed": monthsemployed,
            "numcreditlines": numcreditlines,
            "interestrate": interestrate,
            "loanterm": loanterm,
            "dtiratio": dtiratio,
            "education": education,
            "employmenttype": employmenttype,
            "maritalstatus": maritalstatus,
            "loanpurpose": loanpurpose,
            "hasmortgage": hasmortgage,
            "hasdependents": hasdependents,
            "hascosigner": hascosigner
        }

        # 3. Call the FastAPI backend endpoint
        predict_url = f"{BACKEND_API_URL}/api/v1/predict"
        params = {"model_type": model_type}

        # Make request with a strict timeout (e.g., 10 seconds)
        response = requests.post(predict_url, json=payload, params=params, timeout=10.0)
        
        # 4. Check for response errors
        if response.status_code == 400:
            error_detail = response.json().get("detail", "Invalid input data.")
            flash(f"Input Validation Error: {error_detail}", "danger")
            return redirect(url_for("index"))
            
        elif response.status_code != 200:
            error_detail = response.json().get("detail", "Backend service error.")
            flash(f"Inference Engine Error ({response.status_code}): {error_detail}", "danger")
            return redirect(url_for("index"))

        # Success case
        data = response.json()
        
        # We also pass the input parameters to display them in the results dashboard
        return render_template(
            "dashboard.html",
            result=data,
            inputs=payload
        )

    except requests.exceptions.Timeout:
        flash("The inference engine took too long to respond. Please try again later.", "danger")
        return redirect(url_for("index"))
        
    except requests.exceptions.ConnectionError:
        flash("Could not connect to the inference backend. Please ensure the FastAPI server is running.", "danger")
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")
        return redirect(url_for("index"))

if __name__ == "__main__":
    # Bind to PORT environment variable for hosting platforms like Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
