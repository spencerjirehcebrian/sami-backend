from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movies.id"), nullable=False)
    cinema_id = Column(UUID(as_uuid=True), ForeignKey("cinemas.id"), nullable=False)
    time_slot = Column(DateTime, nullable=False)
    unit_price = Column(Float, nullable=False)
    service_fee = Column(Float, nullable=False)
    max_sales = Column(Integer, nullable=False)
    current_sales = Column(Integer, default=0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    movie = relationship("Movie")
    cinema = relationship("Cinema", back_populates="schedules")