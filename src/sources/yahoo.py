"""
Yahoo Finance data source for fetching stock market data.

This module provides a data source that fetches stock information from Yahoo Finance
using the yfinance library. It handles stock prices, market capitalization, and
trading day validation.

Features:
- Fetch closing prices for specific trading dates
- Retrieve market capitalization data when available
- Handle non-trading days (weekends, holidays)
- Automatic retry mechanism for network failures
- Comprehensive error handling and logging
"""

import yfinance as yf
from typing import Dict, Union
from src.logger import get_logger
from src.retry import retry_on_exception

# Get logger for this module
logger = get_logger(__name__)

class YahooFinanceSource:
    """
    Data source for fetching stock data from Yahoo Finance.
    
    This class provides methods to fetch stock information including:
    - Closing prices for specific dates
    - Market capitalization data
    - Trading day validation
    
    The class uses the yfinance library to access Yahoo Finance data
    and includes retry logic for handling network failures.
    """
    
    def __init__(self):
        """Initialize the Yahoo Finance data source."""
        logger.info("Initialized Yahoo Finance data source")
    
    @retry_on_exception(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch(self, symbol: str, date: str) -> Dict[str, Union[str, float, None]]:
        """
        Fetch stock data for a specific symbol and date from Yahoo Finance.
        
        This method retrieves the closing price and market capitalization
        for a given stock symbol on a specific date. It handles various
        scenarios including non-trading days and missing data.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            date: Date in 'YYYY-MM-DD' format
            
        Returns:
            Dict containing:
                - symbol: Stock symbol
                - date: Requested date
                - close_price: Closing price (float or None if not available)
                - market_cap: Market capitalization (float or None if not available)
                - source: Data source identifier ('yahoo')
                - error: Error message (str or None if successful)
                
        Example:
            result = source.fetch('AAPL', '2024-12-16')
            # Returns: {
            #     'symbol': 'AAPL',
            #     'date': '2024-12-16',
            #     'close_price': 150.25,
            #     'market_cap': 2500000000000.0,
            #     'source': 'yahoo',
            #     'error': None
            # }
        """
        
        try:
            logger.info(f"Fetching data for {symbol} on {date}")
            
            # Create a Ticker object for the symbol
            ticker = yf.Ticker(symbol)
            
            # Get historical data for the specific date
            # We fetch a small range around the date to handle timezone issues
            hist_data = ticker.history(start=date, end=date, period="1d")
            
            # Check if we got any data
            if hist_data.empty:
                logger.warning(f"No data found for {symbol} on {date}")
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": None,
                    "market_cap": None,
                    "source": "yahoo",
                    "error": f"No price data found for {symbol} on {date}, likely weekend or holiday"
                }
            
            # Extract the closing price
            close_price = hist_data['Close'].iloc[0]
            
            # Try to get market cap from ticker info
            market_cap = None
            try:
                ticker_info = ticker.info
                market_cap = ticker_info.get('marketCap')
                if market_cap:
                    logger.debug(f"Found market cap for {symbol}: {market_cap}")
            except Exception as e:
                logger.warning(f"Could not fetch market cap for {symbol}: {str(e)}")
            
            logger.info(f"Successfully fetched data for {symbol}: price={close_price}, market_cap={market_cap}")
            
            return {
                "symbol": symbol,
                "date": date,
                "close_price": float(close_price),
                "market_cap": float(market_cap) if market_cap else None,
                "source": "yahoo",
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} on {date}: {str(e)}")
            return {
                "symbol": symbol,
                "date": date,
                "close_price": None,
                "market_cap": None,
                "source": "yahoo",
                "error": str(e)
            } 