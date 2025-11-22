"""
Health check and status endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.session import check_db_connection
from app.core.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check with database status."""
    status: str
    environment: str
    database_connected: bool
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        HealthResponse: Service status
    """
    return HealthResponse(
        status="healthy",
        message="Stock Screener API is running",
        environment=settings.ENV
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check including database connectivity.

    Returns:
        DetailedHealthResponse: Detailed service status

    Raises:
        HTTPException: If critical services are down
    """
    db_connected = check_db_connection()

    if not db_connected:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

    return DetailedHealthResponse(
        status="healthy",
        environment=settings.ENV,
        database_connected=db_connected,
        message="All services are operational"
    )
