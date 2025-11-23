"""
Event-based data models for market events (Bulk Deals, Block Deals, Surveillance).

NOTE: These models will be refined in Phase 1.2 when actual NSE CSV files are processed.
Field names should match exact CSV column headers from NSE archives.
"""
from sqlalchemy import Column, BigInteger, String, Date, Numeric, DateTime, Index
from sqlalchemy.sql import func
from app.database.base import Base


class BulkDeal(Base):
    """
    Bulk deals transactions (trades exceeding 0.5% of equity).

    Data Source: NSE bulk.csv (https://nsearchives.nseindia.com/content/equities/bulk.csv)

    Schema Status: BASELINE - Will verify with actual NSE CSV format in Phase 1.2

    Note: Bulk deals indicate significant institutional or large investor activity
    """
    __tablename__ = 'bulk_deals'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True,
                 comment="Deal execution date")
    symbol = Column(String(50), nullable=False, index=True,
                   comment="Security symbol")
    security_name = Column(String(255), comment="Security name from CSV")
    client_name = Column(String(255), nullable=False,
                        comment="Name of client/institution")
    deal_type = Column(String(10), comment="BUY or SELL")
    quantity = Column(BigInteger, nullable=False,
                     comment="Number of shares traded")
    price = Column(Numeric(15, 2), nullable=False,
                  comment="Trade execution price per share")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_bulk_deals_date_symbol', 'date', 'symbol'),
        Index('idx_bulk_deals_client', 'client_name'),
    )

    def __repr__(self):
        return f"<BulkDeal(symbol='{self.symbol}', date='{self.date}', type='{self.deal_type}', client='{self.client_name}')>"


class BlockDeal(Base):
    """
    Block deals transactions (large off-market trades).

    Data Source: NSE block.csv (https://nsearchives.nseindia.com/content/equities/block.csv)

    Schema Status: BASELINE - Will verify with actual NSE CSV format in Phase 1.2

    Note: Block deals are large institutional trades executed outside normal market hours
    Typically indicate significant portfolio rebalancing or stake transfers
    """
    __tablename__ = 'block_deals'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True,
                 comment="Deal execution date")
    symbol = Column(String(50), nullable=False, index=True,
                   comment="Security symbol")
    security_name = Column(String(255), comment="Security name from CSV")
    client_name = Column(String(255), nullable=False,
                        comment="Name of client/institution")
    deal_type = Column(String(10), comment="BUY or SELL")
    quantity = Column(BigInteger, nullable=False,
                     comment="Number of shares traded")
    price = Column(Numeric(15, 2), nullable=False,
                  comment="Trade execution price per share")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_block_deals_date_symbol', 'date', 'symbol'),
        Index('idx_block_deals_client', 'client_name'),
    )

    def __repr__(self):
        return f"<BlockDeal(symbol='{self.symbol}', date='{self.date}', type='{self.deal_type}', client='{self.client_name}')>"


class SurveillanceMeasure(Base):
    """
    Securities under regulatory surveillance or Additional Surveillance Mechanism (ASM).

    Data Source: NSE REG1_IND*.csv files (surveillance measures)

    Schema Status: BASELINE - Will verify with actual NSE CSV format in Phase 1.2

    Note: ASM framework is used by NSE to monitor securities with abnormal price movements
    Being on this list indicates heightened regulatory scrutiny
    """
    __tablename__ = 'surveillance_measures'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True,
                 comment="Date surveillance measure was reported")
    symbol = Column(String(50), nullable=False, index=True,
                   comment="Security symbol under surveillance")
    security_name = Column(String(255), comment="Security name from CSV")
    measure_type = Column(String(100), comment="Type of measure (e.g., 'ASM Stage 1', 'GSM', 'Short Term ASM')")
    reason = Column(String(500), comment="Reason for surveillance (if provided in CSV)")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_surveillance_date_symbol', 'date', 'symbol'),
        Index('idx_surveillance_measure_type', 'measure_type'),
    )

    def __repr__(self):
        return f"<SurveillanceMeasure(symbol='{self.symbol}', date='{self.date}', type='{self.measure_type}')>"
