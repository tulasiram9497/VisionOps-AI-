from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DetectionSchema(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: dict[str, float]


class TrackedDetectionSchema(BaseModel):
    track_id: int
    class_name: str
    confidence: float
    bbox: dict[str, float]


class EventSchema(BaseModel):
    event_type: str
    track_id: int | None = None
    zone_id: str | None = None
    confidence: float = 0.0
    timestamp: str
    severity: str = "medium"
    object_class: str | None = None
    duration_seconds: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ZoneSchema(BaseModel):
    id: str
    name: str
    type: str = "restricted"
    polygon: list[list[int]] = Field(min_length=3)
