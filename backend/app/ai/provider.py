from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Provider-agnostic interface for optional LLM-based reasoning."""

    @abstractmethod
    def summarize_event(self, event: dict[str, object]) -> str:
        raise NotImplementedError

    @abstractmethod
    def explain_anomaly(self, anomaly: dict[str, object]) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_incident_report(self, events: list[dict[str, object]]) -> str:
        raise NotImplementedError


class NullAIProvider(AIProvider):
    """Default provider used when no external LLM has been configured."""

    def summarize_event(self, event: dict[str, object]) -> str:
        object_label = event.get("object_class") or "object"
        zone = event.get("zone_id") or "monitored area"
        duration = event.get("duration_seconds")
        duration_text = f" for approximately {duration} seconds" if duration is not None else ""
        return (
            f"Observed fact: {object_label} was associated with {zone}{duration_text}. "
            f"Interpretation: the rule engine classified the event as {event.get('event_type', 'unknown')} "
            f"based on configured local thresholds."
        )

    def explain_anomaly(self, anomaly: dict[str, object]) -> str:
        return f"Observed fact: {anomaly.get('reason', 'No anomaly reason available')}. Interpretation: this result is based on local statistical thresholds, not an external model."

    def generate_incident_report(self, events: list[dict[str, object]]) -> str:
        if not events:
            return "No events available. The system observed no incidents during this reporting period."
        first = events[0]
        return f"Incident summary: {len(events)} event(s) were recorded, including {first.get('event_type', 'unknown')} at {first.get('timestamp', 'unknown time')}."
