"""
FastAPI application entry point for Stock Screener Platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import health, ingest, auth
from app.database.session import engine
from app.database.base import Base

# Create FastAPI application
app = FastAPI(
    title="Indian Stock Market Screener API",
    version="1.0.0",
    description="Data aggregation and screening platform for Indian stock markets (NSE)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Data Ingestion"])


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    Creates database tables if they don't exist.
    Note: In Phase 1.1+, this will be replaced by Alembic migrations.
    """
    print(f"Starting Stock Screener API in {settings.ENV} mode...")
    print(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    # Create tables (will be replaced by Alembic in Phase 1.1)
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    print("Shutting down Stock Screener API...")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Indian Stock Market Screener API",
        "version": "1.0.0",
        "environment": settings.ENV,
        "docs": "/docs",
        "health": "/api/v1/health"
    }
