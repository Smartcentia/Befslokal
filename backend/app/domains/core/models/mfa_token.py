from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid
from app.db.base_class import Base


class MFAToken(Base):
    """
    Stores MFA tokens for multi-factor authentication.
    Tokens expire after 10 minutes and are one-time use.
    """
    __tablename__ = "mfa_tokens"
    
    token = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_email = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_mfa_tokens_user_email_expires', 'user_email', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<MFAToken {self.token[:8]}... for {self.user_email} expires={self.expires_at}>"
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired()
