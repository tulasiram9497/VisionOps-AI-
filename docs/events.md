# Event system

VisionOps AI produces events from tracked objects and monitoring zones. These events are local-first and stored in SQLite by default.

## Event catalog

- PERSON_ENTERED_ZONE: triggered when an object enters a configured monitoring zone.
- PERSON_LEFT_ZONE: triggered when an object leaves a configured monitoring zone.
- OBJECT_STATIONARY: triggered when the object is largely static for a sustained period.
- UNUSUAL_DWELL_TIME: triggered when dwell time exceeds the configured threshold.
- MULTIPLE_PEOPLE_DETECTED: triggered when the scene exceeds a configurable count threshold.
- CAMERA_OFFLINE: triggered when the video source cannot be read reliably.

## Rules

The platform distinguishes between raw detections and rule-based event generation. The `RuleEngine` applies cooldowns so the dashboard does not spam repeated events.

## Severity levels

- low: informational or exit-based events
- medium: general scene-level conditions
- high: restricted-zone entries and dwell-time anomalies
