"""
Pending Script Execution Model
Stores script execution requests awaiting admin approval.
"""
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

class PendingScriptExecution(Base):
    __tablename__ = "pending_script_executions"
    
    execution_id = Column(String, primary_key=True)
    script_key = Column(String, nullable=False)
    params = Column(JSON, nullable=True)
    requested_by = Column(String, nullable=False)  # user_id or "ki_kollega"
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending")  # pending, approved, rejected, executed
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    execution_result = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)  # Why was it requested?
