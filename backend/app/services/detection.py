from datetime import datetime
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import get_logger
from app.models import Transaction, FraudData
from app.services.rules import RuleEngine
from app.ml.ensemble_model import FraudEnsembleModel

logger = get_logger("fraud_detection")
fraud_model = FraudEnsembleModel(settings.MODEL_PATH)

class FraudDetectionService:
    """Service for fraud detection combining rule engine and ensemble model"""
    
    @staticmethod
    @staticmethod
    async def detect_fraud(
        transaction: Dict[str, Any],
        db: AsyncSession,
        store_result: bool = True
    ) -> Dict[str, Any]:
        """
        Detect fraud for a transaction using both rule engine and model.
        Rule engine takes precedence if it detects fraud.
        """
        try:
            transaction_id = transaction.get("transaction_id")
            
            # Start both rule engine and ML model evaluation concurrently
            rule_task = asyncio.create_task(
                RuleEngine.evaluate_transaction(transaction, db)
            )
            model_task = asyncio.create_task(
                fraud_model.predict(transaction)
            )
            
            # Wait for both tasks to complete
            is_rule_fraud, matched_rule = await rule_task
            model_result = await model_task
            
            # Determine final fraud detection result
            is_fraud = is_rule_fraud or model_result["is_fraud"]
            
            # Set fraud source and reason
            fraud_source = "rule" if is_rule_fraud else model_result["fraud_source"] if model_result["is_fraud"] else ""
            
            if is_rule_fraud and matched_rule:
                fraud_reason = f"Rule: {matched_rule['rule_name']} - {matched_rule['rule_description']}"
                rule_id = matched_rule["id"]
            else:
                fraud_reason = model_result["fraud_reason"]
                rule_id = None
            
            # Get fraud score
            fraud_score = 1.0 if is_rule_fraud else model_result["fraud_score"]
            
            # Prepare result
            result = {
                "transaction_id": transaction_id,
                "is_fraud": is_fraud,
                "fraud_source": fraud_source,
                "fraud_reason": fraud_reason,
                "fraud_score": fraud_score,
                "model_version": settings.MODEL_VERSION if fraud_source == "model" else None,
                "rule_id": rule_id if fraud_source == "rule" else None
            }
            
            # Store result in database if requested
            if store_result:
                try:
                    await FraudDetectionService.store_detection_result(db, transaction, result)
                except Exception as e:
                    logger.error(f"Error storing detection result: {e}")
            
            # Return result without internal details
            api_result = {
                "transaction_id": result["transaction_id"],
                "is_fraud": result["is_fraud"],
                "fraud_source": result["fraud_source"],
                "fraud_reason": result["fraud_reason"],
                "fraud_score": result["fraud_score"]
            }
            
            return api_result
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {e}")
            
            # Return a safe default response in case of errors
            return {
                "transaction_id": transaction.get("transaction_id", "unknown"),
                "is_fraud": False,
                "fraud_source": "error",
                "fraud_reason": "Error in fraud detection system",
                "fraud_score": 0.0
            }
    
    @staticmethod
    async def store_detection_result(
        db: AsyncSession,
        transaction: Dict[str, Any],
        detection_result: Dict[str, Any]
    ) -> None:
        """Store transaction and detection result in database"""
        try:
            # Check if transaction already exists
            result = await db.execute(
                select(Transaction).where(Transaction.transaction_id == transaction["transaction_id"])
            )
            existing_tx = result.scalars().first()
            
            if not existing_tx:
                # Parse date if it's a string
                tx_date = transaction["transaction_date"]
                if isinstance(tx_date, str):
                    tx_date = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))
                
                # Create transaction record
                tx = Transaction(
                    transaction_id=transaction["transaction_id"],
                    transaction_date=tx_date,
                    transaction_amount=float(transaction.get("transaction_amount", 0)),
                    transaction_channel=transaction.get("transaction_channel"),
                    transaction_payment_mode=transaction.get("transaction_payment_mode"),
                    payment_gateway_bank=transaction.get("payment_gateway_bank"),
                    payer_email=transaction.get("payer_email"),
                    payer_mobile=transaction.get("payer_mobile"),
                    payer_device=transaction.get("payer_device"),
                    payer_browser=transaction.get("payer_browser"),
                    payee_id=transaction.get("payee_id", "")
                )
                db.add(tx)
                await db.flush()
            
            # Check if fraud data exists for this transaction
            result = await db.execute(
                select(FraudData).where(FraudData.transaction_id == transaction["transaction_id"])
            )
            existing_fraud = result.scalars().first()
            
            if existing_fraud:
                # Update existing record
                existing_fraud.is_fraud_predicted = detection_result["is_fraud"]
                existing_fraud.fraud_source = detection_result["fraud_source"]
                existing_fraud.fraud_reason = detection_result["fraud_reason"]
                existing_fraud.fraud_score = detection_result["fraud_score"]
                existing_fraud.model_version = detection_result.get("model_version")
                existing_fraud.rule_id = detection_result.get("rule_id")
                existing_fraud.processed_at = datetime.now()
            else:
                # Create new fraud data record
                fraud_data = FraudData(
                    transaction_id=transaction["transaction_id"],
                    is_fraud_predicted=detection_result["is_fraud"],
                    is_fraud_reported=False,
                    fraud_source=detection_result["fraud_source"],
                    fraud_reason=detection_result["fraud_reason"],
                    fraud_score=detection_result["fraud_score"],
                    model_version=detection_result.get("model_version"),
                    rule_id=detection_result.get("rule_id"),
                    processed_at=datetime.now()
                )
                db.add(fraud_data)
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing detection result: {e}")
            raise