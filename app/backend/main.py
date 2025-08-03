"""
Main FastAPI application for the Stock Index Service.

This module sets up the FastAPI application with:
- API documentation and metadata
- CORS middleware for cross-origin requests
- Router registration for all API endpoints
- Health check endpoints
- Error handling and logging

The application provides RESTful APIs for:
- Building equal-weighted stock indices
- Retrieving index compositions and performance
- Detecting composition changes
- Exporting data to Excel files
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.backend.utils.redis_client import health_check
from app.backend.routers.index_routes import router as index_router
import os

# Create FastAPI application instance with metadata
app = FastAPI(
    title="Equal-Weighted Index Service",
    description="""
    Backend service for tracking and managing a custom equal-weighted stock index.
    
    This service provides APIs to:
    - Build equal-weighted indices from top stocks by market cap
    - Retrieve historical index compositions and performance
    - Detect and track composition changes over time
    - Export comprehensive data to Excel files
    
    The service uses DuckDB for data storage and Redis for caching.
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI documentation
    redoc_url="/redoc"  # ReDoc documentation
)

# Add CORS middleware to allow cross-origin requests
# This is useful for frontend applications that need to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the main API router with all index-related endpoints
# The router is prefixed with /api/v1 and includes all CRUD operations
app.include_router(index_router)

@app.get("/")
async def root():
    """
    Root endpoint providing basic API information.
    
    This endpoint serves as the entry point and provides:
    - Service name and version
    - Links to documentation
    - Health check endpoint
    
    Returns:
        dict: Basic API information and available endpoints
    """
    return {
        "message": "Equal-Weighted Index Service",
        "version": "1.0.0",
        "docs": "/docs",  # Swagger UI
        "health": "/health"  # Health check endpoint
    }

@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring and load balancers.
    
    This endpoint checks the health of various service components:
    - Redis connection status
    - Overall service status
    
    Returns:
        dict: Health status of the service and its dependencies
    """
    # Check Redis connection health
    redis_status = health_check()
    
    return {
        "status": "ok",
        "redis": redis_status,
        "service": "Equal-Weighted Index API"
    }
