from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Transaction Schemas
class TransactionBase(BaseModel):
    transaction_id: str
    transaction_date: datetime
    transaction_amount: float
    transaction_channel: Optional[str] = None
    transaction_payment_mode: Optional[str] = None
    payment_gateway_bank: Optional[str] = None
    payer_email: Optional[str] = None
    payer_mobile: Optional[str] = None
    payer_device: Optional[str] = None
    payer_browser: Optional[str] = None
    payee_id: str

class TransactionCreate(TransactionBase):
    pass

class TransactionInDB(TransactionBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class TransactionResponse(TransactionBase):
    class Config:
        orm_mode = True

# Fraud Detection Schemas
class FraudDetectionBase(BaseModel):
    transaction_id: str
    is_fraud: bool
    fraud_source: Optional[str] = None
    fraud_reason: Optional[str] = None
    fraud_score: float

class FraudDetectionResponse(FraudDetectionBase):
    pass

class BatchDetectionRequest(BaseModel):
    transactions: List[Dict[str, Any]]

class BatchDetectionResponse(BaseModel):
    results: Dict[str, FraudDetectionResponse]

# Fraud Reporting Schemas
class FraudReportRequest(BaseModel):
    transaction_id: str
    reporting_entity_id: str
    fraud_details: Optional[str] = None

class FraudReportResponse(BaseModel):
    transaction_id: str
    reporting_acknowledged: bool
    failure_code: Optional[int] = None

# Rule Schemas
class RuleBase(BaseModel):
    rule_name: str
    rule_description: Optional[str] = None
    rule_condition: Dict[str, Any]
    rule_priority: int = 0
    is_active: bool = True

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_description: Optional[str] = None
    rule_condition: Optional[Dict[str, Any]] = None
    rule_priority: Optional[int] = None
    is_active: Optional[bool] = None

class RuleInDB(RuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class RuleResponse(RuleInDB):
    class Config:
        orm_mode = True