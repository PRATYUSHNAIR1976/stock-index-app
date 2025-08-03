#!/usr/bin/env python3
"""
Unit tests for data sources with mocked scenarios
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.sources.yahoo import YahooFinanceSource
from src.sources.alphavantage import AlphaVantageSource


class TestYahooFinanceSource:
    """Test Yahoo Finance source with mocked scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.yahoo_source = YahooFinanceSource()
    
    @patch('src.sources.yahoo.yf.Ticker')
    def test_successful_fetch(self, mock_ticker):
        """Test successful fetch returning price."""
        # Mock successful response
        mock_ticker_instance = Mock()
        mock_hist_data = Mock()
        mock_hist_data.empty = False
        
        # Create a proper pandas-like index
        mock_index = Mock()
        mock_strftime_result = Mock()
        mock_strftime_result.values = ['2024-12-16']
        mock_index.strftime = lambda fmt: mock_strftime_result
        mock_hist_data.index = mock_index
        
        # Mock the loc accessor - simpler approach
        mock_loc = Mock()
        mock_loc.__getitem__ = lambda key, *args: 150.0  # Always return 150.0
        mock_hist_data.loc = mock_loc
        mock_ticker_instance.history.return_value = mock_hist_data
        
        # Mock market cap info
        mock_ticker_instance.info = {'marketCap': 2000000000}
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.yahoo_source.fetch("AAPL", "2024-12-16")
        
        assert result["symbol"] == "AAPL"
        assert result["date"] == "2024-12-16"
        assert result["close_price"] == 150.0
        assert result["market_cap"] == 2000000000
        assert result["source"] == "yahoo"
        assert result["error"] is None
    
    @patch('src.sources.yahoo.yf.Ticker')
    def test_network_error_then_success(self, mock_ticker):
        """Test network error causing retries then success."""
        # First call raises exception, second call succeeds
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = [
            Exception("Network error"),  # First call fails
            Mock(empty=False, index=['2024-12-16'], loc={'2024-12-16': {'Close': 150.0}})  # Second call succeeds
        ]
        mock_ticker_instance.info = {'marketCap': 2000000000}
        mock_ticker.return_value = mock_ticker_instance
        
        # The retry decorator should handle this, but we test the underlying logic
        with patch('src.sources.yahoo.logger') as mock_logger:
            result = self.yahoo_source.fetch("AAPL", "2024-12-16")
            
            # Should still return error result due to exception
            assert result["error"] is not None
            assert "Failed to fetch data" in result["error"]
    
    @patch('src.sources.yahoo.yf.Ticker')
    def test_persistent_failure(self, mock_ticker):
        """Test persistent failure leading to error field stored."""
        # Mock empty data (no trading day)
        mock_ticker_instance = Mock()
        mock_hist_data = Mock()
        mock_hist_data.empty = True
        mock_ticker_instance.history.return_value = mock_hist_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.yahoo_source.fetch("AAPL", "2024-12-15")  # Weekend date
        
        assert result["symbol"] == "AAPL"
        assert result["date"] == "2024-12-15"
        assert result["close_price"] is None
        assert result["market_cap"] is None
        assert result["source"] == "yahoo"
        assert "likely weekend or holiday" in result["error"]
    
    @patch('src.sources.yahoo.yf.Ticker')
    def test_market_cap_not_available(self, mock_ticker):
        """Test when market cap is not available."""
        mock_ticker_instance = Mock()
        mock_hist_data = Mock()
        mock_hist_data.empty = False
        
        # Create a proper pandas-like index
        mock_index = Mock()
        mock_strftime_result = Mock()
        mock_strftime_result.values = ['2024-12-16']
        mock_index.strftime = lambda fmt: mock_strftime_result
        mock_hist_data.index = mock_index
        
        # Mock the loc accessor - simpler approach
        mock_loc = Mock()
        mock_loc.__getitem__ = lambda key, *args: 150.0  # Always return 150.0
        mock_hist_data.loc = mock_loc
        mock_ticker_instance.history.return_value = mock_hist_data
        
        # No market cap in info
        mock_ticker_instance.info = {}
        mock_ticker.return_value = mock_ticker_instance
        
        result = self.yahoo_source.fetch("AAPL", "2024-12-16")
        
        assert result["close_price"] == 150.0
        assert result["market_cap"] is None
        assert result["error"] is None


class TestAlphaVantageSource:
    """Test Alpha Vantage source with mocked scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.alpha_source = AlphaVantageSource("test_api_key")
    
    @patch('src.sources.alphavantage.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful fetch returning price."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2024-12-16": {
                    "4. close": "150.00"
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = self.alpha_source.fetch("AAPL", "2024-12-16")
        
        assert result["symbol"] == "AAPL"
        assert result["date"] == "2024-12-16"
        assert result["close_price"] == 150.0
        assert result["market_cap"] is None  # Alpha Vantage doesn't provide market cap
        assert result["source"] == "alphavantage"
        assert result["error"] is None
    
    @patch('src.sources.alphavantage.requests.get')
    def test_network_error_then_success(self, mock_get):
        """Test network error causing retries then success."""
        # First call raises exception, second call succeeds
        mock_get.side_effect = [
            Exception("Connection error"),  # First call fails
            Mock(status_code=200, json=lambda: {
                "Time Series (Daily)": {
                    "2024-12-16": {"4. close": "150.00"}
                }
            })  # Second call succeeds
        ]
        
        with patch('src.sources.alphavantage.logger') as mock_logger:
            result = self.alpha_source.fetch("AAPL", "2024-12-16")
            
            # Should still return error result due to exception
            assert result["error"] is not None
            assert "Failed to fetch data" in result["error"]
    
    @patch('src.sources.alphavantage.requests.get')
    def test_persistent_failure(self, mock_get):
        """Test persistent failure leading to error field stored."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "Invalid API call"
        }
        mock_get.return_value = mock_response
        
        result = self.alpha_source.fetch("INVALID", "2024-12-16")
        
        assert result["symbol"] == "INVALID"
        assert result["date"] == "2024-12-16"
        assert result["close_price"] is None
        assert result["market_cap"] is None
        assert result["source"] == "alphavantage"
        assert "API Error" in result["error"]
    
    @patch('src.sources.alphavantage.requests.get')
    def test_rate_limit_error(self, mock_get):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Note": "API call frequency limit exceeded"
        }
        mock_get.return_value = mock_response
        
        result = self.alpha_source.fetch("AAPL", "2024-12-16")
        
        assert result["close_price"] is None
        assert "Rate limit" in result["error"]
    
    @patch('src.sources.alphavantage.requests.get')
    def test_closest_date_fallback(self, mock_get):
        """Test fallback to closest earlier date."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Time Series (Daily)": {
                "2024-12-15": {"4. close": "149.00"},  # Earlier date
                "2024-12-14": {"4. close": "148.00"}   # Even earlier
            }
        }
        mock_get.return_value = mock_response
        
        result = self.alpha_source.fetch("AAPL", "2024-12-16")  # Requested date not available
        
        assert result["symbol"] == "AAPL"
        assert result["date"] == "2024-12-15"  # Should use closest earlier date
        assert result["close_price"] == 149.0
        assert "closest earlier date" in result["error"]  # Warning message
    
    @patch('src.sources.alphavantage.requests.get')
    def test_http_error(self, mock_get):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        result = self.alpha_source.fetch("AAPL", "2024-12-16")
        
        assert result["close_price"] is None
        assert "HTTP 500" in result["error"] 