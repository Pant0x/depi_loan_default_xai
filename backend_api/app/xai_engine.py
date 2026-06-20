import threading
import joblib
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, Any, Tuple, Optional
from .schemas import LoanFeatures

class XAIEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(XAIEngine, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, artifacts_dir: Optional[Path] = None):
        if getattr(self, '_initialized', False):
            return
        
        if artifacts_dir is None:
            # Resolve relative to this file's location
            self.artifacts_dir = Path(__file__).resolve().parent.parent / "artifacts"
        else:
            self.artifacts_dir = Path(artifacts_dir)

        self.lgb_model = None
        self.lr_model = None
        self.scaler = None
        self.feature_names = None
        self.shap_explainer = None
        
        self.load_artifacts()
        self._initialized = True

    def load_artifacts(self):
        """Load all ML models, scalers, and feature metadata in a thread-safe manner."""
        print(f"Loading ML artifacts from {self.artifacts_dir}...")
        
        lgb_path = self.artifacts_dir / "lightgbm_model (1).joblib"
        lr_path = self.artifacts_dir / "logistic_regression_pipeline.joblib"
        scaler_path = self.artifacts_dir / "scaler.pkl"
        feature_names_path = self.artifacts_dir / "feature_names.pkl"

        if not lgb_path.exists():
            raise FileNotFoundError(f"LightGBM model not found at {lgb_path}")
        if not lr_path.exists():
            raise FileNotFoundError(f"Logistic Regression model not found at {lr_path}")
        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found at {scaler_path}")
        if not feature_names_path.exists():
            raise FileNotFoundError(f"Feature names metadata not found at {feature_names_path}")

        # Load models
        self.lgb_model = joblib.load(lgb_path)
        self.lr_model = joblib.load(lr_path)
        
        # Load scaler and feature names
        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)
        with open(feature_names_path, "rb") as f:
            self.feature_names = pickle.load(f)

        # Initialize TreeExplainer on LightGBM model
        # Using check_additivity=False to prevent warning crashes during service operation
        self.shap_explainer = shap.TreeExplainer(self.lgb_model)
        print("ML artifacts and SHAP explainer loaded successfully!")

    def transform_to_dataframe(self, input_features: LoanFeatures) -> pd.DataFrame:
        """
        Applies feature engineering and one-hot encoding to align raw input features
        with the exact 36-feature space expected by the ML model.
        """
        # 1. Base categorical mapping
        # Yes/No -> 1/0
        yes_no_map = {"Yes": 1, "No": 0}
        hasmortgage = yes_no_map[input_features.hasmortgage]
        hasdependents = yes_no_map[input_features.hasdependents]
        hascosigner = yes_no_map[input_features.hascosigner]

        # Education: Ordinal mapping
        edu_map = {"High School": 0, "Bachelor's": 1, "Master's": 2, "PhD": 3}
        education_val = edu_map[input_features.education]

        # 2. Extract continuous features
        age = input_features.age
        income = input_features.income
        loanamount = input_features.loanamount
        creditscore = input_features.creditscore
        monthsemployed = input_features.monthsemployed
        numcreditlines = input_features.numcreditlines
        interestrate = input_features.interestrate
        loanterm = input_features.loanterm
        dtiratio = input_features.dtiratio

        # 3. Handle One-Hot Categorical features (Base classes dropped: employmenttype_Full-time, maritalstatus_Divorced, loanpurpose_Auto)
        employmenttype_Part_time = 1 if input_features.employmenttype == "Part-time" else 0
        employmenttype_Self_employed = 1 if input_features.employmenttype == "Self-employed" else 0
        employmenttype_Unemployed = 1 if input_features.employmenttype == "Unemployed" else 0

        maritalstatus_Married = 1 if input_features.maritalstatus == "Married" else 0
        maritalstatus_Single = 1 if input_features.maritalstatus == "Single" else 0

        loanpurpose_Business = 1 if input_features.loanpurpose == "Business" else 0
        loanpurpose_Education = 1 if input_features.loanpurpose == "Education" else 0
        loanpurpose_Home = 1 if input_features.loanpurpose == "Home" else 0
        loanpurpose_Other = 1 if input_features.loanpurpose == "Other" else 0

        # 4. Feature Engineering
        log_income = np.log1p(income)
        log_loanamount = np.log1p(loanamount)
        
        # Kept for compatibility
        loan_to_income = loanamount / (income + 1)
        monthly_income = income / 12
        employment_ratio = monthsemployed / (age * 12 + 1)
        
        # Credit Score Bands
        if creditscore <= 580:
            creditscore_band = 0
        elif creditscore <= 670:
            creditscore_band = 1
        elif creditscore <= 740:
            creditscore_band = 2
        else:
            creditscore_band = 3

        # High Risk Flag
        high_risk_flag = 1 if (dtiratio > 0.45 and creditscore < 600) else 0

        # Interaction & composite features
        # Monthly payment estimate (simple approximation)
        monthly_payment_est = (loanamount * interestrate / 100) / (loanterm + 1)

        # Payment-to-income: real affordability pressure
        payment_to_income = monthly_payment_est / (monthly_income + 1)

        # Debt burden: DTI × Interest rate (stress index)
        debt_burden_score = dtiratio * interestrate

        # Composite risk score (weighted combination of top predictors)
        cs_norm = (creditscore - 300) / 550  # 0 = worst, 1 = best
        rate_norm = interestrate / 30       # 0 = lowest, 1 = highest
        risk_score = 0.40 * (1 - cs_norm) + 0.35 * dtiratio + 0.25 * rate_norm

        # Log-scale loan-to-income (robust to outliers)
        log_loan_to_income = log_loanamount - log_income

        # Triple-risk binary flag
        is_very_high_risk = 1 if (creditscore < 580 and dtiratio > 0.40 and interestrate > 15) else 0

        # Age × employment stability
        age_employment_interaction = age * monthsemployed

        # 5. Assemble dictionary matching features order
        raw_features_dict = {
            "age": age,
            "income": income,
            "loanamount": loanamount,
            "creditscore": creditscore,
            "monthsemployed": monthsemployed,
            "numcreditlines": numcreditlines,
            "interestrate": interestrate,
            "loanterm": loanterm,
            "dtiratio": dtiratio,
            "education": education_val,
            "hasmortgage": hasmortgage,
            "hasdependents": hasdependents,
            "hascosigner": hascosigner,
            "log_income": log_income,
            "log_loanamount": log_loanamount,
            "employmenttype_Part-time": employmenttype_Part_time,
            "employmenttype_Self-employed": employmenttype_Self_employed,
            "employmenttype_Unemployed": employmenttype_Unemployed,
            "maritalstatus_Married": maritalstatus_Married,
            "maritalstatus_Single": maritalstatus_Single,
            "loanpurpose_Business": loanpurpose_Business,
            "loanpurpose_Education": loanpurpose_Education,
            "loanpurpose_Home": loanpurpose_Home,
            "loanpurpose_Other": loanpurpose_Other,
            "loan_to_income": loan_to_income,
            "monthly_income": monthly_income,
            "employment_ratio": employment_ratio,
            "creditscore_band": creditscore_band,
            "high_risk_flag": high_risk_flag,
            "monthly_payment_est": monthly_payment_est,
            "payment_to_income": payment_to_income,
            "debt_burden_score": debt_burden_score,
            "risk_score": risk_score,
            "log_loan_to_income": log_loan_to_income,
            "is_very_high_risk": is_very_high_risk,
            "age_employment_interaction": age_employment_interaction
        }

        # Convert to DataFrame with exact column order
        df = pd.DataFrame([raw_features_dict], columns=self.feature_names)
        return df

    def scale_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scales the 36 engineered features using the pre-loaded StandardScaler."""
        scaled_data = self.scaler.transform(df)
        scaled_df = pd.DataFrame(scaled_data, columns=self.feature_names)
        return scaled_df

    def generate_shap_plot(self, df_raw: pd.DataFrame, df_scaled: pd.DataFrame) -> Optional[str]:
        """
        Generates a local SHAP waterfall plot for a single prediction using TreeExplainer
        and encodes it as a base64 string.
        """
        try:
            # Generate SHAP values for the scaled input row
            shap_values = self.shap_explainer(df_scaled)
            
            # Construct a clean Explanation object using the raw (unscaled) data for plotting
            # so the labels show real-world values (e.g., age = 35) instead of Z-scores.
            exp = shap.Explanation(
                values=shap_values.values[0],
                base_values=shap_values.base_values[0],
                data=df_raw.iloc[0].values,
                feature_names=self.feature_names
            )

            # Draw the plot in headless mode
            plt.figure(figsize=(10, 6))
            shap.plots.waterfall(exp, max_display=10, show=False)
            
            # Save the figure to an in-memory buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close()
            
            # Encode as base64
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return img_b64
        except Exception as e:
            print(f"Error generating SHAP explanation plot: {e}")
            return None

    def predict_risk(self, input_features: LoanFeatures, model_type: str = "lightgbm") -> Tuple[float, int, str, Optional[str]]:
        """
        Preprocesses inputs, performs risk probability prediction, and generates SHAP explanations.
        Returns:
            probability (float), prediction (int), risk_level (str), shap_plot_b64 (str or None)
        """
        # 1. Transform raw inputs to dataframe with engineered features
        df_raw = self.transform_to_dataframe(input_features)

        # 2. Scale features
        df_scaled = self.scale_features(df_raw)

        # 3. Model inference based on selected type
        if model_type == "logistic_regression":
            # Logistic Regression Pipeline has the scaler step inside it.
            # We must pass the raw features df_raw to prevent double-scaling!
            prob = float(self.lr_model.predict_proba(df_raw)[0, 1])
            shap_plot_b64 = None  # TreeExplainer is only compatible with LightGBM in our setup
        else:
            # LightGBM requires scaled features input
            prob = float(self.lgb_model.predict_proba(df_scaled)[0, 1])
            # Generate SHAP waterfall plot
            shap_plot_b64 = self.generate_shap_plot(df_raw, df_scaled)

        # Calculate prediction binary flag (0.5 threshold)
        prediction = 1 if prob >= 0.5 else 0

        # Define risk levels based on probability
        if prob < 0.25:
            risk_level = "Low Risk"
        elif prob < 0.60:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"

        return prob, prediction, risk_level, shap_plot_b64
