import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import copy
# Import jsonLogic correctly for your implementation
from jsonlogic_python import jsonLogic
import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import get_logger
from app.models import Rule

logger = get_logger("rule_engine")

class CacheManager:
    """Cache manager that supports file-based or Redis caching"""
    
    def __init__(self):
        self.use_cache = settings.USE_CACHE
        self.cache_type = settings.CACHE_TYPE
        self.redis = None
        
        # Initialize cache based on type
        if self.use_cache:
            if self.cache_type == "redis":
                try:
                    import redis.asyncio as aioredis
                    self.redis = aioredis.from_url(settings.REDIS_URL)
                    logger.info("Redis cache initialized")
                except ImportError:
                    logger.warning("Redis package not installed, falling back to file cache")
                    self.cache_type = "file"
                    os.makedirs(settings.CACHE_DIR, exist_ok=True)
            else:
                os.makedirs(settings.CACHE_DIR, exist_ok=True)
                logger.info(f"File cache initialized at {settings.CACHE_DIR}")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.use_cache:
            return None
            
        if self.cache_type == "redis" and self.redis:
            return await self.redis.get(key)
        else:
            cache_file = os.path.join(settings.CACHE_DIR, f"{key}.json")
            if os.path.exists(cache_file):
                try:
                    async with aiofiles.open(cache_file, 'r') as f:
                        content = await f.read()
                    return content
                except Exception as e:
                    logger.error(f"Error reading from file cache: {e}")
            return None
    
    async def set(self, key: str, value: str, ex: int = 300) -> bool:
        """Set value in cache with expiration in seconds"""
        if not self.use_cache:
            return False
            
        try:
            if self.cache_type == "redis" and self.redis:
                await self.redis.set(key, value, ex=ex)
            else:
                cache_file = os.path.join(settings.CACHE_DIR, f"{key}.json")
                async with aiofiles.open(cache_file, 'w') as f:
                    await f.write(value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate a cache key"""
        if not self.use_cache:
            return True
            
        try:
            if self.cache_type == "redis" and self.redis:
                await self.redis.delete(key)
            else:
                cache_file = os.path.join(settings.CACHE_DIR, f"{key}.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False

# Initialize the cache manager
cache_manager = CacheManager()

class RuleEngine:
    """Rule engine for fraud detection"""
    
    @staticmethod
    async def get_active_rules(db: AsyncSession) -> List[Dict[str, Any]]:
        """Get all active rules from cache or database"""
        # Try to get from cache first
        cached_rules = await cache_manager.get("active_rules")
        if cached_rules:
            try:
                return json.loads(cached_rules)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in cached rules")
        
        # If not in cache or invalid, fetch from DB
        result = await db.execute(
            select(Rule)
            .where(Rule.is_active == True)
            .order_by(Rule.rule_priority.desc())
        )
        rules = result.scalars().all()
        
        # Convert to dict for JSON serialization
        rules_list = []
        for rule in rules:
            rules_list.append({
                "id": rule.id,
                "rule_name": rule.rule_name,
                "rule_description": rule.rule_description,
                "rule_condition": rule.rule_condition,
                "rule_priority": rule.rule_priority
            })
        
        # Cache the rules
        if rules_list:
            await cache_manager.set("active_rules", json.dumps(rules_list))
        
        return rules_list
    
    @staticmethod
    async def evaluate_transaction(
        transaction: Dict[str, Any],
        db: AsyncSession
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Evaluate a transaction against all active rules"""
        rules = await RuleEngine.get_active_rules(db)
        
        # Add derived features for rule evaluation
        enriched_transaction = RuleEngine.enrich_transaction(transaction)
        
        # Evaluate each rule in order of priority
        for rule in rules:
            try:
                # Apply the rule condition to the enriched transaction
                if jsonLogic(rule["rule_condition"], enriched_transaction):
                    return True, rule
            except Exception as e:
                logger.error(f"Error evaluating rule {rule['id']}: {e}")
        
        return False, None
    
    @staticmethod
    def enrich_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Add derived features to transaction for rule evaluation"""
        # Deep copy to avoid modifying the original
        enriched = copy.deepcopy(transaction)
        
        # Ensure has_mobile is set for rule evaluation
        if "payer_mobile" in enriched:
            enriched["has_mobile"] = 1 if enriched["payer_mobile"] else 0
        elif "payer_mobile_anonymous" in enriched:
            enriched["has_mobile"] = 1 if enriched["payer_mobile_anonymous"] else 0
        else:
            enriched["has_mobile"] = 0
            
        # Parse date if it's a string
        if isinstance(enriched.get("transaction_date"), str):
            try:
                date_obj = datetime.fromisoformat(enriched["transaction_date"].replace("Z", "+00:00"))
                enriched["hour_of_day"] = date_obj.hour
                enriched["day_of_week"] = date_obj.weekday()
                enriched["is_weekend"] = 1 if date_obj.weekday() >= 5 else 0
                enriched["is_night"] = 1 if date_obj.hour >= 22 or date_obj.hour <= 6 else 0
            except Exception as e:
                logger.error(f"Error parsing transaction date: {e}")
                # Set default values if date parsing fails
                enriched["hour_of_day"] = 12
                enriched["day_of_week"] = 0
                enriched["is_weekend"] = 0
                enriched["is_night"] = 0
        
        # Round amount features
        if enriched.get("transaction_amount"):
            try:
                # Check if amount is round (e.g., 100.00, 500.00)
                amount = float(enriched["transaction_amount"])
                enriched["is_round_amount"] = 1 if amount % 100 == 0 or amount % 500 == 0 or amount % 1000 == 0 else 0
                
                # Very high amount (based on dataset analysis)
                enriched["is_high_amount"] = 1 if amount > 10000 else 0
            except (ValueError, TypeError):
                # Default values if amount parsing fails
                enriched["is_round_amount"] = 0
                enriched["is_high_amount"] = 0
        
        return enriched
    
    @staticmethod
    async def invalidate_rules_cache():
        """Invalidate the rules cache"""
        await cache_manager.invalidate("active_rules")

async def initialize_default_rules(db: AsyncSession):
    """Initialize India-specific fraud detection rules if none exist"""
    result = await db.execute(select(Rule))
    existing_rules = result.scalars().all()
    
    if not existing_rules:
        india_specific_rules = [
            # High-Value Transaction Rules
            {
                "rule_name": "Very High Value Transaction",
                "rule_description": "Flag transactions with unusually high amounts for INR context",
                "rule_condition": {
                    ">": [{"var": "transaction_amount"}, 500000]  # ₹5 lakh
                },
                "rule_priority": 100
            },
            {
                "rule_name": "High Value with Round Amount",
                "rule_description": "High-value transactions with suspiciously round amounts",
                "rule_condition": {
                    "and": [
                        {">": [{"var": "transaction_amount"}, 100000]},  # ₹1 lakh
                        {"==": [{"var": "is_round_amount"}, 1]}
                    ]
                },
                "rule_priority": 95
            },
            
            # Time Pattern Rules
            {
                "rule_name": "Late Night High Value",
                "rule_description": "High-value transactions during unusual hours (midnight to 5 AM IST)",
                "rule_condition": {
                    "and": [
                        {">": [{"var": "transaction_amount"}, 50000]},  # ₹50k
                        {"or": [
                            {"==": [{"var": "hour_of_day"}, 0]},
                            {"==": [{"var": "hour_of_day"}, 1]},
                            {"==": [{"var": "hour_of_day"}, 2]},
                            {"==": [{"var": "hour_of_day"}, 3]},
                            {"==": [{"var": "hour_of_day"}, 4]}
                        ]}
                    ]
                },
                "rule_priority": 90
            },
            {
                "rule_name": "Weekend Large Transaction",
                "rule_description": "Large transactions during weekends",
                "rule_condition": {
                    "and": [
                        {"==": [{"var": "is_weekend"}, 1]},
                        {">": [{"var": "transaction_amount"}, 200000]}  # ₹2 lakh
                    ]
                },
                "rule_priority": 85
            },
            
            # UPI/Digital Payment Specific Rules
            {
                "rule_name": "UPI Transaction without Mobile Verification",
                "rule_description": "UPI transactions without verified mobile",
                "rule_condition": {
                    "and": [
                        {"==": [{"var": "transaction_payment_mode_anonymous"}, 11]},  # UPI mode
                        {"==": [{"var": "has_mobile"}, 0]}
                    ]
                },
                "rule_priority": 88
            },
            {
                "rule_name": "Late Night UPI Transaction",
                "rule_description": "UPI transactions during high-risk hours",
                "rule_condition": {
                    "and": [
                        {"==": [{"var": "transaction_payment_mode_anonymous"}, 11]},  # UPI mode
                        {">": [{"var": "transaction_amount"}, 25000]},
                        {"or": [
                            {"==": [{"var": "hour_of_day"}, 2]},
                            {"==": [{"var": "hour_of_day"}, 3]},
                            {"==": [{"var": "hour_of_day"}, 23]}
                        ]}
                    ]
                },
                "rule_priority": 86
            },
            
            # Unusual Browser/Device Rules
            {
                "rule_name": "High-Risk Browser with High Value",
                "rule_description": "Transactions from unusual browsers with high amounts",
                "rule_condition": {
                    "and": [
                        {">": [{"var": "payer_browser_anonymous"}, 4000]},
                        {">": [{"var": "transaction_amount"}, 20000]}  # ₹20k
                    ]
                },
                "rule_priority": 80
            },
            
            # Rare Payment Modes
            {
                "rule_name": "Unusual Payment Mode",
                "rule_description": "Transactions using rare or risky payment modes",
                "rule_condition": {
                    "and": [
                        {"in": [
                            {"var": "transaction_payment_mode_anonymous"}, 
                            [4, 5, 9]  # Identified rare payment modes
                        ]},
                        {">": [{"var": "transaction_amount"}, 10000]}  # ₹10k
                    ]
                },
                "rule_priority": 75
            },
            
            # Multi-factor pattern detection
            {
                "rule_name": "Multiple Risk Factors",
                "rule_description": "Transactions with 3+ risk indicators",
                "rule_condition": {
                    ">=": [
                        {"+": [
                            {"?:": [{">": [{"var": "transaction_amount"}, 100000]}, 1, 0]},
                            {"?:": [{"==": [{"var": "is_round_amount"}, 1]}, 1, 0]},
                            {"?:": [{"==": [{"var": "is_night"}, 1]}, 1, 0]},
                            {"?:": [{"==": [{"var": "is_weekend"}, 1]}, 1, 0]},
                            {"?:": [{">": [{"var": "payer_browser_anonymous"}, 4000]}, 1, 0]},
                            {"?:": [{"in": [{"var": "hour_of_day"}, [0,1,2,3,4,23]]}, 1, 0]},
                            {"?:": [{"==": [{"var": "has_mobile"}, 0]}, 1, 0]}
                        ]},
                        3  # At least 3 risk factors
                    ]
                },
                "rule_priority": 92
            },
            
            # Bank-specific patterns (for Indian banks)
            {
                "rule_name": "High-Risk Bank Transfers",
                "rule_description": "Transactions from certain high-risk bank patterns",
                "rule_condition": {
                    "and": [
                        {"in": [
                            {"var": "payment_gateway_bank_anonymous"}, 
                            [31, 42, 54]  # High-risk bank patterns based on analysis
                        ]},
                        {">": [{"var": "transaction_amount"}, 25000]}  # ₹25k
                    ]
                },
                "rule_priority": 78
            },
            
            # Pattern for transactions with unusual amounts (not round, but specific patterns)
            {
                "rule_name": "Suspicious Amount Pattern",
                "rule_description": "Transactions with suspicious amount patterns",
                "rule_condition": {
                    "and": [
                        {">": [{"var": "transaction_amount"}, 5000]},
                        {"or": [
                            # Amounts ending in 999 (common pattern)
                            {"==": [{"%": [{"var": "transaction_amount"}, 1000]}, 999]},
                            # Amount just below round thresholds to avoid detection
                            {"==": [{"%": [{"var": "transaction_amount"}, 10000]}, 9999]},
                            {"==": [{"%": [{"var": "transaction_amount"}, 50000]}, 49999]}
                        ]}
                    ]
                },
                "rule_priority": 70
            },
            
            # Additional UPI fraud patterns (for Indian context)
            {
                "rule_name": "UPI High Value on New Device",
                "rule_description": "High-value UPI transaction with potential device risk",
                "rule_condition": {
                    "and": [
                        {"==": [{"var": "transaction_payment_mode_anonymous"}, 11]},  # UPI
                        {">": [{"var": "transaction_amount"}, 50000]},  # ₹50k
                        {"or": [
                            {">": [{"var": "payer_browser_anonymous"}, 3500]},
                            {"==": [{"var": "has_mobile"}, 0]}
                        ]}
                    ]
                },
                "rule_priority": 82
            }
        ]
        
        # Add rules to database
        for rule_data in india_specific_rules:
            rule = Rule(**rule_data)
            db.add(rule)
        
        await db.commit()
        logger.info("India-specific fraud detection rules initialized")