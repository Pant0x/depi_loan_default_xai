from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class LoanFeatures(BaseModel):
    age: int = Field(
        ..., 
        ge=18, 
        le=100, 
        description="Age of the loan applicant",
        json_schema_extra={"example": 35}
    )
    income: float = Field(
        ..., 
        ge=0.0, 
        description="Annual income of the applicant",
        json_schema_extra={"example": 55000.0}
    )
    loanamount: float = Field(
        ..., 
        ge=0.0, 
        description="Loan amount requested",
        json_schema_extra={"example": 15000.0}
    )
    creditscore: int = Field(
        ..., 
        ge=300, 
        le=850, 
        description="Credit score of the applicant (FICO range 300-850)",
        json_schema_extra={"example": 680}
    )
    monthsemployed: int = Field(
        ..., 
        ge=0, 
        description="Total months in current employment",
        json_schema_extra={"example": 60}
    )
    numcreditlines: int = Field(
        ..., 
        ge=0, 
        description="Number of open credit lines",
        json_schema_extra={"example": 5}
    )
    interestrate: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Interest rate of the loan (percentage)",
        json_schema_extra={"example": 12.0}
    )
    loanterm: int = Field(
        ..., 
        ge=1, 
        description="Duration of the loan in months",
        json_schema_extra={"example": 36}
    )
    dtiratio: float = Field(
        ..., 
        ge=0.0, 
        le=2.0, 
        description="Debt-to-Income ratio",
        json_schema_extra={"example": 0.35}
    )
    education: str = Field(
        ..., 
        description="Highest education level obtained",
        json_schema_extra={"example": "Bachelor's"}
    )
    employmenttype: str = Field(
        ..., 
        description="Employment status/type",
        json_schema_extra={"example": "Full-time"}
    )
    maritalstatus: str = Field(
        ..., 
        description="Marital status of the applicant",
        json_schema_extra={"example": "Married"}
    )
    loanpurpose: str = Field(
        ..., 
        description="Purpose of the loan",
        json_schema_extra={"example": "Home"}
    )
    hasmortgage: str = Field(
        ..., 
        description="Whether the applicant has an active mortgage (Yes/No)",
        json_schema_extra={"example": "No"}
    )
    hasdependents: str = Field(
        ..., 
        description="Whether the applicant has dependents (Yes/No)",
        json_schema_extra={"example": "No"}
    )
    hascosigner: str = Field(
        ..., 
        description="Whether the applicant has a co-signer (Yes/No)",
        json_schema_extra={"example": "No"}
    )

    @field_validator('education')
    def validate_education(cls, v: str) -> str:
        allowed = ["High School", "Bachelor's", "Master's", "PhD"]
        if v not in allowed:
            raise ValueError(f"education must be one of {allowed}")
        return v

    @field_validator('employmenttype')
    def validate_employmenttype(cls, v: str) -> str:
        allowed = ["Full-time", "Part-time", "Self-employed", "Unemployed"]
        if v not in allowed:
            raise ValueError(f"employmenttype must be one of {allowed}")
        return v

    @field_validator('maritalstatus')
    def validate_maritalstatus(cls, v: str) -> str:
        allowed = ["Divorced", "Married", "Single"]
        if v not in allowed:
            raise ValueError(f"maritalstatus must be one of {allowed}")
        return v

    @field_validator('loanpurpose')
    def validate_loanpurpose(cls, v: str) -> str:
        allowed = ["Auto", "Business", "Education", "Home", "Other"]
        if v not in allowed:
            raise ValueError(f"loanpurpose must be one of {allowed}")
        return v

    @field_validator('hasmortgage', 'hasdependents', 'hascosigner')
    def validate_yes_no(cls, v: str) -> str:
        allowed = ["Yes", "No"]
        if v not in allowed:
            raise ValueError(f"Field must be 'Yes' or 'No'")
        return v

class LoanPredictResponse(BaseModel):
    probability: float = Field(..., description="Default probability (0.0 to 1.0)")
    prediction: int = Field(..., description="Binary prediction: 1 for default, 0 for non-default")
    risk_level: str = Field(..., description="Risk category: Low Risk, Medium Risk, High Risk")
    model_type: str = Field(..., description="Model used for prediction")
    shap_plot: Optional[str] = Field(None, description="Base64-encoded SHAP waterfall plot image (or None if unavailable/not calculated)")
