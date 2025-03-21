import numpy as np
import math
from datetime import datetime
from typing import Dict, Any, List, Optional

def extract_enhanced_features(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Extract optimized features for fraud detection with error handling"""
    features = {}
    
    try:
        # Basic numeric features with error handling
        numeric_fields = [
            "transaction_amount", 
            "transaction_payment_mode_anonymous",
            "payment_gateway_bank_anonymous", 
            "payer_browser_anonymous"
        ]
        
        for field in numeric_fields:
            try:
                if field in transaction and transaction[field] is not None:
                    features[field] = float(transaction[field])
                else:
                    features[field] = 0.0
            except (ValueError, TypeError):
                features[field] = 0.0
        
        # Transaction amount features
        amount = features.get("transaction_amount", 0)
        features["log_amount"] = np.log1p(amount) if amount > 0 else 0
        
        # Round amount detection (common in fraud)
        features["is_round_amount"] = 0
        if amount > 0:
            if amount % 1000 == 0 or amount % 5000 == 0 or amount % 10000 == 0:
                features["is_round_amount"] = 1
        
        # High value transaction markers
        features["is_high_value"] = 1 if amount > 100000 else 0
        features["is_very_high_value"] = 1 if amount > 500000 else 0
        
        # Time-based features with error handling
        if "transaction_date" in transaction:
            try:
                if isinstance(transaction["transaction_date"], str):
                    # Try different date formats
                    try:
                        dt = datetime.fromisoformat(transaction["transaction_date"].replace("Z", "+00:00"))
                    except ValueError:
                        dt = datetime.strptime(transaction["transaction_date"], "%Y-%m-%d %H:%M:%S")
                else:
                    dt = transaction["transaction_date"]
                    
                hour = dt.hour
                features["hour"] = hour
                
                # Time period markers
                features["is_weekend"] = 1 if dt.weekday() >= 5 else 0
                features["is_night"] = 1 if hour < 5 or hour >= 23 else 0
                features["is_business_hours"] = 1 if 9 <= hour <= 17 and dt.weekday() < 5 else 0
                    
            except Exception:
                # Default values if date parsing fails
                features["hour"] = 12
                features["is_weekend"] = 0
                features["is_night"] = 0
                features["is_business_hours"] = 1
        else:
            # Default values if no date provided
            features["hour"] = 12
            features["is_weekend"] = 0
            features["is_night"] = 0
            features["is_business_hours"] = 1
        
        # Channel features
        if "transaction_channel" in transaction:
            channel = str(transaction.get("transaction_channel", "")).lower()
            features["channel_web"] = 1 if channel in ["w", "web"] else 0
            features["channel_mobile"] = 1 if channel in ["m", "mobile"] else 0
        
        # Verification features
        features["has_email"] = 1 if transaction.get("payer_email") or transaction.get("payer_email_anonymous") else 0
        features["has_mobile"] = 1 if transaction.get("payer_mobile") or transaction.get("payer_mobile_anonymous") else 0
        
        # Payment mode features
        payment_mode = features.get("transaction_payment_mode_anonymous", 0)
        features["is_upi"] = 1 if payment_mode == 11 else 0
        features["uncommon_payment_mode"] = 1 if payment_mode in [4, 5, 9] else 0
        
        # Feature interactions
        features["high_value_night"] = features.get("is_high_value", 0) * features.get("is_night", 0)
        features["upi_no_mobile"] = features.get("is_upi", 0) * (1 - features.get("has_mobile", 0))
    
    except Exception as e:
        # Provide default values in case of extraction error
        features = {
            "transaction_amount": 0.0,
            "log_amount": 0.0,
            "is_round_amount": 0,
            "is_high_value": 0,
            "is_very_high_value": 0,
            "hour": 12,
            "is_weekend": 0,
            "is_night": 0,
            "is_business_hours": 1,
            "has_email": 0,
            "has_mobile": 0,
            "is_upi": 0,
            "uncommon_payment_mode": 0,
            "high_value_night": 0,
            "upi_no_mobile": 0
        }
    
    return features

def calculate_risk_score(features: Dict[str, Any]) -> float:
    """Calculate direct risk score based on known fraud patterns"""
    score = 0.0
    
    try:
        # Transaction amount risk
        amount = features.get("transaction_amount", 0)
        if amount > 500000:
            score += 0.4
        elif amount > 100000:
            score += 0.3
        elif amount > 50000:
            score += 0.2
        elif amount > 10000:
            score += 0.1
        
        # Time-based risk
        if features.get("is_night", 0) == 1:
            score += 0.2
            if amount > 20000:
                score += 0.1
        
        # Verification risk
        if features.get("has_mobile", 0) == 0:
            score += 0.2
        
        # Round amount risk
        if features.get("is_round_amount", 0) == 1 and amount > 10000:
            score += 0.2
        
        # Payment mode risk
        if features.get("uncommon_payment_mode", 0) == 1:
            score += 0.2
        
        # UPI without mobile verification
        if features.get("upi_no_mobile", 0) == 1:
            score += 0.4
        
        # Combined risks
        if features.get("high_value_night", 0) == 1:
            score += 0.3
    
    except Exception:
        return 0.0
    
    return min(score, 1.0)