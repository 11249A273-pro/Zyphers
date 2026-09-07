import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        print(f"[DB] Connected to PostgreSQL database.")
    except Exception as e:
        print(f"[WARN] Failed to create database engine: {e}")
        engine = None

if engine is None:
    fallback_db_path = os.path.join(BASE_DIR, "polar_fallback.db")
    engine = create_engine(f"sqlite:///{fallback_db_path}")
    print(f"[DB] Using SQLite fallback at {fallback_db_path}")

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)
    solar_kw = Column(Float)
    wind_kw = Column(Float)
    demand_kw = Column(Float)
    battery_percent = Column(Float)
    fuel_liters = Column(Float)
    temperature_c = Column(Float)
    weather = Column(String)
    scenario = Column(String)
    device_id = Column(String, default="simulation")  # NEW: identifies hardware source

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # "admin" | "operator"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)