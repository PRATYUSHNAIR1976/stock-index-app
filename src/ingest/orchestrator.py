import duckdb
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from src.config import settings
from src.logger import get_logger
from src.sources.yahoo import YahooFinanceSource
from src.sources.alphavantage import AlphaVantageSource

logger = get_logger(__name__)


class DataOrchestrator:
    """Orchestrates data ingestion from multiple sources into DuckDB."""
    
    def __init__(self):
        self.db_url = settings.database_url
        self.conn = None
        self.yahoo_source = YahooFinanceSource()
        self.alpha_source = AlphaVantageSource(settings.alpha_vantage_api_key)
        
    def connect(self):
        """Establish DuckDB connection."""
        try:
            self.conn = duckdb.connect(self.db_url)
            logger.info(f"Connected to DuckDB at {self.db_url}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {str(e)}")
            raise
    
    def close(self):
        """Close DuckDB connection."""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")
    
    def create_tables(self):
        """Create tables if they don't exist (safe creation, no DROP)."""
        try:
            # Create stock_metadata table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_metadata (
                    symbol VARCHAR PRIMARY KEY,
                    name VARCHAR,
                    exchange VARCHAR,
                    latest_market_cap DOUBLE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create daily_stock_data table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stock_data (
                    symbol VARCHAR,
                    date DATE,
                    close_price DOUBLE,
                    market_cap DOUBLE,
                    source VARCHAR,
                    error VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, date)
                )
            """)
            
            # Create top_universe table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS top_universe (
                    symbol VARCHAR,
                    date DATE,
                    market_cap DOUBLE,
                    rank INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    def upsert_stock_metadata(self, symbol: str, name: str = None, exchange: str = None, 
                             market_cap: Optional[float] = None):
        """Upsert stock metadata using DuckDB's INSERT OR REPLACE."""
        try:
            # Check if record exists
            existing = self.conn.execute("""
                SELECT symbol FROM stock_metadata WHERE symbol = ?
            """, [symbol]).fetchone()
            
            if existing:
                # Update existing record
                update_fields = []
                params = []
                
                if name is not None:
                    update_fields.append("name = ?")
                    params.append(name)
                if exchange is not None:
                    update_fields.append("exchange = ?")
                    params.append(exchange)
                if market_cap is not None:
                    update_fields.append("latest_market_cap = ?")
                    params.append(market_cap)
                
                update_fields.append("last_updated = CURRENT_TIMESTAMP")
                params.append(symbol)
                
                if update_fields:
                    query = f"""
                        UPDATE stock_metadata 
                        SET {', '.join(update_fields)}
                        WHERE symbol = ?
                    """
                    self.conn.execute(query, params)
            else:
                # Insert new record
                self.conn.execute("""
                    INSERT INTO stock_metadata (symbol, name, exchange, latest_market_cap)
                    VALUES (?, ?, ?, ?)
                """, [symbol, name, exchange, market_cap])
            
            logger.debug(f"Upserted metadata for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to upsert metadata for {symbol}: {str(e)}")
            raise
    
    def upsert_daily_data(self, symbol: str, date: str, close_price: Optional[float], 
                         market_cap: Optional[float], source: str, error: Optional[str] = None):
        """Upsert daily stock data with idempotent logic."""
        try:
            # Check if record exists
            existing = self.conn.execute("""
                SELECT close_price, market_cap FROM daily_stock_data 
                WHERE symbol = ? AND date = ?
            """, [symbol, date]).fetchone()
            
            if existing:
                existing_close, existing_market_cap = existing
                
                # Only update if new data has non-null values for previously null fields
                should_update = False
                new_close_price = existing_close
                new_market_cap = existing_market_cap
                
                if existing_close is None and close_price is not None:
                    new_close_price = close_price
                    should_update = True
                
                if existing_market_cap is None and market_cap is not None:
                    new_market_cap = market_cap
                    should_update = True
                
                if should_update:
                    self.conn.execute("""
                        UPDATE daily_stock_data 
                        SET close_price = ?, market_cap = ?, source = ?, error = ?, 
                            updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = ? AND date = ?
                    """, [new_close_price, new_market_cap, source, error, symbol, date])
                    logger.debug(f"Updated daily data for {symbol} on {date}")
            else:
                # Insert new record
                self.conn.execute("""
                    INSERT INTO daily_stock_data (symbol, date, close_price, market_cap, source, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [symbol, date, close_price, market_cap, source, error])
                logger.debug(f"Inserted daily data for {symbol} on {date}")
            
        except Exception as e:
            logger.error(f"Failed to upsert daily data for {symbol} on {date}: {str(e)}")
            raise
    
    def fetch_stock_data(self, symbol: str, date: str) -> Dict[str, Any]:
        """Fetch stock data with fallback logic."""
        # Try Yahoo first
        yahoo_result = self.yahoo_source.fetch(symbol, date)
        
        if yahoo_result.get("close_price") is not None:
            logger.info(f"Yahoo data successful for {symbol} on {date}")
            return yahoo_result
        
        # Fallback to Alpha Vantage
        logger.info(f"Yahoo failed for {symbol} on {date}, trying Alpha Vantage")
        alpha_result = self.alpha_source.fetch(symbol, date)
        
        if alpha_result.get("close_price") is not None:
            logger.info(f"Alpha Vantage data successful for {symbol} on {date}")
            return alpha_result
        
        # Both failed, return the last result (with error)
        logger.warning(f"Both sources failed for {symbol} on {date}")
        return yahoo_result if yahoo_result.get("error") else alpha_result
    
    def ingest(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Ingest stock data for given symbols and date range.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with ingestion summary
        """
        logger.info(f"Starting ingestion for {len(symbols)} symbols from {start_date} to {end_date}")
        
        # Connect to database
        self.connect()
        self.create_tables()
        
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Initialize counters
        total_symbols = len(symbols)
        total_dates = 0
        successes = 0
        failures = 0
        failed_pairs = []
        
        try:
            # Process each symbol
            for symbol in symbols:
                logger.info(f"Processing symbol: {symbol}")
                
                # Process each date in range
                current_dt = start_dt
                while current_dt <= end_dt:
                    current_date = current_dt.strftime("%Y-%m-%d")
                    total_dates += 1
                    
                    try:
                        # Fetch data
                        result = self.fetch_stock_data(symbol, current_date)
                        
                        # Upsert daily data
                        self.upsert_daily_data(
                            symbol=symbol,
                            date=current_date,
                            close_price=result.get("close_price"),
                            market_cap=result.get("market_cap"),
                            source=result.get("source"),
                            error=result.get("error")
                        )
                        
                        # Update metadata if we have market cap data
                        if result.get("market_cap") is not None:
                            self.upsert_stock_metadata(
                                symbol=symbol,
                                market_cap=result.get("market_cap")
                            )
                        
                        # Track success/failure
                        if result.get("close_price") is not None:
                            successes += 1
                            logger.debug(f"Success: {symbol} on {current_date}")
                        else:
                            failures += 1
                            failed_pairs.append(f"{symbol}-{current_date}")
                            logger.warning(f"Failed: {symbol} on {current_date} - {result.get('error')}")
                    
                    except Exception as e:
                        failures += 1
                        failed_pairs.append(f"{symbol}-{current_date}")
                        logger.error(f"Exception processing {symbol} on {current_date}: {str(e)}")
                    
                    current_dt += timedelta(days=1)
            
            # Commit all changes
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            self.conn.rollback()
            raise
        finally:
            self.close()
        
        # Prepare summary
        summary = {
            "total_symbols": total_symbols,
            "total_dates": total_dates,
            "successes": successes,
            "failures": failures,
            "failed_pairs": failed_pairs,
            "success_rate": (successes / total_dates * 100) if total_dates > 0 else 0
        }
        
        # Log summary
        logger.info("Ingestion completed!")
        logger.info(f"Total symbols: {total_symbols}")
        logger.info(f"Total dates: {total_dates}")
        logger.info(f"Successes: {successes}")
        logger.info(f"Failures: {failures}")
        logger.info(f"Success rate: {summary['success_rate']:.2f}%")
        
        if failed_pairs:
            logger.warning(f"Failed symbol-date pairs: {failed_pairs}")
        
        return summary 