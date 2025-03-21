from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import time
import asyncio
from app.db.database import get_async_session
from app.schemas import (
    TransactionCreate, FraudDetectionResponse, BatchDetectionRequest, 
    BatchDetectionResponse, FraudReportRequest, FraudReportResponse,
    RuleCreate, RuleUpdate, RuleResponse
)
from app.models import Rule
from app.services.detection import FraudDetectionService
from app.services.reporting import FraudReportingService
from app.services.analytics import DashboardService
from app.services.rules import RuleEngine
from app.core.logging import get_logger

logger = get_logger("api")

# Create API router
api_router = APIRouter()

# Fraud Detection Endpoints
@api_router.post("/fraud-detection/detect", response_model=FraudDetectionResponse, tags=["fraud-detection"])
async def detect_fraud(
    transaction: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Detect fraud for a single transaction in real-time.
    Results are stored in the database for analytics and reporting.
    """
    start_time = time.time()
    
    try:
        result = await FraudDetectionService.detect_fraud(
            transaction=transaction.model_dump(),
            db=db,
            store_result=True
        )
        
        # Log latency for monitoring
        latency = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"Fraud detection completed in {latency:.2f}ms for {transaction.transaction_id}")
        
        if latency > 300:
            logger.warning(f"High latency ({latency:.2f}ms) for fraud detection on {transaction.transaction_id}")
        
        return result
        
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        logger.error(f"Error in fraud detection API ({latency:.2f}ms): {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during fraud detection"
        )

@api_router.post("/fraud-detection/detect-batch", response_model=BatchDetectionResponse, tags=["fraud-detection"])
async def detect_fraud_batch(
    request: BatchDetectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Process multiple transactions in parallel for fraud detection.
    """
    start_time = time.time()
    
    try:
        results = {}
        
        # Process transactions in parallel
        async def process_transaction(tx_data):
            tx_id = tx_data.get("transaction_id")
            if not tx_id:
                logger.warning(f"Transaction missing ID: {tx_data}")
                return
                
            try:
                result = await FraudDetectionService.detect_fraud(
                    transaction=tx_data,
                    db=db,
                    store_result=True
                )
                results[tx_id] = result
            except Exception as e:
                logger.error(f"Error processing transaction {tx_id}: {e}")
                results[tx_id] = {
                    "transaction_id": tx_id,
                    "is_fraud": False,
                    "fraud_source": "error",
                    "fraud_reason": f"Processing error: {str(e)}",
                    "fraud_score": 0.0
                }
        
        # Create tasks for all transactions with bounded concurrency
        semaphore = asyncio.Semaphore(10)  # Process up to 10 transactions concurrently
        
        async def bounded_process(tx):
            async with semaphore:
                await process_transaction(tx)
        
        await asyncio.gather(*[bounded_process(tx) for tx in request.transactions])
        
        # Calculate and log metrics
        latency = (time.time() - start_time) * 1000
        tx_count = len(request.transactions)
        avg_latency = latency / tx_count if tx_count > 0 else 0
        
        logger.info(f"Batch detection completed: {tx_count} transactions in {latency:.2f}ms (avg: {avg_latency:.2f}ms)")
        
        return BatchDetectionResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error in batch detection API: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during batch fraud detection"
        )

# Fraud Reporting Endpoints
@api_router.post("/fraud-reporting/report", response_model=FraudReportResponse, tags=["fraud-reporting"])
async def report_fraud(
    report: FraudReportRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Report a transaction as fraudulent.
    This is used for actual fraud reports from users or other systems.
    """
    try:
        result = await FraudReportingService.report_fraud(
            db=db,
            transaction_id=report.transaction_id,
            reporting_entity_id=report.reporting_entity_id,
            fraud_details=report.fraud_details
        )
        
        if result["reporting_acknowledged"]:
            logger.info(f"Fraud report submitted for transaction {report.transaction_id}")
        else:
            logger.warning(f"Fraud report failed for transaction {report.transaction_id}: {result.get('failure_code')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in fraud reporting API: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during fraud reporting"
        )

# Rules Endpoints
@api_router.get("/rules", response_model=List[RuleResponse], tags=["rules"])
async def get_rules(
    active_only: bool = False,
    db: AsyncSession = Depends(get_async_session)
):
    """Get all fraud detection rules"""
    query = select(Rule)
    if active_only:
        query = query.where(Rule.is_active == True)
    query = query.order_by(Rule.rule_priority.desc())
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return rules

@api_router.post("/rules", response_model=RuleResponse, tags=["rules"])
async def create_rule(
    rule: RuleCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new fraud detection rule"""
    try:
        # Create new rule
        new_rule = Rule(**rule.model_dump())
        db.add(new_rule)
        await db.commit()
        await db.refresh(new_rule)
        
        # Invalidate rules cache
        await RuleEngine.invalidate_rules_cache()
        
        logger.info(f"Created new rule: {rule.rule_name}")
        return new_rule
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating rule: {str(e)}"
        )

@api_router.get("/rules/{rule_id}", response_model=RuleResponse, tags=["rules"])
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific rule by ID"""
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalars().first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule

@api_router.put("/rules/{rule_id}", response_model=RuleResponse, tags=["rules"])
async def update_rule(
    rule_id: int,
    rule_update: RuleUpdate,
    db: AsyncSession = Depends(get_async_session)
):
    """Update an existing rule"""
    try:
        # Get existing rule
        result = await db.execute(select(Rule).where(Rule.id == rule_id))
        rule = result.scalars().first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Update fields
        update_data = rule_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)
        
        await db.commit()
        await db.refresh(rule)
        
        # Invalidate rules cache
        await RuleEngine.invalidate_rules_cache()
        
        logger.info(f"Updated rule {rule_id}: {rule.rule_name}")
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating rule {rule_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating rule: {str(e)}"
        )

@api_router.delete("/rules/{rule_id}", tags=["rules"])
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a rule"""
    try:
        # Get existing rule
        result = await db.execute(select(Rule).where(Rule.id == rule_id))
        rule = result.scalars().first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Delete rule
        await db.delete(rule)
        await db.commit()
        
        # Invalidate rules cache
        await RuleEngine.invalidate_rules_cache()
        
        logger.info(f"Deleted rule {rule_id}")
        return {"message": "Rule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting rule {rule_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting rule: {str(e)}"
        )

# Analytics Endpoints
@api_router.get("/analytics/transactions", tags=["analytics"])
async def get_transactions(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    payer_id: Optional[str] = None,
    payee_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session)
):
    """Get paginated transaction data with filters"""
    try:
        # Parse dates if provided
        from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
        to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None
        
        transactions, total_count = await DashboardService.get_transactions(
            db=db,
            date_from=from_date,
            date_to=to_date,
            payer_id=payer_id,
            payee_id=payee_id,
            transaction_id=transaction_id,
            page=page,
            page_size=page_size
        )
        
        return {
            "data": transactions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching transaction data"
        )

@api_router.get("/analytics/summary", tags=["analytics"])
async def get_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    payer_id: Optional[str] = None,
    payee_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get summary metrics for dashboard"""
    try:
        # Parse dates if provided
        from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
        to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None
        
        summary = await DashboardService.get_summary_metrics(
            db=db,
            date_from=from_date,
            date_to=to_date,
            payer_id=payer_id,
            payee_id=payee_id
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching summary metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching summary metrics"
        )

@api_router.get("/analytics/dimensional", tags=["analytics"])
async def get_dimensional_analysis(
    dimension: str = Query("transaction_channel", enum=["transaction_channel", "transaction_payment_mode", "payment_gateway_bank", "payee_id"]),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get fraud analysis by dimension"""
    try:
        # Parse dates if provided
        from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
        to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None
        
        analysis = await DashboardService.get_dimensional_analysis(
            db=db,
            date_from=from_date,
            date_to=to_date,
            dimension=dimension
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error generating dimensional analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generating dimensional analysis"
        )

@api_router.get("/analytics/timeseries", tags=["analytics"])
async def get_time_series(
    interval: str = Query("day", enum=["hour", "day", "week", "month"]),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get time series analysis of frauds"""
    try:
        # Parse dates if provided
        from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
        to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None
        
        time_series = await DashboardService.get_time_series_analysis(
            db=db,
            date_from=from_date,
            date_to=to_date,
            interval=interval
        )
        
        return time_series
        
    except Exception as e:
        logger.error(f"Error generating time series analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generating time series analysis"
        )

@api_router.get("/analytics/evaluation", tags=["analytics"])
async def get_evaluation_metrics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get model evaluation metrics"""
    try:
        # Parse dates if provided
        from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
        to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None
        
        metrics = await DashboardService.get_evaluation_metrics(
            db=db,
            date_from=from_date,
            date_to=to_date
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating evaluation metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error calculating evaluation metrics"
        )