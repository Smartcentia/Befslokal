from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class Sensor(Base):
    """
    Represents a physical IoT device or virtual sensor info.
    """
    __tablename__ = "sensors"

    sensor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String(50), nullable=False) # e.g. "temperature", "humidity", "water_leak", "energy"
    location = Column(String, nullable=True)
    status = Column(String(20), default="active") # active, offline, maintenance
    config = Column(JSON, default={}) # threshold settings, polling info
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SensorReading(Base):
    """
    Time-series data from sensors.
    """
    __tablename__ = "sensor_readings"

    reading_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.sensor_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True) # e.g. "C", "%", "kWh"
    raw_data = Column(JSON, nullable=True)

class Anomaly(Base):
    """
    Detected anomalies from sensor data.
    """
    __tablename__ = "sensor_anomalies"

    anomaly_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.sensor_id"), nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String, nullable=False)
    severity = Column(String(20), default="medium") # low, medium, high, critical
    status = Column(String(20), default="open") # open, investigating, resolved
    resolution = Column(String, nullable=True)
