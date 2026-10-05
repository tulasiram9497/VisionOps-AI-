from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat(), index=True)
    class_name: Mapped[str] = mapped_column(String, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    x1: Mapped[float] = mapped_column(Float, default=0.0)
    y1: Mapped[float] = mapped_column(Float, default=0.0)
    x2: Mapped[float] = mapped_column(Float, default=0.0)
    y2: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("details", JSON, default=dict, nullable=True)


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat(), index=True)
    object_class: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    zone: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String, default="medium")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("details", JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String, default="new")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)


class ZoneRecord(Base):
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    zone_type: Mapped[str] = mapped_column(String, default="restricted")
    polygon: Mapped[str] = mapped_column(Text)


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat(), index=True)
    metric_name: Mapped[str] = mapped_column(String, index=True)
    metric_value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("details", JSON, default=dict, nullable=True)
