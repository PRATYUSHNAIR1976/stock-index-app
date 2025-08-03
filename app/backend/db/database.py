"""
Database service for index operations using DuckDB.

This module provides a comprehensive database interface for:
- Stock metadata management
- Daily stock data storage and retrieval
- Index composition persistence
- Performance calculation and storage
- Composition change detection

The module uses DuckDB as the underlying database engine for its
excellent performance with analytical workloads and SQL compatibility.
"""

import duckdb
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


class IndexDatabase:
    """
    Database service for managing stock index data.
    
    This class provides methods for:
    - Creating and managing database tables
    - Storing and retrieving stock metadata
    - Managing daily stock price and market cap data
    - Building and storing index compositions
    - Calculating and storing index performance
    - Detecting composition changes over time
    
    The class uses DuckDB for data storage and provides a clean
    interface for all database operations.
    """
    
    def __init__(self, db_path: str = "stock_data.duckdb"):
        """
        Initialize the database service.
        
        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = db_path
        self._ensure_tables()
        logger.info(f"Initialized database at {db_path}")
    
    def _get_connection(self):
        """
        Get a DuckDB connection.
        
        Returns:
            duckdb.DuckDBPyConnection: Database connection
        """
        return duckdb.connect(self.db_path)
    
    def _ensure_tables(self):
        """
        Ensure all required database tables exist.
        
        This method creates the necessary tables if they don't exist:
        - index_compositions: Stores daily index compositions
        - index_performance: Stores calculated performance metrics
        - composition_changes: Tracks changes in index composition
        
        The tables are created with appropriate constraints and indexes
        for optimal query performance.
        """
        conn = self._get_connection()
        
        # Create index_compositions table
        # This table stores the daily composition of the index
        # Each row represents one stock in the index for a specific date
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_compositions (
                id INTEGER PRIMARY KEY,
                date DATE,
                symbol VARCHAR,
                weight DOUBLE,
                market_cap DOUBLE,
                rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, symbol)
            )
        """)
        
        # Create index_performance table
        # This table stores calculated performance metrics for each date
        # Includes daily returns, cumulative returns, and index values
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_performance (
                id INTEGER PRIMARY KEY,
                date DATE,
                daily_return DOUBLE,
                cumulative_return DOUBLE,
                index_value DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        """)
        
        # Create composition_changes table
        # This table tracks when stocks enter or exit the index
        # Useful for analyzing index turnover and rebalancing
        conn.execute("""
            CREATE TABLE IF NOT EXISTS composition_changes (
                id INTEGER PRIMARY KEY,
                date DATE,
                symbol VARCHAR,
                action VARCHAR,
                previous_rank INTEGER,
                new_rank INTEGER,
                market_cap DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.close()
        logger.info("Database tables ensured")
    
    def get_top_stocks_by_date(self, date: str, top_n: int = 100) -> List[Dict]:
        """
        Get top N stocks by market cap for a specific date.
        
        This method queries the database to find the stocks with the highest
        market capitalization on a given date. It joins stock metadata with
        daily stock data to get both market cap and price information.
        
        Args:
            date: Date in 'YYYY-MM-DD' format
            top_n: Number of top stocks to return
            
        Returns:
            List[Dict]: List of stock dictionaries with symbol, name, exchange,
                       market_cap, close_price, and rank
                       
        Example:
            stocks = db.get_top_stocks_by_date('2024-12-16', 10)
            # Returns list of top 10 stocks by market cap
        """
        conn = self._get_connection()
        
        # Query to get top stocks by market cap
        # Joins stock metadata with daily data to get complete information
        query = """
            SELECT 
                m.symbol,
                m.name,
                m.exchange,
                m.latest_market_cap as market_cap,
                d.close_price,
                ROW_NUMBER() OVER (ORDER BY m.latest_market_cap DESC) as rank
            FROM stock_metadata m
            JOIN daily_stock_data d ON m.symbol = d.symbol
            WHERE d.date = ? 
                AND m.latest_market_cap IS NOT NULL 
                AND d.close_price IS NOT NULL
                AND d.error IS NULL
            ORDER BY m.latest_market_cap DESC
            LIMIT ?
        """
        
        result = conn.execute(query, [date, top_n]).fetchall()
        conn.close()
        
        # Convert database rows to dictionaries
        stocks = []
        for row in result:
            stocks.append({
                "symbol": row[0],
                "name": row[1],
                "exchange": row[2],
                "market_cap": row[3],
                "close_price": row[4],
                "rank": row[5]
            })
        
        return stocks
    
    def save_index_composition(self, date: str, stocks: List[Dict]):
        """
        Save index composition for a specific date.
        
        This method stores the composition of the index for a given date.
        It first clears any existing composition for that date, then
        inserts the new composition with equal weights calculated
        based on the number of stocks.
        
        Args:
            date: Date in 'YYYY-MM-DD' format
            stocks: List of stock dictionaries with symbol, market_cap, and rank
            
        Example:
            stocks = [{'symbol': 'AAPL', 'market_cap': 1000000000, 'rank': 1}]
            db.save_index_composition('2024-12-16', stocks)
        """
        conn = self._get_connection()
        
        # Calculate equal weight for each stock
        # In an equal-weighted index, each stock has the same weight
        equal_weight = 1.0 / len(stocks) if stocks else 0
        
        # Clear existing composition for this date
        # This ensures we don't have duplicate entries
        conn.execute("DELETE FROM index_compositions WHERE date = ?", [date])
        
        # Insert new composition
        for i, stock in enumerate(stocks):
            # Generate unique ID using a smaller number
            # This ensures each record has a unique identifier
            date_int = int(date.replace('-', ''))
            unique_id = (date_int % 10000) * 100 + stock['rank']
            
            conn.execute("""
                INSERT INTO index_compositions (id, date, symbol, weight, market_cap, rank)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [unique_id, date, stock["symbol"], equal_weight, stock["market_cap"], stock["rank"]])
        
        conn.commit()
        conn.close()
        logger.info(f"Saved index composition for {date} with {len(stocks)} stocks")
    
    def get_index_composition(self, date: str) -> List[Dict]:
        """
        Get index composition for a specific date.
        
        This method retrieves the stored index composition for a given date.
        It returns the list of stocks in the index with their weights,
        market caps, and ranks.
        
        Args:
            date: Date in 'YYYY-MM-DD' format
            
        Returns:
            List[Dict]: List of stock dictionaries with symbol, weight,
                       market_cap, and rank
                       
        Example:
            composition = db.get_index_composition('2024-12-16')
            # Returns list of stocks in the index for that date
        """
        conn = self._get_connection()
        
        query = """
            SELECT symbol, weight, market_cap, rank
            FROM index_compositions
            WHERE date = ?
            ORDER BY rank
        """
        
        result = conn.execute(query, [date]).fetchall()
        conn.close()
        
        # Convert database rows to dictionaries
        stocks = []
        for row in result:
            stocks.append({
                "symbol": row[0],
                "weight": row[1],
                "market_cap": row[2],
                "rank": row[3]
            })
        
        return stocks
    
    def calculate_index_performance(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Calculate index performance for a date range.
        
        This method calculates daily returns and cumulative performance
        for the index over a specified date range. It uses a simplified
        approach for demonstration purposes.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List[Dict]: List of performance records with date, daily_return,
                       cumulative_return, and index_value
        """
        conn = self._get_connection()
        
        # Get all dates in range that have index compositions
        query = """
            SELECT DISTINCT date
            FROM index_compositions
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """
        
        dates = [row[0] for row in conn.execute(query, [start_date, end_date]).fetchall()]
        
        if not dates:
            conn.close()
            return []
        
        # Calculate daily returns
        performance = []
        base_value = 100.0  # Base index value
        cumulative_return = 0.0
        
        for i, date in enumerate(dates):
            # Get composition for this date
            comp_query = """
                SELECT ic.symbol, ic.weight, d.close_price
                FROM index_compositions ic
                JOIN daily_stock_data d ON ic.symbol = d.symbol
                WHERE ic.date = ? AND d.date = ?
            """
            
            composition = conn.execute(comp_query, [date, date]).fetchall()
            
            if not composition:
                continue
            
            # Calculate weighted return
            # For simplicity, we use a fixed return rate
            # In a real implementation, you'd calculate actual returns
            daily_return = 0.0
            for symbol, weight, close_price in composition:
                if close_price and weight:
                    # Assume 1% daily return for demonstration
                    daily_return += weight * 0.01
            
            cumulative_return += daily_return
            index_value = base_value * (1 + cumulative_return)
            
            performance.append({
                "date": date,
                "daily_return": daily_return * 100,  # Convert to percentage
                "cumulative_return": cumulative_return * 100,
                "index_value": index_value
            })
            
            # Save to database
            conn.execute("""
                DELETE FROM index_performance WHERE date = ?
            """, [date])
            conn.execute("""
                INSERT INTO index_performance (id, date, daily_return, cumulative_return, index_value)
                VALUES (?, ?, ?, ?, ?)
            """, [i + 1, date, daily_return * 100, cumulative_return * 100, index_value])
        
        conn.commit()
        conn.close()
        
        return performance
    
    def get_index_performance(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get stored index performance for a date range.
        
        This method retrieves previously calculated performance data
        from the database for a specified date range.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List[Dict]: List of performance records
        """
        conn = self._get_connection()
        
        query = """
            SELECT date, daily_return, cumulative_return, index_value
            FROM index_performance
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """
        
        result = conn.execute(query, [start_date, end_date]).fetchall()
        conn.close()
        
        performance = []
        for row in result:
            performance.append({
                "date": row[0],
                "daily_return": row[1],
                "cumulative_return": row[2],
                "index_value": row[3]
            })
        
        return performance
    
    def detect_composition_changes(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Detect composition changes between dates.
        
        This method analyzes index compositions over time to identify
        when stocks enter or exit the index. It compares compositions
        between consecutive dates to detect changes.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List[Dict]: List of composition change records
        """
        conn = self._get_connection()
        
        # Get all dates in range
        query = """
            SELECT DISTINCT date
            FROM index_compositions
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """
        
        dates = [row[0] for row in conn.execute(query, [start_date, end_date]).fetchall()]
        
        if len(dates) < 2:
            conn.close()
            return []
        
        changes = []
        
        # Compare consecutive dates
        for i in range(1, len(dates)):
            current_date = dates[i]
            previous_date = dates[i - 1]
            
            # Get current and previous compositions
            current_composition = conn.execute("""
                SELECT symbol, rank, market_cap
                FROM index_compositions
                WHERE date = ?
                ORDER BY symbol
            """, [current_date]).fetchall()
            
            previous_composition = conn.execute("""
                SELECT symbol, rank, market_cap
                FROM index_compositions
                WHERE date = ?
                ORDER BY symbol
            """, [previous_date]).fetchall()
            
            # Convert to sets for easy comparison
            current_symbols = {row[0] for row in current_composition}
            previous_symbols = {row[0] for row in previous_composition}
            
            # Find new stocks (entered the index)
            new_stocks = current_symbols - previous_symbols
            for symbol in new_stocks:
                # Find the stock's details
                for row in current_composition:
                    if row[0] == symbol:
                        changes.append({
                            "date": current_date,
                            "symbol": symbol,
                            "action": "entered",
                            "previous_rank": None,
                            "new_rank": row[1],
                            "market_cap": row[2]
                        })
                        break
            
            # Find removed stocks (exited the index)
            removed_stocks = previous_symbols - current_symbols
            for symbol in removed_stocks:
                # Find the stock's previous details
                for row in previous_composition:
                    if row[0] == symbol:
                        changes.append({
                            "date": current_date,
                            "symbol": symbol,
                            "action": "exited",
                            "previous_rank": row[1],
                            "new_rank": None,
                            "market_cap": row[2]
                        })
                        break
        
        conn.close()
        return changes
    
    def get_composition_changes(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get stored composition changes for a date range.
        
        This method retrieves previously detected composition changes
        from the database for a specified date range.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List[Dict]: List of composition change records
        """
        conn = self._get_connection()
        
        query = """
            SELECT date, symbol, action, previous_rank, new_rank, market_cap
            FROM composition_changes
            WHERE date BETWEEN ? AND ?
            ORDER BY date, symbol
        """
        
        result = conn.execute(query, [start_date, end_date]).fetchall()
        conn.close()
        
        changes = []
        for row in result:
            changes.append({
                "date": row[0],
                "symbol": row[1],
                "action": row[2],
                "previous_rank": row[3],
                "new_rank": row[4],
                "market_cap": row[5]
            })
        
        return changes 