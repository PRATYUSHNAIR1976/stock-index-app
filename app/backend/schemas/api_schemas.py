from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class BuildIndexRequest(BaseModel):
    """Request schema for building index."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    top_n: int = Field(default=100, description="Number of top stocks to include")


class IndexPerformanceRequest(BaseModel):
    """Request schema for index performance."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class IndexCompositionRequest(BaseModel):
    """Request schema for index composition."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")


class CompositionChangesRequest(BaseModel):
    """Request schema for composition changes."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class ExportDataRequest(BaseModel):
    """Request schema for data export."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    include_performance: bool = Field(default=True, description="Include performance data")
    include_compositions: bool = Field(default=True, description="Include composition data")
    include_changes: bool = Field(default=True, description="Include change data")


class IndexCompositionResponse(BaseModel):
    """Response schema for index composition."""
    date: str
    total_stocks: int
    equal_weight: float
    stocks: List[dict] = Field(..., description="List of stocks with symbol, weight, market_cap, rank")


class IndexPerformanceResponse(BaseModel):
    """Response schema for index performance."""
    start_date: str
    end_date: str
    total_return: float
    daily_returns: List[dict] = Field(..., description="List of daily returns")


class CompositionChangesResponse(BaseModel):
    """Response schema for composition changes."""
    start_date: str
    end_date: str
    total_changes: int
    changes: List[dict] = Field(..., description="List of composition changes")


class ExportDataResponse(BaseModel):
    """Response schema for data export."""
    file_url: str = Field(..., description="URL to download the Excel file")
    file_size: int = Field(..., description="File size in bytes")
    export_date: str = Field(..., description="Export date")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details") 