from __future__ import annotations

from app.ai.provider import AIProvider, NullAIProvider


class EventSummarizer:
    """Thin wrapper around the configured AI provider."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self.provider = provider or NullAIProvider()

    def summarize_event(self, event: dict[str, object]) -> str:
        return self.provider.summarize_event(event)

    def explain_anomaly(self, anomaly: dict[str, object]) -> str:
        return self.provider.explain_anomaly(anomaly)

    def generate_incident_report(self, events: list[dict[str, object]]) -> str:
        return self.provider.generate_incident_report(events)
