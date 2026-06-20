import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the app
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from app.schemas import LoanFeatures
from app.xai_engine import XAIEngine

def run_test():
    print("Initializing XAI Inference Engine...")
    # Initialize engine with the absolute path of the artifacts directory
    artifacts_dir = current_dir / "artifacts"
    engine = XAIEngine(artifacts_dir=artifacts_dir)
    
    # Define a test sample
    sample = LoanFeatures(
        age=35,
        income=65000.0,
        loanamount=25000.0,
        creditscore=720,
        monthsemployed=48,
        numcreditlines=4,
        interestrate=8.5,
        loanterm=36,
        dtiratio=0.28,
        education="Bachelor's",
        employmenttype="Full-time",
        maritalstatus="Married",
        loanpurpose="Home",
        hasmortgage="Yes",
        hasdependents="No",
        hascosigner="No"
    )
    
    print("\n--- Testing LightGBM Model ---")
    try:
        prob, pred, risk_level, shap_plot, lime_plot, text_exp = engine.predict_risk(sample, model_type="lightgbm")
        print(f"Result: Probability={prob:.5f}, Prediction={pred}, Risk={risk_level}")
        if shap_plot:
            print(f"Success! SHAP Plot generated. Base64 length: {len(shap_plot)}")
        else:
            print("WARNING: SHAP Plot was not generated.")
        if lime_plot:
            print(f"Success! LIME Plot generated. Base64 length: {len(lime_plot)}")
        else:
            print("WARNING: LIME Plot was not generated.")
        print(f"Text explanation: {text_exp}")
    except Exception as e:
        print(f"FAILED LightGBM test: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n--- Testing Logistic Regression Model ---")
    try:
        prob, pred, risk_level, shap_plot, lime_plot, text_exp = engine.predict_risk(sample, model_type="logistic_regression")
        print(f"Result: Probability={prob:.5f}, Prediction={pred}, Risk={risk_level}")
        if shap_plot is None:
            print("Success! Logistic Regression skipped SHAP plot generation as expected.")
        else:
            print(f"WARNING: Logistic Regression unexpectedly returned a SHAP plot: {len(shap_plot)} chars.")
        if lime_plot:
            print(f"Success! LIME Plot generated for Logistic Regression. Base64 length: {len(lime_plot)}")
        else:
            print("WARNING: LIME Plot was not generated for Logistic Regression.")
        print(f"Text explanation: {text_exp}")
    except Exception as e:
        print(f"FAILED Logistic Regression test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    print("\nAll automated tests completed successfully!")
    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
