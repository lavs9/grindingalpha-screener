from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from urllib.parse import quote_plus

# Database configuration
DB_USER = "postgres"
DB_PASSWORD = "Password@123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "screener_db"

# Create the database URL with properly encoded password
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Usage:
        with get_db_context() as db:
            # do something with db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables.
    Call this function when the application starts.
    """
    Base.metadata.create_all(bind=engine) 