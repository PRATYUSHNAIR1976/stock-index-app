"""
Alpha Vantage data source for fetching stock market data.

This module provides a data source that fetches stock information from Alpha Vantage
API. It handles stock prices and provides fallback functionality when exact dates
are not available.

Features:
- Fetch closing prices for specific trading dates
- Handle API rate limits and errors
- Find closest earlier trading date if exact date not available
- Automatic retry mechanism for network failures
- Comprehensive error handling and logging
"""

import requests
from typing import Dict, Union
from src.logger import get_logger
from src.retry import retry_on_exception

# Get logger for this module
logger = get_logger(__name__)

class AlphaVantageSource:
    """
    Data source for fetching stock data from Alpha Vantage API.
    
    This class provides methods to fetch stock information including:
    - Closing prices for specific dates
    - Fallback to closest earlier trading date
    - API rate limit handling
    - Error message parsing
    
    The class uses the Alpha Vantage REST API to access stock data
    and includes retry logic for handling network failures.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Alpha Vantage data source.
        
        Args:
            api_key: Alpha Vantage API key (required for API access)
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        logger.info("Initialized Alpha Vantage data source")
    
    @retry_on_exception(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch(self, symbol: str, date: str) -> Dict[str, Union[str, float, None]]:
        """
        Fetch stock data for a specific symbol and date from Alpha Vantage.
        
        This method retrieves the closing price for a given stock symbol on a
        specific date. If the exact date is not available, it finds the closest
        earlier trading date and includes a warning in the response.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            date: Date in 'YYYY-MM-DD' format
            
        Returns:
            Dict containing:
                - symbol: Stock symbol
                - date: Actual date of data (may differ from requested date)
                - close_price: Closing price (float or None if not available)
                - market_cap: Always None (Alpha Vantage doesn't provide market cap)
                - source: Data source identifier ('alphavantage')
                - error: Error message (str or None if successful)
                
        Example:
            result = source.fetch('AAPL', '2024-12-16')
            # Returns: {
            #     'symbol': 'AAPL',
            #     'date': '2024-12-16',
            #     'close_price': 150.25,
            #     'market_cap': None,
            #     'source': 'alphavantage',
            #     'error': None
            # }
        """
        
        try:
            logger.info(f"Fetching data for {symbol} on {date}")
            
            # Prepare API request parameters
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "compact"  # Get last 100 data points
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Parse JSON response
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                error_msg = data["Error Message"]
                logger.error(f"Alpha Vantage API error for {symbol}: {error_msg}")
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": None,
                    "market_cap": None,
                    "source": "alphavantage",
                    "error": error_msg
                }
            
            # Check for rate limit or other API notes
            if "Note" in data:
                note_msg = data["Note"]
                logger.warning(f"Alpha Vantage API note for {symbol}: {note_msg}")
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": None,
                    "market_cap": None,
                    "source": "alphavantage",
                    "error": f"API rate limit: {note_msg}"
                }
            
            # Extract time series data
            time_series = data.get("Time Series (Daily)")
            if not time_series:
                logger.error(f"No time series data found for {symbol}")
                return {
                    "symbol": symbol,
                    "date": date,
                    "close_price": None,
                    "market_cap": None,
                    "source": "alphavantage",
                    "error": "No time series data available"
                }
            
            # Try to get data for the exact date
            if date in time_series:
                close_price = float(time_series[date]["4. close"])
                actual_date = date
                warning = None
            else:
                # Find the closest earlier trading date
                available_dates = sorted(time_series.keys(), reverse=True)
                actual_date = None
                
                for available_date in available_dates:
                    if available_date <= date:
                        actual_date = available_date
                        break
                
                if actual_date:
                    close_price = float(time_series[actual_date]["4. close"])
                    warning = f"Exact date {date} not available, using {actual_date}"
                    logger.warning(f"Using closest earlier date for {symbol}: {actual_date} instead of {date}")
                else:
                    logger.error(f"No data available for {symbol} on or before {date}")
                    return {
                        "symbol": symbol,
                        "date": date,
                        "close_price": None,
                        "market_cap": None,
                        "source": "alphavantage",
                        "error": f"No data available for {symbol} on or before {date}"
                    }
            
            logger.info(f"Successfully fetched data for {symbol}: price={close_price}, date={actual_date}")
            
            return {
                "symbol": symbol,
                "date": actual_date,
                "close_price": close_price,
                "market_cap": None,  # Alpha Vantage doesn't provide market cap
                "source": "alphavantage",
                "error": warning  # Warning message if date was adjusted
            }
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching data for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "date": date,
                "close_price": None,
                "market_cap": None,
                "source": "alphavantage",
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} on {date}: {str(e)}")
            return {
                "symbol": symbol,
                "date": date,
                "close_price": None,
                "market_cap": None,
                "source": "alphavantage",
                "error": str(e)
            } 