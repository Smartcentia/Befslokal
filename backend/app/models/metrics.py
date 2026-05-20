from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
from app.db.base_class import Base

class DashboardMetrics(Base):
    __tablename__ = "dashboard_metrics"

    metric_id = Column(Integer, primary_key=True, index=True)
    properties_count = Column(Integer, default=0)
    contracts_count = Column(Integer, default=0)
    risks_count = Column(Integer, default=0)
    total_annual_rent = Column(Float, default=0.0)
    total_maintenance_cost = Column(Float, default=0.0)
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
