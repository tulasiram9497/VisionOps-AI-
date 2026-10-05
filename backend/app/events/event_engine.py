from __future__ import annotations

from datetime import datetime, timezone

from app.events.rules import RuleEngine
from app.vision.zones import Zone, ZoneManager


class EventEngine:
    """Transforms tracked objects and zones into structured events."""

    def __init__(self, zone_manager: ZoneManager | None = None, rule_engine: RuleEngine | None = None) -> None:
        self.zone_manager = zone_manager or ZoneManager()
        self.rule_engine = rule_engine or RuleEngine()
        self.track_state: dict[int, dict[str, object]] = {}

    def _now(self) -> float:
        return datetime.now(timezone.utc).timestamp()

    def process(self, tracked_objects: list[dict[str, object]], zones: list[Zone] | None = None) -> list[dict[str, object]]:
        zones = zones or self.zone_manager.list_zones()
        now = self._now()
        events: list[dict[str, object]] = []

        if not tracked_objects and not zones:
            return events

        people_count = sum(str(item.get("class_name", "")).lower() == "person" for item in tracked_objects)
        if people_count >= 2:
            event_type = "MULTIPLE_PEOPLE_DETECTED"
            if self.rule_engine.should_fire(event_type, now):
                events.append({
                    "event_type": event_type,
                    "track_id": None,
                    "zone_id": None,
                    "confidence": 0.8,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "severity": "medium",
                    "object_class": "scene",
                    "metadata": {"object_count": people_count},
                })
                self.rule_engine.register_event(event_type, now)

        for object_info in tracked_objects:
            track_id = int(object_info["track_id"])
            bbox = object_info["bbox"]
            zone_hits = []
            for zone in zones:
                if self.zone_manager.is_object_in_zone(bbox, zone):
                    zone_hits.append(zone)

            previous_state = self.track_state.get(track_id, {"inside_zone": False, "entered_at": now, "last_seen": now, "duration": 0.0})
            inside_zone = bool(zone_hits)
            entered_zone = inside_zone and not bool(previous_state.get("inside_zone"))
            left_zone = (not inside_zone) and bool(previous_state.get("inside_zone"))
            center = ((float(bbox["x1"]) + float(bbox["x2"])) / 2, (float(bbox["y1"]) + float(bbox["y2"])) / 2)
            previous_center = previous_state.get("center")
            if previous_center is None:
                stationary_since = now
            else:
                distance = ((center[0] - float(previous_center[0])) ** 2 + (center[1] - float(previous_center[1])) ** 2) ** 0.5
                stationary_since = float(previous_state.get("stationary_since", now)) if distance <= 5 else now
            stationary_seconds = now - stationary_since

            if entered_zone:
                for zone in zone_hits:
                    event_type = "PERSON_ENTERED_ZONE"
                    subject_key = f"{track_id}:{zone.id}"
                    if str(object_info["class_name"]).lower() == "person" and self.rule_engine.should_fire(event_type, now, subject_key):
                        events.append({
                            "event_type": event_type,
                            "track_id": track_id,
                            "zone_id": zone.id,
                            "confidence": float(object_info["confidence"]),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "severity": "high",
                            "object_class": str(object_info["class_name"]),
                            "metadata": {"zone_name": zone.name, "bbox": bbox},
                        })
                        self.rule_engine.register_event(event_type, now, subject_key)

            if left_zone:
                event_type = "PERSON_LEFT_ZONE"
                subject_key = f"{track_id}:{previous_state.get('zone_id')}"
                if str(object_info["class_name"]).lower() == "person" and self.rule_engine.should_fire(event_type, now, subject_key):
                    events.append({
                        "event_type": event_type,
                        "track_id": track_id,
                        "zone_id": previous_state.get("zone_id"),
                        "confidence": float(object_info["confidence"]),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "severity": "low",
                        "object_class": str(object_info["class_name"]),
                        "metadata": {"bbox": bbox},
                    })
                    self.rule_engine.register_event(event_type, now, subject_key)

            dwell_seconds = (now - float(previous_state.get("entered_at", now))) if inside_zone else 0.0
            if inside_zone and dwell_seconds > 12:
                event_type = "UNUSUAL_DWELL_TIME"
                subject_key = f"{track_id}:{zone_hits[0].id}"
                if self.rule_engine.should_fire(event_type, now, subject_key):
                    events.append({
                        "event_type": event_type,
                        "track_id": track_id,
                        "zone_id": zone_hits[0].id if zone_hits else None,
                        "confidence": float(object_info["confidence"]),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "severity": "high",
                        "object_class": str(object_info["class_name"]),
                        "duration_seconds": dwell_seconds,
                        "metadata": {"zone_name": zone_hits[0].name if zone_hits else "unknown"},
                    })
                    self.rule_engine.register_event(event_type, now, subject_key)

            if stationary_seconds > 15:
                event_type = "OBJECT_STATIONARY"
                subject_key = str(track_id)
                if self.rule_engine.should_fire(event_type, now, subject_key):
                    events.append({
                        "event_type": event_type,
                        "track_id": track_id,
                        "zone_id": zone_hits[0].id if zone_hits else None,
                        "confidence": float(object_info["confidence"]),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "severity": "medium",
                        "object_class": str(object_info["class_name"]),
                        "duration_seconds": stationary_seconds,
                        "metadata": {"movement_threshold_pixels": 5},
                    })
                    self.rule_engine.register_event(event_type, now, subject_key)

            self.track_state[track_id] = {
                "inside_zone": inside_zone,
                "entered_at": previous_state.get("entered_at", now) if inside_zone else now,
                "last_seen": now,
                "duration": dwell_seconds,
                "zone_id": zone_hits[0].id if zone_hits else None,
                "center": center,
                "stationary_since": stationary_since,
            }

        return events
