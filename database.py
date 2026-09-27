"""
Database module for Industrial AI - Quotation Intelligence.
Handles SQLite database operations using SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(String(50), unique=True, nullable=False, index=True)
    image_name = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    frame_number = Column(String(255), nullable=True)
    equipment_type = Column(String(255), nullable=True)
    power = Column(String(100), nullable=True)
    voltage = Column(String(100), nullable=True)
    current = Column(String(100), nullable=True)
    rpm = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    power_factor = Column(String(100), nullable=True)
    phase = Column(String(50), nullable=True)
    duty = Column(String(100), nullable=True)
    insulation_class = Column(String(50), nullable=True)
    connection = Column(String(100), nullable=True)
    bearing_number = Column(String(100), nullable=True)
    cooling = Column(String(100), nullable=True)
    protection = Column(String(100), nullable=True)
    weight = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    manufacturer_address = Column(String(500), nullable=True)
    status = Column(String(50), default="Processing")
    extracted_data = Column(Text, nullable=True)
    engineering_data = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quotation_number = Column(String(50), unique=True, nullable=False, index=True)
    inventory_id = Column(String(50), nullable=False, index=True)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    subtotal = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    cost_breakdown = Column(Text, nullable=True)
    engineering_details = Column(Text, nullable=True)
    motor_details = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    status = Column(String(50), default="Generated")
    created_date = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a direct database session (non-generator)."""
    return SessionLocal()


def generate_inventory_id(db):
    """Generate unique inventory ID in format INV-YYYYMMDD-0001."""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"INV-{today}-"

    last_record = (
        db.query(Inventory)
        .filter(Inventory.inventory_id.like(f"{prefix}%"))
        .order_by(Inventory.inventory_id.desc())
        .first()
    )

    if last_record:
        last_num = int(last_record.inventory_id.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}{new_num:04d}"


def generate_quotation_number(db):
    """Generate unique quotation number in format QT-YYYYMMDD-0001."""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"QT-{today}-"

    last_record = (
        db.query(Quotation)
        .filter(Quotation.quotation_number.like(f"{prefix}%"))
        .order_by(Quotation.quotation_number.desc())
        .first()
    )

    if last_record:
        last_num = int(last_record.quotation_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}{new_num:04d}"
