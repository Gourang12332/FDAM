from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.models import Transaction, FraudData

logger = get_logger("fraud_reporting")

class FraudReportingService:
    """Service for handling fraud reports"""
    
    @staticmethod
    async def report_fraud(
        db: AsyncSession,
        transaction_id: str,
        reporting_entity_id: str,
        fraud_details: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process and store a fraud report"""
        try:
            # Check if transaction exists
            result = await db.execute(
                select(Transaction).where(Transaction.transaction_id == transaction_id)
            )
            transaction = result.scalars().first()
            
            if not transaction:
                logger.warning(f"Attempted to report fraud for non-existent transaction: {transaction_id}")
                return {
                    "transaction_id": transaction_id,
                    "reporting_acknowledged": False,
                    "failure_code": 404  # Transaction not found
                }
            
            # Check if fraud data exists for this transaction
            result = await db.execute(
                select(FraudData).where(FraudData.transaction_id == transaction_id)
            )
            fraud_data = result.scalars().first()
            
            if fraud_data:
                # Update existing record
                fraud_data.is_fraud_reported = True
                fraud_data.reporting_entity_id = reporting_entity_id
                fraud_data.fraud_details = fraud_details
                fraud_data.reported_at = datetime.now()
            else:
                # Create new fraud data record
                new_fraud_data = FraudData(
                    transaction_id=transaction_id,
                    is_fraud_reported=True,
                    reporting_entity_id=reporting_entity_id,
                    fraud_details=fraud_details,
                    reported_at=datetime.now()
                )
                db.add(new_fraud_data)
            
            await db.commit()
            
            return {
                "transaction_id": transaction_id,
                "reporting_acknowledged": True,
                "failure_code": None
            }
                
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing fraud report: {e}")
            
            return {
                "transaction_id": transaction_id,
                "reporting_acknowledged": False,
                "failure_code": 500  # Internal server error
            }