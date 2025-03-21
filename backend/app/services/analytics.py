from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, func, and_, or_, cast, Float, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.core.logging import get_logger
from app.models import Transaction, FraudData
from app.core.config import settings

logger = get_logger("analytics")

class DashboardService:
    """Service for analytics and dashboard data"""
    
    @staticmethod
    async def get_transactions(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        payer_id: Optional[str] = None,
        payee_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get transactions with pagination and filtering"""
        try:
            # Build query with joins
            query = (
                select(Transaction, FraudData)
                .outerjoin(FraudData, Transaction.transaction_id == FraudData.transaction_id)
            )
            
            # Apply filters
            if date_from:
                query = query.where(Transaction.transaction_date >= date_from)
            if date_to:
                query = query.where(Transaction.transaction_date <= date_to)
            if payer_id:
                query = query.where(Transaction.payer_email.like(f"%{payer_id}%"))
            if payee_id:
                query = query.where(Transaction.payee_id == payee_id)
            if transaction_id:
                query = query.where(Transaction.transaction_id.like(f"%{transaction_id}%"))
            
            # Get total count (without pagination)
            count_query = select(func.count()).select_from(query.subquery())
            result = await db.execute(count_query)
            total_count = result.scalar()
            
            # Apply pagination
            query = (
                query
                .order_by(Transaction.transaction_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            
            # Execute query
            result = await db.execute(query)
            rows = result.all()
            
            # Format results
            transactions = []
            for transaction, fraud_data in rows:
                tx_dict = {
                    "transaction_id": transaction.transaction_id,
                    "transaction_date": transaction.transaction_date.isoformat(),
                    "transaction_amount": transaction.transaction_amount,
                    "transaction_channel": transaction.transaction_channel,
                    "transaction_payment_mode": transaction.transaction_payment_mode,
                    "payment_gateway_bank": transaction.payment_gateway_bank,
                    "payer_email": transaction.payer_email,
                    "payer_mobile": transaction.payer_mobile,
                    "payer_device": transaction.payer_device,
                    "payer_browser": transaction.payer_browser,
                    "payee_id": transaction.payee_id,
                    "is_fraud_predicted": fraud_data.is_fraud_predicted if fraud_data else None,
                    "is_fraud_reported": fraud_data.is_fraud_reported if fraud_data else None,
                    "fraud_score": fraud_data.fraud_score if fraud_data else None,
                    "fraud_source": fraud_data.fraud_source if fraud_data else None,
                    "fraud_reason": fraud_data.fraud_reason if fraud_data else None
                }
                transactions.append(tx_dict)
            
            return transactions, total_count
                
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            raise
    
    @staticmethod
    async def get_summary_metrics(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        payer_id: Optional[str] = None,
        payee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        try:
            # Build base query conditions
            conditions = []
            if date_from:
                conditions.append(Transaction.transaction_date >= date_from)
            if date_to:
                conditions.append(Transaction.transaction_date <= date_to)
            if payer_id:
                conditions.append(Transaction.payer_email.like(f"%{payer_id}%"))
            if payee_id:
                conditions.append(Transaction.payee_id == payee_id)
            
            # Total transactions
            query = select(func.count()).select_from(Transaction)
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            total_transactions = result.scalar() or 0
            
            # Total transaction amount
            query = select(func.sum(Transaction.transaction_amount)).select_from(Transaction)
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            total_amount = result.scalar() or 0
            
            # Predicted frauds
            query = (
                select(func.count())
                .select_from(Transaction)
                .join(FraudData, Transaction.transaction_id == FraudData.transaction_id)
                .where(FraudData.is_fraud_predicted == True)
            )
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            predicted_frauds = result.scalar() or 0
            
            # Reported frauds
            query = (
                select(func.count())
                .select_from(Transaction)
                .join(FraudData, Transaction.transaction_id == FraudData.transaction_id)
                .where(FraudData.is_fraud_reported == True)
            )
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            reported_frauds = result.scalar() or 0
            
            # False positives (predicted but not reported)
            query = (
                select(func.count())
                .select_from(Transaction)
                .join(FraudData, Transaction.transaction_id == FraudData.transaction_id)
                .where(
                    and_(
                        FraudData.is_fraud_predicted == True,
                        or_(
                            FraudData.is_fraud_reported == False,
                            FraudData.is_fraud_reported == None
                        )
                    )
                )
            )
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            false_positives = result.scalar() or 0
            
            # False negatives (not predicted but reported)
            query = (
                select(func.count())
                .select_from(Transaction)
                .join(FraudData, Transaction.transaction_id == FraudData.transaction_id)
                .where(
                    and_(
                        or_(
                            FraudData.is_fraud_predicted == False,
                            FraudData.is_fraud_predicted == None
                        ),
                        FraudData.is_fraud_reported == True
                    )
                )
            )
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            false_negatives = result.scalar() or 0
            
            # Calculate metrics
            avg_transaction = total_amount / total_transactions if total_transactions > 0 else 0
            fraud_rate = predicted_frauds / total_transactions * 100 if total_transactions > 0 else 0
            
            precision = (predicted_frauds - false_positives) / predicted_frauds * 100 if predicted_frauds > 0 else 0
            recall = (reported_frauds - false_negatives) / reported_frauds * 100 if reported_frauds > 0 else 0
            
            return {
                "total_transactions": total_transactions,
                "total_amount": total_amount,
                "avg_transaction": avg_transaction,
                "predicted_frauds": predicted_frauds,
                "reported_frauds": reported_frauds,
                "fraud_rate": fraud_rate,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "precision": precision,
                "recall": recall
            }
                
        except Exception as e:
            logger.error(f"Error calculating summary metrics: {e}")
            raise
    
    @staticmethod
    async def get_dimensional_analysis(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        dimension: str = "transaction_channel"
    ) -> List[Dict[str, Any]]:
        """Get fraud analysis by dimension (channel, payment_mode, etc.)"""
        try:
            # Validate dimension
            valid_dimensions = [
                "transaction_channel", "transaction_payment_mode", 
                "payment_gateway_bank", "payee_id"
            ]
            
            if dimension not in valid_dimensions:
                dimension = "transaction_channel"
            
            # Build query conditions
            conditions = []
            if date_from:
                conditions.append(Transaction.transaction_date >= date_from)
            if date_to:
                conditions.append(Transaction.transaction_date <= date_to)
            
            # Dynamic dimension column
            dimension_col = getattr(Transaction, dimension)
            
            # Query for dimensional analysis
            query = (
                select(
                    dimension_col,
                    func.count().label("total_transactions"),
                    func.sum(cast(FraudData.is_fraud_predicted == True, Float)).label("predicted_frauds"),
                    func.sum(cast(FraudData.is_fraud_reported == True, Float)).label("reported_frauds")
                )
                .select_from(Transaction)
                .outerjoin(FraudData, Transaction.transaction_id == FraudData.transaction_id)
                .group_by(dimension_col)
                .order_by(desc("total_transactions"))
            )
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Execute query
            result = await db.execute(query)
            rows = result.all()
            
            # Format results
            analysis = []
            for row in rows:
                if row[0] is None:  # Skip null dimension values
                    continue
                    
                analysis.append({
                    "dimension": dimension,
                    "value": str(row[0]),
                    "total_transactions": row[1],
                    "predicted_frauds": int(row[2] or 0),
                    "reported_frauds": int(row[3] or 0),
                    "fraud_rate": (row[2] or 0) / row[1] * 100 if row[1] > 0 else 0
                })
            
            return analysis
                
        except Exception as e:
            logger.error(f"Error generating dimensional analysis: {e}")
            raise
    
    @staticmethod
    async def get_time_series_analysis(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        interval: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get time series analysis of frauds"""
        try:
            # Set default date range if not provided
            if not date_from:
                date_from = datetime.now() - timedelta(days=30)
            if not date_to:
                date_to = datetime.now()
            
            # Determine date trunc function based on interval
            if interval == "hour":
                date_part = "hour"
            elif interval == "week":
                date_part = "week"
            elif interval == "month":
                date_part = "month"
            else:
                date_part = "day"  # default
            
            # Create query based on database type
            if "sqlite" in settings.SQLALCHEMY_DATABASE_URI:
                # SQLite query using strftime
                if date_part == "day":
                    format_str = "%Y-%m-%d"
                elif date_part == "hour":
                    format_str = "%Y-%m-%d %H:00:00"
                elif date_part == "week":
                    format_str = "%Y-%W"
                elif date_part == "month":
                    format_str = "%Y-%m"
                
                query = text(f"""
                    SELECT 
                        strftime('{format_str}', transaction_date) as time_period,
                        COUNT(t.id) as total_transactions,
                        SUM(CASE WHEN f.is_fraud_predicted = 1 THEN 1 ELSE 0 END) as predicted_frauds,
                        SUM(CASE WHEN f.is_fraud_reported = 1 THEN 1 ELSE 0 END) as reported_frauds
                    FROM transactions t
                    LEFT JOIN fraud_data f ON t.transaction_id = f.transaction_id
                    WHERE t.transaction_date BETWEEN :date_from AND :date_to
                    GROUP BY time_period
                    ORDER BY time_period
                """)
            else:
                # PostgreSQL query using date_trunc
                query = text(f"""
                    SELECT 
                        date_trunc('{date_part}', transaction_date) as time_period,
                        COUNT(t.id) as total_transactions,
                        SUM(CASE WHEN f.is_fraud_predicted = true THEN 1 ELSE 0 END) as predicted_frauds,
                        SUM(CASE WHEN f.is_fraud_reported = true THEN 1 ELSE 0 END) as reported_frauds
                    FROM transactions t
                    LEFT JOIN fraud_data f ON t.transaction_id = f.transaction_id
                    WHERE t.transaction_date BETWEEN :date_from AND :date_to
                    GROUP BY time_period
                    ORDER BY time_period
                """)
            
            # Execute query
            result = await db.execute(
                query, 
                {"date_from": date_from, "date_to": date_to}
            )
            
            rows = result.all()
            
            # Format results
            time_series = []
            for row in rows:
                time_period, total_tx, predicted, reported = row
                
                # Format the time period
                if isinstance(time_period, str):
                    # SQLite returns string
                    formatted_period = time_period
                else:
                    # PostgreSQL returns datetime
                    formatted_period = time_period.isoformat()
                
                time_series.append({
                    "time_period": formatted_period,
                    "interval": interval,
                    "total_transactions": total_tx,
                    "predicted_frauds": int(predicted or 0),
                    "reported_frauds": int(reported or 0),
                    "fraud_rate": (predicted or 0) / total_tx * 100 if total_tx > 0 else 0
                })
            
            return time_series
                
        except Exception as e:
            logger.error(f"Error generating time series analysis: {e}")
            raise
    
    @staticmethod
    async def get_evaluation_metrics(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get model evaluation metrics based on predicted vs reported frauds"""
        try:
            # Set default date range if not provided
            if not date_from:
                date_from = datetime.now() - timedelta(days=30)
            if not date_to:
                date_to = datetime.now()
            
            # Query for counts needed for confusion matrix
            query = text("""
                SELECT
                    SUM(CASE 
                        WHEN (is_fraud_predicted = 0 OR is_fraud_predicted IS NULL) 
                             AND (is_fraud_reported = 0 OR is_fraud_reported IS NULL) 
                        THEN 1 ELSE 0 END) as true_negatives,
                    SUM(CASE 
                        WHEN is_fraud_predicted = 1 
                             AND (is_fraud_reported = 0 OR is_fraud_reported IS NULL) 
                        THEN 1 ELSE 0 END) as false_positives,
                    SUM(CASE 
                        WHEN (is_fraud_predicted = 0 OR is_fraud_predicted IS NULL) 
                             AND is_fraud_reported = 1 
                        THEN 1 ELSE 0 END) as false_negatives,
                    SUM(CASE 
                        WHEN is_fraud_predicted = 1 
                             AND is_fraud_reported = 1 
                        THEN 1 ELSE 0 END) as true_positives
                FROM fraud_data f
                JOIN transactions t ON f.transaction_id = t.transaction_id
                WHERE t.transaction_date BETWEEN :date_from AND :date_to
            """)
            
            result = await db.execute(
                query, 
                {"date_from": date_from, "date_to": date_to}
            )
            
            tn, fp, fn, tp = result.fetchone()
            
            # Handle None values
            tn = int(tn or 0)
            fp = int(fp or 0)
            fn = int(fn or 0)
            tp = int(tp or 0)
            
            # Calculate metrics
            total = tn + fp + fn + tp
            accuracy = (tp + tn) / total if total > 0 else 0
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                "confusion_matrix": {
                    "true_negatives": tn,
                    "false_positives": fp,
                    "false_negatives": fn,
                    "true_positives": tp
                },
                "metrics": {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "specificity": specificity,
                    "f1_score": f1
                },
                "total_evaluated": total,
                "date_range": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat()
                }
            }
                
        except Exception as e:
            logger.error(f"Error calculating evaluation metrics: {e}")
            raise