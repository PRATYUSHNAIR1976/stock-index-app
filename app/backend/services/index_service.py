import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.backend.db.database import IndexDatabase
from app.backend.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class IndexService:
    """Service for index construction and management."""
    
    def __init__(self):
        from src.config import settings
        self.db = IndexDatabase(settings.database_url)
        self.redis_client = get_redis_client()
    
    def build_index(self, start_date: str, end_date: Optional[str] = None, top_n: int = 100) -> Dict:
        """Build equal-weighted index for the specified date range."""
        try:
            # If no end_date provided, use start_date
            if not end_date:
                end_date = start_date
            
            # Get all trading dates in range
            dates = self._get_trading_dates_in_range(start_date, end_date)
            
            if not dates:
                return {
                    "success": False,
                    "error": f"No trading data available for date range {start_date} to {end_date}"
                }
            
            total_compositions = 0
            total_performance_calculated = 0
            
            # Build index for each date
            for date in dates:
                try:
                    # Get top N stocks by market cap
                    date_str = date.strftime('%Y-%m-%d')
                    stocks = self.db.get_top_stocks_by_date(date_str, top_n)
                    
                    if len(stocks) < top_n:
                        logger.warning(f"Only {len(stocks)} stocks available for {date}, expected {top_n}")
                    
                    if stocks:
                        # Save composition
                        self.db.save_index_composition(date_str, stocks)
                        total_compositions += 1
                        
                        # Clear cache for this date
                        self._clear_cache_for_date(date_str)
                        
                        logger.info(f"Built index for {date} with {len(stocks)} stocks")
                    
                except Exception as e:
                    logger.error(f"Error building index for {date}: {str(e)}")
                    continue
            
            # Calculate performance for the entire range
            try:
                performance = self.db.calculate_index_performance(start_date, end_date)
                total_performance_calculated = len(performance)
                logger.info(f"Calculated performance for {len(performance)} days")
            except Exception as e:
                logger.error(f"Error calculating performance: {str(e)}")
            
            # Detect composition changes
            try:
                changes = self.db.detect_composition_changes(start_date, end_date)
                logger.info(f"Detected {len(changes)} composition changes")
            except Exception as e:
                logger.error(f"Error detecting composition changes: {str(e)}")
            
            return {
                "success": True,
                "date_range": f"{start_date} to {end_date}",
                "total_dates_processed": len(dates),
                "total_compositions_built": total_compositions,
                "total_performance_calculated": total_performance_calculated,
                "top_n": top_n
            }
            
        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_index_composition(self, date: str, use_cache: bool = True) -> Dict:
        """Get index composition for a specific date."""
        cache_key = f"index_composition:{date}"
        
        # Try cache first
        if use_cache and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    import json
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Cache error: {str(e)}")
        
        # Get from database
        try:
            stocks = self.db.get_index_composition(date)
            
            if not stocks:
                return {
                    "success": False,
                    "error": f"No index composition found for {date}"
                }
            
            equal_weight = 1.0 / len(stocks) if stocks else 0
            
            result = {
                "success": True,
                "date": date,
                "total_stocks": len(stocks),
                "equal_weight": equal_weight,
                "stocks": stocks
            }
            
            # Cache the result
            if use_cache and self.redis_client:
                try:
                    import json
                    self.redis_client.setex(cache_key, 3600, json.dumps(result))  # Cache for 1 hour
                except Exception as e:
                    logger.warning(f"Cache error: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting index composition: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_index_performance(self, start_date: str, end_date: str, use_cache: bool = True) -> Dict:
        """Get index performance for a date range."""
        cache_key = f"index_performance:{start_date}:{end_date}"
        
        # Try cache first
        if use_cache and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    import json
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Cache error: {str(e)}")
        
        # Get from database
        try:
            performance = self.db.get_index_performance(start_date, end_date)
            
            if not performance:
                return {
                    "success": False,
                    "error": f"No performance data found for date range {start_date} to {end_date}"
                }
            
            # Calculate total return
            if performance:
                total_return = performance[-1]["cumulative_return"]
            else:
                total_return = 0.0
            
            result = {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "total_return": total_return,
                "daily_returns": performance
            }
            
            # Cache the result
            if use_cache and self.redis_client:
                try:
                    import json
                    self.redis_client.setex(cache_key, 3600, json.dumps(result))  # Cache for 1 hour
                except Exception as e:
                    logger.warning(f"Cache error: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting index performance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_composition_changes(self, start_date: str, end_date: str, use_cache: bool = True) -> Dict:
        """Get composition changes for a date range."""
        cache_key = f"composition_changes:{start_date}:{end_date}"
        
        # Try cache first
        if use_cache and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    import json
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Cache error: {str(e)}")
        
        # Get from database
        try:
            changes = self.db.get_composition_changes(start_date, end_date)
            
            result = {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "total_changes": len(changes),
                "changes": changes
            }
            
            # Cache the result
            if use_cache and self.redis_client:
                try:
                    import json
                    self.redis_client.setex(cache_key, 3600, json.dumps(result))  # Cache for 1 hour
                except Exception as e:
                    logger.warning(f"Cache error: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting composition changes: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_trading_dates_in_range(self, start_date: str, end_date: str) -> List[str]:
        """Get all trading dates in the specified range."""
        try:
            conn = self.db._get_connection()
            
            query = """
                SELECT DISTINCT date
                FROM daily_stock_data
                WHERE date BETWEEN ? AND ?
                    AND error IS NULL
                ORDER BY date
            """
            
            result = conn.execute(query, [start_date, end_date]).fetchall()
            conn.close()
            
            return [row[0] for row in result]
            
        except Exception as e:
            logger.error(f"Error getting trading dates: {str(e)}")
            return []
    
    def _clear_cache_for_date(self, date: str):
        """Clear cache entries for a specific date."""
        if not self.redis_client:
            return
        
        try:
            # Clear composition cache
            self.redis_client.delete(f"index_composition:{date}")
            
            # Clear performance cache (would need to clear ranges that include this date)
            # For simplicity, we'll clear all performance cache
            pattern = "index_performance:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # Clear composition changes cache
            pattern = "composition_changes:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}") 