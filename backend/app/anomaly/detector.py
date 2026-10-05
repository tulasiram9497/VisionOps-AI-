from __future__ import annotations

from typing import Any


class AnomalyDetector:
    """Baseline anomaly detector using explainable statistical rules."""

    def __init__(self, max_object_count: int = 4, dwell_threshold_seconds: int = 12) -> None:
        self.max_object_count = max_object_count
        self.dwell_threshold_seconds = dwell_threshold_seconds

    def detect(self, tracked_objects: list[dict[str, Any]], events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        event_list = events or []
        object_count = len(tracked_objects)
        dwell_events = [event for event in event_list if event.get("event_type") == "UNUSUAL_DWELL_TIME"]

        if object_count > self.max_object_count:
            return {
                "is_anomaly": True,
                "score": min(0.99, 0.4 + (object_count - self.max_object_count) * 0.15),
                "reason": "Object count exceeded the configured baseline threshold for the scene.",
            }

        if dwell_events:
            return {
                "is_anomaly": True,
                "score": 0.82,
                "reason": "Object remained in a monitored zone longer than the configured threshold.",
            }

        if object_count == 0:
            return {
                "is_anomaly": False,
                "score": 0.0,
                "reason": "No unusual activity detected.",
            }

        return {
            "is_anomaly": False,
            "score": 0.12,
            "reason": "No baseline anomaly conditions were triggered.",
        }
