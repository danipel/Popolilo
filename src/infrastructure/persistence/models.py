# Pattern: ORM Model (Mapper a DB)
# UNIQUE constraint previene race conditions en PostgreSQL
# IntegrityError si email ya existe (manejado en Repository)
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index
from src.infrastructure.persistence.database import Base


class UserModel(Base):
    """SQLAlchemy model para tabla users."""

    __tablename__ = "users"

    # Columnas
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"<UserModel(id={self.id}, email={self.email})>"
