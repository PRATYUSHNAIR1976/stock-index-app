#!/usr/bin/env python3
"""
Unit tests for configuration loading and validation
"""

import os
import pytest
import tempfile
from unittest.mock import patch
from src.config import Settings


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_default_settings(self):
        """Test default settings without environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            # This should fail because alpha_vantage_api_key is required
            with pytest.raises(Exception):
                settings = Settings()
    
    def test_valid_settings_with_env(self):
        """Test valid settings with environment variables."""
        test_env = {
            "ALPHA_VANTAGE_API_KEY": "test_key_123",
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            
            assert settings.alpha_vantage_api_key == "test_key_123"
            assert settings.database_url == "stock_data.duckdb"  # Default value
            assert settings.symbols == []  # Default empty list
            assert settings.top_n_default == 100  # Default value
            assert settings.redis_url == "redis://localhost:6379/0"  # Default value
            assert settings.retry_max_attempts == 3  # Default value
            assert settings.retry_backoff_base == 1.0  # Default value
            assert settings.output_base_path == "data"  # Default value
    
    def test_symbols_parsing(self):
        """Test symbols parsing from different formats."""
        test_cases = [
            ("AAPL,MSFT,GOOGL", ["AAPL", "MSFT", "GOOGL"]),
            ("AAPL, MSFT , GOOGL", ["AAPL", "MSFT", "GOOGL"]),
            ("  AAPL  ,  MSFT  ", ["AAPL", "MSFT"]),
            ("", []),
            (["AAPL", "MSFT"], ["AAPL", "MSFT"]),
        ]
        
        for input_symbols, expected in test_cases:
            with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "test_key"}, clear=True):
                if isinstance(input_symbols, str):
                    settings = Settings(symbols=input_symbols)
                else:
                    settings = Settings(symbols=input_symbols)
                
                assert settings.symbols == expected
    
    def test_missing_required_field(self):
        """Test that missing required field raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                Settings()
    
    def test_invalid_numeric_fields(self):
        """Test invalid numeric fields raise validation errors."""
        test_env = {"ALPHA_VANTAGE_API_KEY": "test_key"}
        
        # Test invalid TOP_N_DEFAULT
        with patch.dict(os.environ, {**test_env, "TOP_N_DEFAULT": "invalid"}):
            with pytest.raises(Exception):
                Settings()
        
        # Test invalid RETRY_MAX_ATTEMPTS
        with patch.dict(os.environ, {**test_env, "RETRY_MAX_ATTEMPTS": "invalid"}):
            with pytest.raises(Exception):
                Settings()
        
        # Test invalid RETRY_BACKOFF_BASE
        with patch.dict(os.environ, {**test_env, "RETRY_BACKOFF_BASE": "invalid"}):
            with pytest.raises(Exception):
                Settings()
    
    def test_get_symbols_method(self):
        """Test the get_symbols method."""
        with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "test_key"}, clear=True):
            settings = Settings(symbols=["AAPL", "MSFT"])
            assert settings.get_symbols() == ["AAPL", "MSFT"] 