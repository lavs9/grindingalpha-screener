from sqlalchemy import Column, Date, Float, String
from screener_project.database.db_helper import Base

class IndexBase(Base):
    """
    Base model for all index tables with common fields
    """
    __abstract__ = True

    id = Column(String, primary_key=True)  # Will be a combination of index_name and date
    index_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False) 