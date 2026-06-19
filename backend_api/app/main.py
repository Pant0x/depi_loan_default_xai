from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .schemas import LoanFeatures, LoanPredictResponse
from .xai_engine import XAIEngine
from contextlib import asynccontextmanager

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
    if engine is None or engine.lgb_model is None or engine.lr_model is None:
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
    model_type: str = Query(
        "lightgbm",
        description="ML model to use for inference ('lightgbm' or 'logistic_regression')"
    )
):
    """
    Accepts loan applicant details, runs machine learning inference, and returns 
    the probability of default, prediction class, risk level, and a base64-encoded SHAP waterfall plot.
    """
    global engine
    
    # 1. Ensure engine is initialized
    if engine is None:
        try:
            engine = XAIEngine()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference engine is not initialized. Model load failed: {str(e)}"
            )

    # 2. Validate model type
    model_type = model_type.lower().strip()
    if model_type not in ["lightgbm", "logistic_regression"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model_type. Choose either 'lightgbm' or 'logistic_regression'."
        )

    # 3. Perform inference and explanation
    try:
        prob, pred, risk_level, shap_plot = engine.predict_risk(features, model_type=model_type)
        
        return LoanPredictResponse(
            probability=prob,
            prediction=pred,
            risk_level=risk_level,
            model_type=model_type,
            shap_plot=shap_plot
        )
    except Exception as e:
        # Log the full error on the server
        print(f"Error during inference request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during inference processing: {str(e)}"
        )
