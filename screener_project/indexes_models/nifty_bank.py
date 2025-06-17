from sqlalchemy import Column, String
from .base_model import IndexBase

class NiftyBank(IndexBase):
    """
    Model for Nifty Bank index data
    """
    __tablename__ = "nifty_bank"

    def __init__(self, index_name: str, date: str, open: float, high: float, low: float, close: float):
        formatted_index = index_name.lower().replace(" ", "_")
        formatted_date = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else date
        self.id = f"{formatted_index}_{formatted_date}"
        self.index_name = index_name
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close 