from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from .schemas import LoanFeatures, LoanPredictResponse
from .xai_engine import XAIEngine
from contextlib import asynccontextmanager
import os
import threading
import time
import urllib.request

# Keep-Alive Pinger to prevent Render instances from going offline/sleeping
def keep_alive_pinger():
    # Wait 30 seconds for the web server to boot up
    time.sleep(30)
    self_url = os.environ.get("RENDER_EXTERNAL_URL")
    print(f"[Pinger] Active. Self URL: {self_url}")
    while True:
        if self_url:
            try:
                # Use standard library to ping self (prevents dependency errors)
                req = urllib.request.Request(self_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    pass
                print("[Pinger] Successfully pinged backend self-url.")
            except Exception as e:
                print(f"[Pinger] Failed to ping backend self-url: {e}")
        # Sleep for 10 minutes (Render sleep threshold is 15 minutes)
        time.sleep(10 * 60)

# Start keep-alive thread only when running in the Render production environment
if os.environ.get("RENDER"):
    threading.Thread(target=keep_alive_pinger, daemon=True).start()


# Thread-safe global engine instance
engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager that pre-loads models into memory on startup."""
    global engine
    try:
        print("Starting FastAPI app... Preloading ML models.")
        engine = XAIEngine()
    except Exception as e:
        print(f"CRITICAL: Failed to load ML models on startup: {e}")
        # We don't crash the server process immediately, but we log the error.
        # Requests will fail with HTTP 500.
    yield
    print("Shutting down FastAPI app...")

app = FastAPI(
    title="Automated Explainable AI (XAI) System API",
    description="FastAPI backend for high-performance ML inference and local SHAP explanations for Loan Default prediction.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Simple API healthcheck."""
    global engine
    if engine is None or engine.lgb_model is None:
        return {"status": "unhealthy", "message": "ML models not loaded"}
    return {"status": "healthy", "message": "API and ML models are fully operational"}

@app.post(
    "/api/v1/predict",
    response_model=LoanPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Loan Default Risk and Generate SHAP Explanation"
)
async def predict_loan_default(
    features: LoanFeatures,
    username: Optional[str] = Query(None),
):
    """
    Accepts loan applicant details, runs LightGBM inference, and returns 
    the probability of default, prediction class, risk level, and a base64-encoded SHAP waterfall plot.
    """
    global engine
    
    if engine is None:
        try:
            engine = XAIEngine()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference engine is not initialized. Model load failed: {str(e)}"
            )

    try:
        prob, pred, risk_level, shap_plot, text_explanation = engine.predict_risk(
            features, username=username
        )
        
        return LoanPredictResponse(
            probability=prob,
            prediction=pred,
            risk_level=risk_level,
            model_type="lightgbm",
            shap_plot=shap_plot,
            text_explanation=text_explanation
        )
    except Exception as e:
        print(f"Error during inference request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during inference processing: {str(e)}"
        )
