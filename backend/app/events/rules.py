from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EventRule:
    name: str
    event_type: str
    severity: str = "medium"
    cooldown_seconds: float = 30.0
    description: str = ""


class RuleEngine:
    """Simple rule-driven event system for local-first monitoring."""

    def __init__(self) -> None:
        self.rules = [
            EventRule("restricted area entry", "PERSON_ENTERED_ZONE", "high", 15.0, "Object entered a restricted zone."),
            EventRule("restricted area exit", "PERSON_LEFT_ZONE", "low", 15.0, "Object left a monitored zone."),
            EventRule("unusual dwell", "UNUSUAL_DWELL_TIME", "high", 30.0, "An object remained in a restricted area longer than expected."),
            EventRule("stationary object", "OBJECT_STATIONARY", "medium", 20.0, "Object motion is below threshold for a sustained period."),
            EventRule("crowding", "MULTIPLE_PEOPLE_DETECTED", "medium", 30.0, "More than one object was observed in the scene."),
            EventRule("camera offline", "CAMERA_OFFLINE", "high", 60.0, "Camera feed could not be read."),
        ]
        self.last_event_times: dict[str, float] = {}

    def should_fire(self, event_type: str, now: float, subject_key: str | None = None) -> bool:
        cooldown_key = f"{event_type}:{subject_key}" if subject_key else event_type
        last_time = self.last_event_times.get(cooldown_key)
        rule = next((item for item in self.rules if item.event_type == event_type), None)
        if rule is None:
            return True
        if last_time is None:
            return True
        return (now - last_time) >= rule.cooldown_seconds

    def register_event(self, event_type: str, now: float, subject_key: str | None = None) -> None:
        cooldown_key = f"{event_type}:{subject_key}" if subject_key else event_type
        self.last_event_times[cooldown_key] = now
