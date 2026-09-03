import joblib
import json
import pandas as pd
from pydantic import BaseModel, ConfigDict
from pathlib import Path
from typing import List, Dict, Any

class PredictionRequest(BaseModel):
    transaction_id: str = "UNKNOWN"
    payment_id: str = "UNKNOWN"
    amount: float
    payment_method: str
    customer_segment: str
    transaction_hour: int
    days_since_last_payment: int
    previous_failures: int
    retry_count: int
    checkout_duration: int
    device_type: str
    location_type: str
    payment_gateway: str
    failure_reason: str
    subscription_status: str
    invoice_age_days: int
    amount_due: float
    payment_status: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 1500.50,
                "payment_method": "credit_card",
                "customer_segment": "loyal",
                "transaction_hour": 14,
                "days_since_last_payment": 30,
                "previous_failures": 1,
                "retry_count": 1,
                "checkout_duration": 45,
                "device_type": "mobile",
                "location_type": "domestic",
                "payment_gateway": "razorpay",
                "failure_reason": "network_error",
                "subscription_status": "active",
                "invoice_age_days": 5,
                "amount_due": 1500.50,
                "payment_status": "failed"
            }
        }
    )

class FactorDetail(BaseModel):
    feature: str
    direction: str
    importance: float

class PredictionResponse(BaseModel):
    risk_probability: float
    revenue_at_risk_prediction: int
    risk_level: str
    top_factors: List[str]                  
    top_factors_details: List[FactorDetail]  

class RiskPredictor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.models_dir = self.base_dir / "models"
        
        self.model_path = self.models_dir / "recovery_model.joblib"
        self.metadata_path = self.models_dir / "model_metadata.json"
        
        if not self.model_path.exists() or not self.metadata_path.exists():
            raise RuntimeError("Model or metadata not found. Please run training Phase 5 first.")
            
        self.model = joblib.load(self.model_path)
        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)
            
        self.feature_names = self.metadata["feature_names"]
        
        self.cat_mappings = {
            'payment_method': sorted(['credit_card', 'debit_card', 'upi', 'net_banking', 'wallet']),
            'customer_segment': sorted(['new', 'loyal', 'returning', 'high_value', 'churn_risk']),
            'device_type': sorted(['mobile', 'desktop', 'tablet']),
            'location_type': sorted(['domestic', 'international']),
            'payment_gateway': sorted(['razorpay']),
            'failure_reason': sorted(['insufficient_funds', 'bank_declined', 'network_error', 'authentication_failed', 'expired_card', 'None']),
            'subscription_status': sorted(['active', 'inactive', 'none']),
            'payment_status': sorted(['success', 'failed', 'pending', 'abandoned', 'overdue'])
        }

    def predict(self, data: PredictionRequest) -> PredictionResponse:
        raw_data = data.model_dump()
        
        processed_data = {}
        for feature in self.feature_names:
            val = raw_data.get(feature)
            if feature in self.cat_mappings:
                try:
                    processed_data[feature] = self.cat_mappings[feature].index(str(val))
                except ValueError:
                    processed_data[feature] = 0 
            else:
                processed_data[feature] = float(val)
                
        df = pd.DataFrame([processed_data])[self.feature_names]
        
        probability = float(self.model.predict_proba(df)[0][1])
        prediction = int(self.model.predict(df)[0])
        
        if probability >= 0.7:
            risk_level = "HIGH"
        elif probability >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        top_factors = []
        top_factors_details = []
        try:
            import shap
            explainer = shap.TreeExplainer(self.model)
            shap_vals = explainer.shap_values(df)
            
            feature_impacts = [(self.feature_names[i], shap_vals[0][i]) for i in range(len(self.feature_names))]
            feature_impacts.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for name, impact in feature_impacts[:3]:
                direction_txt = "increases" if impact > 0 else "decreases"
                top_factors.append(f"{name} ({direction_txt} risk)")
                
                top_factors_details.append(FactorDetail(
                    feature=name,
                    direction="increases_risk" if impact > 0 else "decreases_risk",
                    importance=round(abs(float(impact)), 4)
                ))
        except Exception:
            top_factors = ["SHAP explanation unavailable"]
            
        return PredictionResponse(
            risk_probability=round(probability, 4),
            revenue_at_risk_prediction=prediction,
            risk_level=risk_level,
            top_factors=top_factors,
            top_factors_details=top_factors_details
        )

try:
    predictor_service = RiskPredictor()
except Exception as e:
    print(f"Warning/Error loading model: {e}")
    predictor_service = None
