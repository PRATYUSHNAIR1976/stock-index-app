"""
Configuration settings for the Stock Index Application.

This module defines all application settings using Pydantic BaseSettings.
Settings can be loaded from environment variables or use default values.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional

class Settings(BaseSettings):
    """
    Application settings class that loads configuration from environment variables.
    
    This class uses Pydantic BaseSettings to automatically load values from
    environment variables. If an environment variable is not set, it uses
    the default value specified in the Field.
    """
    
    # Database configuration - path to the DuckDB database file
    database_url: str = Field(default="stock_data.duckdb")
    
    # Alpha Vantage API key - required for fetching stock data
    # This must be set as an environment variable: ALPHA_VANTAGE_API_KEY
    alpha_vantage_api_key: str = Field(..., env="ALPHA_VANTAGE_API_KEY")
    
    # List of stock symbols to track - can be loaded from environment variable
    # Format: "AAPL,MSFT,GOOGL" or ["AAPL", "MSFT", "GOOGL"]
    symbols: List[str] = Field(default_factory=list)
    
    # Default number of top stocks to include in the index
    top_n_default: int = Field(default=100)
    
    # Redis connection URL for caching - defaults to local Redis instance
    redis_url: Optional[str] = Field(default="redis://localhost:6379/0")
    
    # Retry configuration for API calls
    retry_max_attempts: int = Field(default=3)  # Maximum number of retry attempts
    retry_backoff_base: float = Field(default=1.0)  # Base delay for exponential backoff
    
    # Base path for output files (exports, logs, etc.)
    output_base_path: str = Field(default="data")

    @field_validator("symbols", mode="before")
    @classmethod
    def parse_symbols(cls, v):
        """
        Parse stock symbols from various input formats.
        
        This validator converts stock symbols to a standardized format:
        - Converts to uppercase
        - Removes whitespace
        - Handles both string and list inputs
        
        Args:
            v: Input value (string or list)
            
        Returns:
            List[str]: Cleaned list of stock symbols
        """
        if isinstance(v, str):
            # Split comma-separated string and clean each symbol
            return [s.strip().upper() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            # Clean each symbol in the list
            return [s.strip().upper() for s in v if s.strip()]
        return []

    def get_symbols(self) -> List[str]:
        """
        Get the list of stock symbols to track.
        
        Returns:
            List[str]: List of stock symbols in uppercase format
        """
        return self.symbols

# Create a global settings instance that loads configuration on import
settings = Settings()
