from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Optional
import os
from app.backend.schemas.api_schemas import (
    BuildIndexRequest, IndexPerformanceRequest, IndexCompositionRequest,
    CompositionChangesRequest, ExportDataRequest,
    IndexCompositionResponse, IndexPerformanceResponse, 
    CompositionChangesResponse, ExportDataResponse, ErrorResponse
)
from app.backend.services.index_service import IndexService
from app.backend.services.export_service import ExportService

router = APIRouter(prefix="/api/v1", tags=["index"])

# Initialize services
index_service = IndexService()
export_service = ExportService()


@router.post("/build-index", response_model=dict)
async def build_index(request: BuildIndexRequest):
    """
    Build equal-weighted index for the specified date range.
    
    This endpoint constructs the index dynamically at runtime by:
    1. Selecting top N stocks by market cap for each date
    2. Assigning equal weights to each stock
    3. Calculating performance metrics
    4. Detecting composition changes
    """
    try:
        result = index_service.build_index(
            start_date=request.start_date,
            end_date=request.end_date,
            top_n=request.top_n
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building index: {str(e)}")


@router.get("/index-performance")
async def get_index_performance(start_date: str, end_date: str):
    """
    Get index performance for a date range.
    
    Returns daily returns and cumulative returns for the specified period.
    Results are cached for improved performance.
    """
    try:
        result = index_service.get_index_performance(start_date, end_date)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance: {str(e)}")


@router.get("/index-composition")
async def get_index_composition(date: str):
    """
    Get index composition for a specific date.
    
    Returns the 100-stock composition with equal weights for the given date.
    Results are cached for improved performance.
    """
    try:
        result = index_service.get_index_composition(date)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving composition: {str(e)}")


@router.get("/composition-changes")
async def get_composition_changes(start_date: str, end_date: str):
    """
    Get composition changes for a date range.
    
    Returns a list of days when the index composition changed,
    including stocks that were added or removed.
    Results are cached for improved performance.
    """
    try:
        result = index_service.get_composition_changes(start_date, end_date)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving composition changes: {str(e)}")


@router.post("/export-data", response_model=ExportDataResponse)
async def export_data(request: ExportDataRequest):
    """
    Export index data to Excel file.
    
    Creates a comprehensive Excel file with multiple sheets:
    - Performance data
    - Daily compositions
    - Composition changes
    - Summary statistics
    """
    try:
        result = export_service.export_data(
            start_date=request.start_date,
            end_date=request.end_date,
            include_performance=request.include_performance,
            include_compositions=request.include_compositions,
            include_changes=request.include_changes
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ExportDataResponse(
            file_url=result["file_url"],
            file_size=result["file_size"],
            export_date=result["export_date"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Equal-Weighted Index API",
        "version": "1.0.0"
    }


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download exported Excel file."""
    file_path = os.path.join("exports", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ) 