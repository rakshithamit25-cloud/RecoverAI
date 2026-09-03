import razorpay
import os
import logging
from dotenv import load_dotenv
import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

def get_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise ValueError("Razorpay Test Mode credentials are not configured in environment variables.")
        
    if not str(RAZORPAY_KEY_ID).startswith("rzp_test_"):
        logger.warning("WARNING: RAZORPAY_KEY_ID does not start with 'rzp_test_'. Ensure you are using TEST MODE credentials!")
        
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def fetch_payment_details(payment_id: str):
    client = get_client()
    return client.payment.fetch(payment_id)

def fetch_order_details(order_id: str):
    client = get_client()
    return client.order.fetch(order_id)

def list_payments(count: int = 10, skip: int = 0):
    client = get_client()
    return client.payment.all({"count": count, "skip": skip})

def list_orders(count: int = 10, skip: int = 0):
    client = get_client()
    return client.order.all({"count": count, "skip": skip})

def normalize_payment_for_ml(payment_data: dict) -> dict:
    """
    Normalizes raw Razorpay payment dictionary into the ML feature format.
    Fields missing in Razorpay must be provided from our DB history.
    """
    # Razorpay returns amounts in basic denomination (e.g. paise for INR). We divide by 100.
    amount = float(payment_data.get("amount", 0)) / 100.0  
    
    payment_method = payment_data.get("method", "card")
    status = payment_data.get("status", "unknown")
    failure_reason = payment_data.get("error_reason", "None") or "None"
    
    # Map explicit Razorpay methods to our ML expected categorical labels
    if payment_method == "card":
        payment_method = "credit_card"  
    elif payment_method == "netbanking":
        payment_method = "net_banking"
    
    # Derive hour from created_at
    created_ts = payment_data.get("created_at")
    transaction_hour = 12
    if created_ts:
        dt = datetime.datetime.fromtimestamp(created_ts)
        transaction_hour = dt.hour
        
    normalized = {
        "amount": amount,
        "payment_method": payment_method,
        "transaction_hour": transaction_hour,
        "payment_status": status,
        "failure_reason": failure_reason,
        "payment_gateway": "razorpay",
        
        # --- FIELDS REQUIRING DB LOOKUP (Filled with generic defaults for now) ---
        "customer_segment": "new",                  
        "days_since_last_payment": 0,               
        "previous_failures": 0,                     
        "retry_count": 0,                           
        "checkout_duration": 60,                    
        "device_type": "mobile",                   
        "location_type": "domestic",                
        "subscription_status": "none",              
        "invoice_age_days": 1,                      
        "amount_due": amount                        
    }
    
    return normalized
