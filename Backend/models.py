from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, index=True)
    amount = Column(Float)
    payment_status = Column(String)
    payment_method = Column(String)
    failure_reason = Column(String)
    retry_count = Column(Integer, default=0)
    customer_segment = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True) 
    action = Column(String)
    reason = Column(String)
    result = Column(String)
    
    # Phase 8 Extended Audit Fields
    risk_probability = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    detected_problem = Column(String, nullable=True)
    selected_action = Column(String, nullable=True)
    reason_for_action = Column(String, nullable=True)
    previous_attempt_count = Column(Integer, nullable=True)
    new_attempt_count = Column(Integer, nullable=True)
    action_status = Column(String, nullable=True)
    estimated_amount_recoverable = Column(Float, nullable=True)
    recovered_amount = Column(Float, nullable=True)
    failure_reason = Column(String, nullable=True)
    stopping_rule_result = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
