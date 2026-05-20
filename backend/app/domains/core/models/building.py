"""
Building, Floor, Space – hierarki under Property

Property → Building → Floor → Unit (og Space)
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base


class Building(Base):
    __tablename__ = "buildings"

    building_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    name = Column(String, nullable=False)               # "Bygg A", "Hovedbygg"
    building_code = Column(String(20), nullable=True)   # "A", "B1"
    year_built = Column(Integer, nullable=True)
    building_type = Column(String(50), default="main")  # main, annex, garage
    floors_above_ground = Column(Integer, default=1)
    floors_below_ground = Column(Integer, default=0)
    total_area_sqm = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    floors = relationship(
        "Floor",
        back_populates="building",
        cascade="all, delete-orphan",
        order_by="Floor.floor_number",
    )


class Floor(Base):
    __tablename__ = "floors"

    floor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.building_id"), nullable=False, index=True)
    floor_number = Column(Integer, nullable=False)  # -1=kjeller, 0=bakkeplan, 1=1.etasje
    name = Column(String, nullable=True)            # "Kjeller", "1. etasje"
    area_sqm = Column(Float, nullable=True)

    # Relationships
    building = relationship("Building", back_populates="floors")
    spaces = relationship("Space", back_populates="floor", cascade="all, delete-orphan")


class Space(Base):
    __tablename__ = "spaces"

    space_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id = Column(UUID(as_uuid=True), ForeignKey("floors.floor_id"), nullable=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.unit_id"), nullable=True)
    name = Column(String, nullable=False)            # "Rom 101", "Kjøkken"
    space_type = Column(String(50), default="room")  # room, office, kitchen, bathroom, corridor, storage
    area_sqm = Column(Float, nullable=True)
    description = Column(String, nullable=True)

    # Relationships
    floor = relationship("Floor", back_populates="spaces")
