# First Screener API

A FastAPI-based API service.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

To run the application, use the following command:
```bash
uvicorn main:app --reload
```

The API will be available at:
- Main API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Documentation: http://localhost:8000/redoc

## Available Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check endpoint 