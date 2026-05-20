"""
Vedlikeholdsplan – MaintenancePlan + MaintenanceTask

MaintenancePlan:  En gjentagende plan koblet til eiendom og/eller komponent.
MaintenanceTask:  En konkret oppgave generert fra planen (én per intervall).
"""
from sqlalchemy import Column, String, Integer, Boolean, Date, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base


class MaintenancePlan(Base):
    __tablename__ = "maintenance_plans"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    component_id = Column(UUID(as_uuid=True), ForeignKey("building_components.component_id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Kategori: preventive | inspection | cleaning | corrective | legal
    category = Column(String(50), default="preventive")

    # Frekvens i måneder: 1=månedlig, 3=kvartalsvis, 6=halvårlig, 12=årlig, 24=hvert 2. år
    frequency_months = Column(Integer, nullable=False, default=12)

    # Hvem utfører: janitor | contractor | property_manager
    responsible_role = Column(String(50), default="janitor")

    # Estimert kostnad (NOK)
    estimated_cost_nok = Column(Numeric(10, 2), nullable=True)

    # NS 3451 kode (valgfritt – for gruppering)
    ns3451_code = Column(String(20), nullable=True)

    # Dato for sist utførelse → beregn next_due_date
    last_performed_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tasks = relationship("MaintenanceTask", back_populates="plan", cascade="all, delete-orphan")


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("maintenance_plans.plan_id"), nullable=False, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    component_id = Column(UUID(as_uuid=True), ForeignKey("building_components.component_id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    due_date = Column(Date, nullable=False, index=True)

    # Status: pending | in_progress | completed | overdue | cancelled | skipped
    status = Column(String(30), default="pending", nullable=False)

    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)
    actual_cost_nok = Column(Numeric(10, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    plan = relationship("MaintenancePlan", back_populates="tasks")
