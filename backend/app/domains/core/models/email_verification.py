from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.db.base_class import Base


class EmailVerificationCode(Base):
    """
    Stores email verification codes for new user registration.
    Codes expire after 15 minutes and are hashed before storage.
    """
    __tablename__ = "email_verification_codes"
    
    id = Column(String, primary_key=True)  # UUID as string
    email = Column(String, nullable=False, index=True)
    code_hash = Column(String, nullable=False)  # Hashed code, not plaintext
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_email_verification_codes_email_expires', 'email', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<EmailVerificationCode {self.email} expires={self.expires_at}>"
    
    def is_expired(self) -> bool:
        """Check if code has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if code is valid (not used and not expired)."""
        return not self.used and not self.is_expired()
