import os
import numpy as np
import pandas as pd
from datetime import datetime
import time
from typing import Dict, Any, List, Tuple, Optional
import joblib
import json

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from app.core.logging import get_logger
from app.ml.enhanced_features import extract_enhanced_features, calculate_risk_score
from app.core.config import settings

logger = get_logger("ensemble_model")

class FraudEnsembleModel:
    """Simplified anomaly detection model for extreme imbalance scenarios"""
    
    def __init__(self, model_path: str = None):
        # Initialize model components
        self.anomaly_model = None
        self.scaler = None
        self.feature_names = None
        self.anomaly_threshold = 0.4  # Default threshold
        
        # Load model if path provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            logger.warning(f"Model path {model_path} not found. Running with default settings.")
    
    def load_model(self, model_path: str) -> bool:
        """Load trained model from file"""
        try:
            # Load model artifacts
            model_data = joblib.load(model_path)
            
            # Load model components
            self.anomaly_model = model_data.get("anomaly_model")
            self.scaler = model_data.get("scaler")
            self.feature_names = model_data.get("feature_names")
            self.anomaly_threshold = model_data.get("anomaly_threshold", 0.4)
            
            logger.info(f"Model loaded successfully from {model_path}")
            logger.info(f"Model features: {self.feature_names}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    async def predict(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud using anomaly detection and rule-based scoring"""
        try:
            # Add basic error handling
            if not transaction.get("transaction_id"):
                transaction["transaction_id"] = f"UNKNOWN_{time.time()}"
            
            # Extract features
            features = extract_enhanced_features(transaction)
            
            # Calculate rule-based risk score
            risk_score = calculate_risk_score(features)
            
            # Default values if no model is available
            is_fraud = False
            fraud_reason = ""
            anomaly_score = 0.0
            
            # 1. Check explicit rule patterns first
            amount = features.get("transaction_amount", 0)
            
            # Rule 1: High-value night transactions
            if features.get("is_night", 0) == 1 and amount > 100000:
                is_fraud = True
                fraud_reason = "High-value transaction during night hours"
            
            # Rule 2: UPI without mobile verification
            elif features.get("upi_no_mobile", 0) == 1 and amount > 20000:
                is_fraud = True
                fraud_reason = "UPI transaction without mobile verification"
            
            # Rule 3: Very large round amounts
            elif features.get("is_round_amount", 0) == 1 and amount > 200000:
                is_fraud = True
                fraud_reason = "Very large round amount transaction"
            
            # Rule 4: Uncommon payment mode without verification
            elif features.get("uncommon_payment_mode", 0) == 1 and features.get("has_mobile", 0) == 0:
                is_fraud = True
                fraud_reason = "Unusual payment mode without verified mobile"
            
            # 2. Use anomaly detection as backup if available
            elif self.anomaly_model is not None and self.feature_names:
                # Convert features to model input format
                X = np.array([[features.get(f, 0) for f in self.feature_names]])
                
                # Scale features if scaler is available
                if self.scaler:
                    X = self.scaler.transform(X)
                
                # Get anomaly score
                raw_score = self.anomaly_model.decision_function(X)[0]
                # Convert to 0-1 range (higher is more anomalous)
                anomaly_score = 1 - ((raw_score + 1) / 2)
                
                # Check if anomalous
                if anomaly_score > self.anomaly_threshold:
                    is_fraud = True
                    fraud_reason = "Unusual transaction pattern detected by anomaly detection"
            
            # 3. Use risk score as final backup
            elif risk_score > 0.7:
                is_fraud = True
                fraud_reason = "Multiple risk factors identified"
            
            # Set fraud score - use max of risk and anomaly scores
            fraud_score = max(risk_score, anomaly_score)
            
            # Return result
            return {
                "is_fraud": is_fraud,
                "fraud_score": float(fraud_score),
                "fraud_reason": fraud_reason,
                "fraud_source": "rule" if fraud_reason and "pattern" not in fraud_reason else "model",
                "feature_contributions": {}
            }
        
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return {
                "is_fraud": False, 
                "fraud_score": 0.0,
                "fraud_reason": f"Error during prediction: {str(e)}",
                "fraud_source": "error",
                "feature_contributions": {}
            }
    
    def train(self, data_path: str, test_size: float = 0.2, random_state: int = 42, save_path: str = None):
        """Train a simplified anomaly detection model focused on normal transactions"""
        try:
            # Load data
            logger.info(f"Loading data from {data_path}")
            df = pd.read_csv(data_path)
            
            logger.info(f"Dataset shape: {df.shape}")
            logger.info(f"Fraud instances: {df['is_fraud'].sum()}")
            
            # 1. Basic preprocessing
            df = df.copy()
            
            # Handle missing values in key fields
            df["transaction_amount"] = df["transaction_amount"].fillna(df["transaction_amount"].median())
            
            # 2. Feature extraction
            # Convert date to datetime and extract time features
            if "transaction_date" in df.columns:
                df["transaction_date"] = pd.to_datetime(df["transaction_date"])
                df["hour"] = df["transaction_date"].dt.hour
                df["is_night"] = ((df["hour"] < 5) | (df["hour"] >= 23)).astype(int)
                df["is_weekend"] = df["transaction_date"].dt.dayofweek.isin([5, 6]).astype(int)
            
            # Verification features
            df["has_mobile"] = df["payer_mobile_anonymous"].notna().astype(int)
            df["has_email"] = df["payer_email_anonymous"].notna().astype(int)
            
            # Amount features
            if "transaction_amount" in df.columns:
                df["is_round_amount"] = (
                    (df["transaction_amount"] % 1000 == 0) | 
                    (df["transaction_amount"] % 5000 == 0) | 
                    (df["transaction_amount"] % 10000 == 0)
                ).astype(int)
                df["is_high_value"] = (df["transaction_amount"] > 100000).astype(int)
            
            # Payment mode features
            if "transaction_payment_mode_anonymous" in df.columns:
                df["is_upi"] = (df["transaction_payment_mode_anonymous"] == 11).astype(int)
                df["uncommon_payment_mode"] = df["transaction_payment_mode_anonymous"].isin([4, 5, 9]).astype(int)
            
            # Feature interactions
            df["upi_no_mobile"] = df["is_upi"] * (1 - df["has_mobile"])
            df["high_value_night"] = df["is_high_value"] * df["is_night"]
            
            # 3. Select features
            # Use simplified feature set
            selected_features = [
                "transaction_amount", "hour", "is_night", "is_weekend", 
                "has_mobile", "has_email", "is_round_amount", "is_high_value",
                "is_upi", "uncommon_payment_mode", "upi_no_mobile", "high_value_night"
            ]
            
            # Keep only features present in the dataset
            feature_cols = [f for f in selected_features if f in df.columns]
            logger.info(f"Selected features: {feature_cols}")
            
            # 4. Use only legitimate transactions to train anomaly detector
            normal_idx = np.where(df["is_fraud"] == 0)[0]
            X_normal = df[feature_cols].iloc[normal_idx].values
            
            # 5. Get fraud transactions for evaluation
            fraud_idx = np.where(df["is_fraud"] == 1)[0]
            X_fraud = df[feature_cols].iloc[fraud_idx].values if len(fraud_idx) > 0 else None
            
            # 6. Standardize features
            scaler = StandardScaler()
            X_normal_scaled = scaler.fit_transform(X_normal)
            X_fraud_scaled = scaler.transform(X_fraud) if X_fraud is not None else None
            
            # 7. Train anomaly detection model
            logger.info("Training Isolation Forest model")
            anomaly_model = IsolationForest(
                n_estimators=300,
                max_samples="auto",
                contamination=0.005,  # Expect 0.5% of transactions to be anomalous
                max_features=1.0,
                bootstrap=True,
                n_jobs=-1,
                random_state=random_state
            )
            
            anomaly_model.fit(X_normal_scaled)
            
            # 8. Find optimal threshold using fraud examples
            best_threshold = 0.4  # Default
            
            if X_fraud is not None and len(X_fraud) > 0:
                # Get anomaly scores
                normal_scores = anomaly_model.decision_function(X_normal_scaled)
                fraud_scores = anomaly_model.decision_function(X_fraud_scaled)
                
                # Convert to 0-1 range (higher is more anomalous)
                normal_scores_norm = 1 - ((normal_scores + 1) / 2)
                fraud_scores_norm = 1 - ((fraud_scores + 1) / 2)
                
                logger.info(f"Anomaly scores - non-fraud mean: {normal_scores_norm.mean()}, fraud mean: {fraud_scores_norm.mean()}")
                
                # Choose threshold slightly below fraud mean score
                best_threshold = max(0.38, fraud_scores_norm.mean() * 0.9)
                logger.info(f"Setting anomaly threshold to: {best_threshold}")
            
            # 9. Evaluate on held-out sample
            # Use a small sample to evaluate false positive rate
            sample_size = min(10000, len(normal_idx))
            sample_idx = np.random.choice(normal_idx, size=sample_size, replace=False)
            X_sample = df[feature_cols].iloc[sample_idx].values
            X_sample_scaled = scaler.transform(X_sample)
            
            # Get anomaly scores
            sample_scores = anomaly_model.decision_function(X_sample_scaled)
            sample_scores_norm = 1 - ((sample_scores + 1) / 2)
            
            # Calculate false positive rate
            false_positives = (sample_scores_norm > best_threshold).sum()
            false_positive_rate = false_positives / sample_size
            
            logger.info(f"False positive rate at threshold {best_threshold}: {false_positive_rate:.4f}")
            
            # 10. Save model
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                model_data = {
                    "anomaly_model": anomaly_model,
                    "scaler": scaler,
                    "feature_names": feature_cols,
                    "anomaly_threshold": best_threshold,
                    "training_date": datetime.now().isoformat(),
                    "metrics": {
                        "false_positive_rate": false_positive_rate,
                        "normal_mean_score": normal_scores_norm.mean(),
                        "fraud_mean_score": fraud_scores_norm.mean() if X_fraud is not None else None
                    }
                }
                
                joblib.dump(model_data, save_path)
                logger.info(f"Model saved to {save_path}")
                
                # Update instance properties
                self.anomaly_model = anomaly_model
                self.scaler = scaler
                self.feature_names = feature_cols
                self.anomaly_threshold = best_threshold
            
            # Return training results
            result = {
                "metrics": {
                    "false_positive_rate": false_positive_rate,
                    "threshold": best_threshold
                },
                "model_info": {
                    "type": "Isolation Forest Anomaly Detection",
                    "feature_count": len(feature_cols)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise