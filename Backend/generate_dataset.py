import csv
import random
import os
import uuid
from pathlib import Path

# Fixed random seed for reproducibility
random.seed(42)

NUM_RECORDS = 10000

PAYMENT_METHODS = ["credit_card", "debit_card", "upi", "net_banking", "wallet"]
CUSTOMER_SEGMENTS = ["new", "loyal", "returning", "high_value", "churn_risk"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
LOCATION_TYPES = ["domestic", "international"]
PAYMENT_STATUSES = ["success", "failed", "pending", "abandoned", "overdue"]
FAILURE_REASONS = [
    "insufficient_funds",
    "bank_declined",
    "network_error",
    "authentication_failed",
    "expired_card"
]

def generate_transactions():
    data = []
    
    for i in range(NUM_RECORDS):
        transaction_id = f"txn_{uuid.uuid4().hex[:14]}"
        customer_id = f"cust_{random.randint(1000, 9999)}"
        amount = round(random.uniform(50.0, 50000.0), 2)
        payment_method = random.choice(PAYMENT_METHODS)
        customer_segment = random.choice(CUSTOMER_SEGMENTS)
        transaction_hour = random.randint(0, 23)
        days_since_last_payment = random.randint(0, 180)
        previous_failures = random.choices([0, 1, 2, 3, 4, 5], weights=[60, 20, 10, 5, 3, 2])[0]
        checkout_duration = random.randint(10, 600)
        device_type = random.choice(DEVICE_TYPES)
        location_type = random.choices(LOCATION_TYPES, weights=[90, 10])[0]
        payment_gateway = "razorpay"
        subscription_status = random.choice(["active", "inactive", "none"])
        invoice_age_days = random.randint(0, 60)
        amount_due = round(amount if random.random() > 0.3 else amount + random.uniform(10, 500), 2)

        # Baseline payment status assignment based on some probabilities
        status_weights = [60, 20, 5, 10, 5] # success, failed, pending, abandoned, overdue
        
        # Modify weights slightly if they have previous failures or they are churn risk
        if previous_failures > 2 or customer_segment == "churn_risk":
            status_weights = [30, 40, 5, 15, 10]
            
        payment_status = random.choices(PAYMENT_STATUSES, weights=status_weights)[0]

        # Logic for failure reasons
        if payment_status in ["success", "pending"]:
            failure_reason = "None"
            retry_count = 0
        else:
            failure_reason = random.choice(FAILURE_REASONS)
            retry_count = random.randint(1, 3)

        # Revenue at risk logic (1 = at risk, 0 = not at risk)
        revenue_at_risk = 0
        
        # Definition of at risk: Failed, abandoned, or overdue.
        # But if it's abandoned/overdue for a huge amount or they have failures, it's definitively at risk.
        if payment_status in ["failed", "abandoned", "overdue"]:
            # Baseline 70% risk for failed things, but increased with variables
            risk_score = 0.5
            if previous_failures >= 1:
                risk_score += 0.2
            if retry_count >= 2:
                risk_score += 0.2
            if amount > 5000:
                risk_score += 0.1
                
            revenue_at_risk = 1 if random.random() < risk_score else 0

        # Successful payments are never "at risk" of failure for this txn
        if payment_status == "success":
            revenue_at_risk = 0

        data.append({
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "amount": amount,
            "payment_method": payment_method,
            "customer_segment": customer_segment,
            "transaction_hour": transaction_hour,
            "days_since_last_payment": days_since_last_payment,
            "previous_failures": previous_failures,
            "retry_count": retry_count,
            "checkout_duration": checkout_duration,
            "device_type": device_type,
            "location_type": location_type,
            "payment_gateway": payment_gateway,
            "failure_reason": failure_reason,
            "subscription_status": subscription_status,
            "invoice_age_days": invoice_age_days,
            "amount_due": amount_due,
            "payment_status": payment_status,
            "revenue_at_risk": revenue_at_risk
        })

    return data


if __name__ == "__main__":
    print("Generating synthetic transactions...")
    transactions = generate_transactions()
    
    # Ensure dataset directory exists
    dataset_dir = Path(__file__).parent / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    csv_file_path = dataset_dir / "transactions.csv"
    
    # Write to CSV
    fieldnames = transactions[0].keys()
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
        
    # Metrics Calculation
    num_records = len(transactions)
    num_success = sum(1 for t in transactions if t["payment_status"] == "success")
    num_failed = sum(1 for t in transactions if t["payment_status"] == "failed")
    num_at_risk = sum(1 for t in transactions if t["revenue_at_risk"] == 1)
    total_amount = sum(t["amount"] for t in transactions)
    total_risk_amount = sum(t["amount"] for t in transactions if t["revenue_at_risk"] == 1)
    
    print("\n--- Dataset Generation Metrics ---")
    print(f"Total Records Generated: {num_records}")
    print(f"Total Transaction Amount: ₹{total_amount:,.2f}")
    print(f"Successful Transactions: {num_success}")
    print(f"Failed Transactions: {num_failed}")
    print(f"At-Risk Transactions: {num_at_risk}")
    print(f"Total Revenue at Risk: ₹{total_risk_amount:,.2f}")
    print(f"\nDataset successfully saved to: {csv_file_path}")
