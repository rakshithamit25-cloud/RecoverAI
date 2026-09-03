from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from database import engine, get_db
import models

from ml.predict import PredictionRequest, PredictionResponse
from ml.predict import predictor_service
import razorpay_service
import recovery_service

from fastapi.middleware.cors import CORSMiddleware

# Note: Since models were just modified, rebuild DB explicitly.
try:
    import os
    if os.path.exists("./recoverai.db"):
        pass # Disabling auto-delete so user's data isn't wiped again
except Exception:
    pass
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RecoverAI",
    description="Razorpay Buildathon 2026 - Track 03: AI Revenue Recovery"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Standard App Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()
    return transactions

@app.post("/predict-risk", response_model=PredictionResponse)
def predict_risk(request: PredictionRequest):
    if predictor_service is None:
        raise HTTPException(status_code=503, detail="ML Model not loaded.")
    try:
        return predictor_service.predict(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

# --- Razorpay Integration Routes ---
rzp_router = APIRouter(prefix="/razorpay", tags=["Razorpay TEST MODE"])

@rzp_router.get("/test-connection")
def test_connection():
    try:
        client = razorpay_service.get_client()
        res = client.payment.all({"count": 1})
        return {"status": "success", "message": "Successfully authenticated with Razorpay Test Mode.", "environment": "TEST"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay API Error: {str(e)}")

@rzp_router.get("/payments")
def get_payments(count: int = 10, skip: int = 0):
    try:
        data = razorpay_service.list_payments(count=count, skip=skip)
        return {"success": True, "items": data.get("items", [])}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay request failed: {str(e)}")

@rzp_router.get("/payment-for-ml/{payment_id}")
def get_payment_for_ml(payment_id: str):
    try:
        payment = razorpay_service.fetch_payment_details(payment_id)
        normalized = razorpay_service.normalize_payment_for_ml(payment)
        return {"success": True, "payment_id": payment_id, "ml_features_prepared": normalized}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch or normalize payment: {str(e)}")

app.include_router(rzp_router)

# --- Phase 8/10: Recovery Agent API ---
recovery_router = APIRouter(prefix="/recovery", tags=["AI Recovery Agent"])

@app.post("/agent/decision")
def get_structured_decision(request: PredictionRequest):
    """Phase 10: Generates the structured, explainable decision JSON output."""
    try:
        return recovery_service.make_agent_decision(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@recovery_router.post("/analyze")
def analyze_transaction(request: PredictionRequest):
    return recovery_service.analyze_risk(request.model_dump())

@recovery_router.post("/execute")
def execute_recovery_action(request: PredictionRequest, db: Session = Depends(get_db)):
    try:
        audit = recovery_service.execute_recovery(request.model_dump(), db)
        return audit
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@recovery_router.get("/audit")
def get_audit_trail(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(100).all()

@recovery_router.get("/metrics")
def get_recovery_metrics(db: Session = Depends(get_db)):
    return recovery_service.get_metrics(db)

@recovery_router.post("/batch")
def run_batch_simulation(limit: int = 50, db: Session = Depends(get_db)):
    """Simulates AI recovery across a chunk of historical failed accounts."""
    return recovery_service.process_batch(db, limit)

app.include_router(recovery_router)
