from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class IndexComposition(BaseModel):
    """Model for index composition data."""
    id: Optional[int] = None
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    symbol: str = Field(..., description="Stock symbol")
    weight: float = Field(..., description="Equal weight (1/N for N stocks)")
    market_cap: float = Field(..., description="Market capitalization")
    rank: int = Field(..., description="Rank by market cap")
    created_at: Optional[datetime] = None


class IndexPerformance(BaseModel):
    """Model for index performance data."""
    id: Optional[int] = None
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    daily_return: float = Field(..., description="Daily return percentage")
    cumulative_return: float = Field(..., description="Cumulative return percentage")
    index_value: float = Field(..., description="Index value (base 100)")
    created_at: Optional[datetime] = None


class CompositionChange(BaseModel):
    """Model for composition change tracking."""
    id: Optional[int] = None
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    symbol: str = Field(..., description="Stock symbol")
    action: str = Field(..., description="'added' or 'removed'")
    previous_rank: Optional[int] = Field(None, description="Previous rank if removed")
    new_rank: Optional[int] = Field(None, description="New rank if added")
    market_cap: float = Field(..., description="Market capitalization")
    created_at: Optional[datetime] = None


class IndexSummary(BaseModel):
    """Model for index summary data."""
    date: str
    total_stocks: int
    total_market_cap: float
    average_market_cap: float
    min_market_cap: float
    max_market_cap: float
    daily_return: float
    cumulative_return: float 