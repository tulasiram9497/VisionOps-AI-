from __future__ import annotations

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.automation.dispatcher import ActionDispatcher
from app.ai.summarizer import EventSummarizer
from app.core.config import settings
from app.database.database import get_db
from app.database.models import Detection, EventRecord, SystemMetric, ZoneRecord
from app.events.schemas import ZoneSchema
from app.vision.runtime import runtime

router = APIRouter()
action_dispatcher = ActionDispatcher(settings.webhook_url)
event_summarizer = EventSummarizer()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/api/system/status")
def system_status(db: Session = Depends(get_db)) -> dict[str, object]:
    runtime_state = runtime.snapshot()
    recent_event_count = db.query(EventRecord).count()
    return {
        "status": "ok",
        "camera_status": runtime_state["camera_status"],
        "camera_error": runtime_state["camera_error"],
        "fps": runtime_state["fps"],
        "inference_latency_ms": runtime_state["inference_latency_ms"],
        "frame_processing_time_ms": runtime_state["frame_processing_time_ms"],
        "object_count": runtime_state["object_count"],
        "event_count": recent_event_count,
        "ai_enabled": settings.enable_ai,
    }


@router.get("/api/detections")
def get_detections(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = db.query(Detection).order_by(Detection.timestamp.desc()).limit(100).all()
    return [
        {
            "id": row.id,
            "timestamp": row.timestamp,
            "class_name": row.class_name,
            "confidence": row.confidence,
            "track_id": row.track_id,
            "bbox": {"x1": row.x1, "y1": row.y1, "x2": row.x2, "y2": row.y2},
        }
        for row in rows
    ]


@router.get("/api/events")
def get_events(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = db.query(EventRecord).order_by(EventRecord.timestamp.desc()).limit(100).all()
    return [
        {
            "id": row.id,
            "event_type": row.event_type,
            "timestamp": row.timestamp,
            "object_class": row.object_class,
            "track_id": row.track_id,
            "zone": row.zone,
            "confidence": row.confidence,
            "severity": row.severity,
            "metadata": row.metadata_json,
            "status": row.status,
            "duration_seconds": row.duration_seconds,
        }
        for row in rows
    ]


@router.get("/api/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.query(EventRecord).filter(EventRecord.id == event_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return {
        "id": row.id,
        "event_type": row.event_type,
        "timestamp": row.timestamp,
        "object_class": row.object_class,
        "track_id": row.track_id,
        "zone": row.zone,
        "confidence": row.confidence,
        "severity": row.severity,
        "metadata": row.metadata_json,
        "status": row.status,
        "duration_seconds": row.duration_seconds,
    }


@router.post("/api/events/{event_id}/acknowledge")
def acknowledge_event(event_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    row = db.query(EventRecord).filter(EventRecord.id == event_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    row.status = "acknowledged"
    db.commit()
    return {"status": "acknowledged", "event_id": str(event_id)}


@router.get("/api/events/{event_id}/summary")
def summarize_event(event_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    row = db.query(EventRecord).filter(EventRecord.id == event_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    event = {
        "event_type": row.event_type,
        "timestamp": row.timestamp,
        "object_class": row.object_class,
        "track_id": row.track_id,
        "zone_id": row.zone,
        "confidence": row.confidence,
        "duration_seconds": row.duration_seconds,
    }
    return {"summary": event_summarizer.summarize_event(event)}


@router.get("/api/zones")
def get_zones(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = db.query(ZoneRecord).all()
    return [{"id": row.id, "name": row.name, "type": row.zone_type, "polygon": json.loads(row.polygon)} for row in rows]


@router.post("/api/zones", status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneSchema, db: Session = Depends(get_db)) -> dict[str, object]:
    if any(len(point) != 2 for point in payload.polygon):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Each polygon point must have two coordinates.")
    if db.query(ZoneRecord).filter(ZoneRecord.id == payload.id).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Zone ID already exists.")
    row = ZoneRecord(id=payload.id, name=payload.name, zone_type=payload.type, polygon=json.dumps(payload.polygon))
    db.add(row)
    db.commit()
    return {"id": row.id, "name": row.name, "type": row.zone_type, "polygon": payload.polygon}


@router.delete("/api/zones/{zone_id}")
def delete_zone(zone_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    row = db.query(ZoneRecord).filter(ZoneRecord.id == zone_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
    db.delete(row)
    db.commit()
    return {"status": "deleted", "zone_id": zone_id}


@router.get("/api/metrics")
def get_metrics(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    rows = db.query(SystemMetric).order_by(SystemMetric.timestamp.desc()).limit(50).all()
    return [
        {"id": row.id, "timestamp": row.timestamp, "metric_name": row.metric_name, "metric_value": row.metric_value, "unit": row.unit}
        for row in rows
    ]


@router.get("/api/video/stream")
async def stream_video() -> StreamingResponse:
    runtime_state = runtime.snapshot()
    if runtime_state["camera_status"] != "online" and runtime.get_jpeg() is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=runtime_state["camera_error"] or "Camera feed is not available.",
        )

    async def generate():
        while True:
            jpeg = runtime.get_jpeg()
            if jpeg is not None:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            state = runtime.snapshot()
            if state["camera_status"] != "online" and jpeg is None:
                break
            await asyncio.sleep(0.1)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.post("/api/actions/dispatch")
def dispatch_action(payload: dict[str, object]) -> dict[str, object]:
    return action_dispatcher.dispatch(payload)


@router.get("/api/health-check")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
