from sqlalchemy import Column, String, DateTime, Text, UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class Session(Base):
    """
    NextAuth session storage for database-backed sessions.
    Stores OAuth access tokens server-side to avoid HTTP 431 cookie size errors.
    """
    __tablename__ = "sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email = Column(String, nullable=False, index=True)
    
    # OAuth tokens (can be very large, hence Text type)
    access_token = Column(Text, nullable=False)
    id_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    
    # Session metadata
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Session {self.session_id} for {self.user_email}>"
