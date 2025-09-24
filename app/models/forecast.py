from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date_range_start = Column(DateTime, nullable=False)
    date_range_end = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="generating")
    optimization_parameters = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    total_schedules_generated = Column(Integer, nullable=False, default=0)

    # Relationships
    schedules = relationship("Schedule", back_populates="forecast", cascade="all, delete-orphan")
    predictions = relationship("PredictionData", back_populates="forecast", cascade="all, delete-orphan")


class PredictionData(Base):
    __tablename__ = "prediction_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(UUID(as_uuid=True), ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False)
    metrics = Column(JSONB, nullable=False)
    confidence_score = Column(Float, nullable=False)
    error_margin = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    forecast = relationship("Forecast", back_populates="predictions")