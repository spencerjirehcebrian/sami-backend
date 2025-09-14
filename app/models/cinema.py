from sqlalchemy import Column, String, Integer, Float, ARRAY, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class CinemaType(Base):
    __tablename__ = "cinema_types"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price_multiplier = Column(Float, nullable=False)


class Cinema(Base):
    __tablename__ = "cinemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(Integer, unique=True, nullable=False)
    type = Column(String, ForeignKey("cinema_types.id"), nullable=False)
    total_seats = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    features = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cinema_type = relationship("CinemaType")
    schedules = relationship("Schedule", back_populates="cinema")