from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.database.database import SessionLocal
from app.database.models import Detection, EventRecord, SystemMetric, ZoneRecord
from app.events.event_engine import EventEngine
from app.vision.camera import CameraError, CameraManager
from app.vision.detector import ObjectDetector
from app.vision.zones import Zone, ZoneManager


class VisionRuntime:
    """Owns the local capture and inference worker used by the API."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._latest_jpeg: bytes | None = None
        self.camera_status = "starting"
        self.camera_error: str | None = None
        self.fps: float | None = None
        self.inference_latency_ms: float | None = None
        self.frame_processing_time_ms: float | None = None
        self.object_count = 0
        self.last_events: list[dict[str, Any]] = []

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="visionops-camera", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def get_jpeg(self) -> bytes | None:
        with self._lock:
            return self._latest_jpeg

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "camera_status": self.camera_status,
                "camera_error": self.camera_error,
                "fps": self.fps,
                "inference_latency_ms": self.inference_latency_ms,
                "frame_processing_time_ms": self.frame_processing_time_ms,
                "object_count": self.object_count,
                "last_events": list(self.last_events),
            }

    def _load_zones(self, db: Session, manager: ZoneManager) -> list[Zone]:
        manager.zones.clear()
        rows = db.query(ZoneRecord).all()
        for row in rows:
            try:
                manager.create_zone(row.id, row.name, row.zone_type, json.loads(row.polygon))
            except (TypeError, ValueError, json.JSONDecodeError):
                logger.warning("Skipping invalid zone configuration: %s", row.id)
        return manager.list_zones()

    def _persist_frame(
        self,
        db: Session,
        tracked_objects: list[dict[str, Any]],
        events: list[dict[str, Any]],
        metrics: dict[str, float],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for tracked in tracked_objects:
            bbox = tracked["bbox"]
            db.add(Detection(
                timestamp=now,
                class_name=str(tracked["class_name"]),
                confidence=float(tracked["confidence"]),
                track_id=int(tracked["track_id"]),
                x1=float(bbox["x1"]),
                y1=float(bbox["y1"]),
                x2=float(bbox["x2"]),
                y2=float(bbox["y2"]),
                metadata_json={},
            ))
        for event in events:
            db.add(EventRecord(
                event_type=str(event["event_type"]),
                timestamp=str(event["timestamp"]),
                object_class=event.get("object_class"),
                track_id=event.get("track_id"),
                zone=event.get("zone_id"),
                confidence=float(event.get("confidence", 0.0)),
                severity=str(event.get("severity", "medium")),
                metadata_json=event.get("metadata", {}),
                duration_seconds=event.get("duration_seconds"),
            ))
        for metric_name, value in metrics.items():
            db.add(SystemMetric(metric_name=metric_name, metric_value=value))
        db.commit()

    def _annotate(
        self,
        frame: np.ndarray,
        tracked_objects: list[dict[str, Any]],
        zones: list[Zone],
    ) -> np.ndarray:
        output = frame
        for zone in zones:
            polygon = np.asarray(zone.polygon, dtype=np.int32)
            if len(polygon) >= 3:
                cv2.polylines(output, [polygon], True, (0, 220, 255), 2)
                cv2.putText(output, zone.name, tuple(polygon[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
        for item in tracked_objects:
            bbox = item["bbox"]
            x1, y1, x2, y2 = (int(bbox[key]) for key in ("x1", "y1", "x2", "y2"))
            cv2.rectangle(output, (x1, y1), (x2, y2), (40, 220, 130), 2)
            label = f"{item['class_name']} #{item['track_id']} {item['confidence']:.2f}"
            cv2.putText(output, label, (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 220, 130), 2)
        return output

    def _run(self) -> None:
        camera = CameraManager(settings.camera_index, settings.frame_width, settings.frame_height)
        detector = ObjectDetector(settings.model_name, settings.confidence_threshold)
        zones = ZoneManager()
        events = EventEngine(zones)
        db = SessionLocal()
        try:
            camera.open()
            detector.load_model()
            with self._lock:
                self.camera_status = "online"
                self.camera_error = None
            last_metrics_at = 0.0
            previous_frame_at: float | None = None
            while not self._stop.is_set():
                frame_started = time.perf_counter()
                frame = camera.read_frame()
                inference_started = time.perf_counter()
                detections = detector.track(frame, settings.tracker_type)
                inference_ms = (time.perf_counter() - inference_started) * 1000
                timestamp = time.time()
                tracked = detections
                current_zones = self._load_zones(db, zones)
                generated_events = events.process(tracked, current_zones)
                annotated = self._annotate(frame, tracked, current_zones)
                encoded, jpeg = cv2.imencode(".jpg", annotated)
                if encoded:
                    with self._lock:
                        self._latest_jpeg = jpeg.tobytes()
                        self.object_count = len(tracked)
                        self.inference_latency_ms = inference_ms
                        self.frame_processing_time_ms = (time.perf_counter() - frame_started) * 1000
                        self.last_events = generated_events
                        self.camera_status = "online"
                        self.camera_error = None
                        if previous_frame_at is not None:
                            elapsed = timestamp - previous_frame_at
                            self.fps = 1.0 / elapsed if elapsed > 0 else None
                    previous_frame_at = timestamp

                now = time.monotonic()
                metrics_to_store: dict[str, float] = {}
                if now - last_metrics_at >= 5:
                    snapshot = self.snapshot()
                    metrics_to_store = {
                        "fps": float(snapshot["fps"] or 0.0),
                        "inference_latency_ms": float(snapshot["inference_latency_ms"] or 0.0),
                        "frame_processing_time_ms": float(snapshot["frame_processing_time_ms"] or 0.0),
                        "detected_object_count": float(snapshot["object_count"]),
                    }
                    last_metrics_at = now
                if tracked or generated_events or metrics_to_store:
                    self._persist_frame(db, tracked, generated_events, metrics_to_store)
        except (CameraError, RuntimeError, OSError) as exc:
            logger.warning("Vision runtime unavailable: %s", exc)
            with self._lock:
                self.camera_status = "offline"
                self.camera_error = str(exc)
        except Exception as exc:  # Keep the API alive if inference fails.
            logger.exception("Vision runtime stopped unexpectedly")
            with self._lock:
                self.camera_status = "error"
                self.camera_error = str(exc)
        finally:
            camera.release()
            db.close()


runtime = VisionRuntime()
