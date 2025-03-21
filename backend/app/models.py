from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    transaction_amount = Column(Float, nullable=False)
    transaction_channel = Column(String(50))
    transaction_payment_mode = Column(String(50))
    payment_gateway_bank = Column(String(100))
    payer_email = Column(String(255))
    payer_mobile = Column(String(50))
    payer_device = Column(String(255))
    payer_browser = Column(String(255))
    payee_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship with the fraud_data table
    fraud_data = relationship("FraudData", back_populates="transaction", uselist=False)

class FraudData(Base):
    __tablename__ = "fraud_data"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    is_fraud_predicted = Column(Boolean, nullable=True)
    is_fraud_reported = Column(Boolean, nullable=True)
    fraud_source = Column(String(50), nullable=True)
    fraud_reason = Column(Text, nullable=True)
    fraud_score = Column(Float, nullable=True)
    reporting_entity_id = Column(String(255), nullable=True)
    fraud_details = Column(Text, nullable=True)
    model_version = Column(String(100), nullable=True)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=True)
    processed_at = Column(DateTime, default=func.now())
    reported_at = Column(DateTime, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="fraud_data")
    rule = relationship("Rule", back_populates="fraud_detections")

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(255), nullable=False)
    rule_description = Column(Text, nullable=True)
    rule_condition = Column(JSON, nullable=False)
    rule_priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    fraud_detections = relationship("FraudData", back_populates="rule")