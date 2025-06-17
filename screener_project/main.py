from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database.db_helper import init_db
from .data_ingester import ingest_index_data
from typing import Dict

from .return_calculator.returns import calculate_return


app = FastAPI(title="First Screener API")

class HealthResponse(BaseModel):
    status: str
    message: str

class IngestRequest(BaseModel):
    index_name: str
    csv_path: str

class ReturnResponse(BaseModel):
    success: bool
    timeframe: str
    return_: float | None = None 
    message: str



@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup
    """
    init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to First Screener API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="Service is running normally"
    )

@app.post("/ingest", response_model=Dict)
async def ingest_data(request: IngestRequest):
    """
    Ingest index data from CSV file
    """
    result = ingest_index_data(
        index_name=request.index_name,
        csv_path=request.csv_path
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )
    
    return result

 
@app.get("/returns/{index_name}/{timeframe}", response_model=ReturnResponse)
async def get_index_return(index_name: str, timeframe: str):
    """Calculate and return index returns for the specified timeframe"""
    result = calculate_return(index_name=index_name, timeframe=timeframe)
    
    return ReturnResponse(
        success=result["success"],
        timeframe=result["timeframe"],
        return_=result["return"],
        message=result["message"],
    )
