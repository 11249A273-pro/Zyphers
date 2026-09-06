import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
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

def init_db():
    Base.metadata.create_all(bind=engine)