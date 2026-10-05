from __future__ import annotations

import json
from typing import Any

import requests

from app.core.config import settings
from app.core.logging import logger


class ActionDispatcher:
    """Dispatch action handlers for events and alerts."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or settings.webhook_url or settings.alert_webhook_url

    def dispatch(self, event: dict[str, Any]) -> dict[str, Any]:
        results: list[str] = []
        results.append("dashboard_notification")
        results.append("local_log")

        if self.webhook_url:
            try:
                response = requests.post(self.webhook_url, data=json.dumps(event), timeout=5)
                response.raise_for_status()
                results.append("webhook")
            except requests.RequestException as exc:  # pragma: no cover
                logger.warning("Webhook dispatch failed: %s", exc)
                return {"status": "warning", "result": "webhook_failed", "details": str(exc)}

        return {"status": "ok", "actions": results}
