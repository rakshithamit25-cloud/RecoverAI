import json

# Test script to prove ML scoring consistency across endpoints
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def run_tests():
    payload = {
      "transaction_id": "test_auth_fail_1",
      "amount": 5500.25,
      "payment_method": "net_banking",
      "customer_segment": "loyal",
      "transaction_hour": 9,
      "days_since_last_payment": 5,
      "previous_failures": 0,
      "retry_count": 0,
      "checkout_duration": 18,
      "device_type": "desktop",
      "location_type": "domestic",
      "payment_gateway": "razorpay",
      "failure_reason": "authentication_failed",
      "subscription_status": "none",
      "invoice_age_days": 2,
      "amount_due": 5500.25,
      "payment_status": "failed"
    }

    print("--- Running Consistency Tests ---")
    
    # 1. Test /predict-risk
    res_predict = client.post("/predict-risk", json=payload).json()
    prob_predict = res_predict["risk_probability"]
    print(f"[OK] /predict-risk ML Score: {prob_predict}")
    
    # 2. Test /agent/decision
    res_agent = client.post("/agent/decision", json=payload).json()
    prob_agent = res_agent["risk_probability"]
    txn_id_agent = res_agent["transaction_id"]
    
    print(f"[OK] /agent/decision ML Score: {prob_agent}")
    print(f"[OK] /agent/decision Transaction ID parsed: '{txn_id_agent}'")
    
    # 3. Asserts
    assert prob_predict == prob_agent, f"MISMATCH: Predict returned {prob_predict}, Agent returned {prob_agent}"
    print("[PASS] Both endpoints use identical ML pipelines and preprocessing.")
    
    assert txn_id_agent == "test_auth_fail_1", f"MISMATCH: Transaction ID lost. Found {txn_id_agent}"
    print("[PASS] Transaction ID is correctly preserved through structured pipeline.")

if __name__ == "__main__":
    run_tests()
