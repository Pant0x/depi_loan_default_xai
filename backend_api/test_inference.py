import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from app.schemas import LoanFeatures
from app.xai_engine import XAIEngine

def run_test():
    print("Initializing XAI Inference Engine...")
    artifacts_dir = current_dir / "artifacts"
    engine = XAIEngine(artifacts_dir=artifacts_dir)
    
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
    
    print("\n--- Testing LightGBM + SHAP Pipeline ---")
    try:
        prob, pred, risk_level, shap_plot, text_exp = engine.predict_risk(sample)
        print(f"Result: Probability={prob:.5f}, Prediction={pred}, Risk={risk_level}")
        if shap_plot:
            print(f"Success! SHAP Plot generated. Base64 length: {len(shap_plot)}")
        else:
            print("WARNING: SHAP Plot was not generated.")
        print(f"Text explanation: {text_exp}")
    except Exception as e:
        print(f"FAILED inference test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    print("\nAll automated tests completed successfully!")
    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
