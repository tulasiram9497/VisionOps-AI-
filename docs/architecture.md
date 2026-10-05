# Architecture

VisionOps AI follows a layered design: input capture, detection, tracking, event logic, anomaly detection, automation, and presentation.

## Components

- Camera manager: captures frames from local webcams or video files.
- Object detector: runs YOLO inference locally.
- Object tracker: assigns persistent IDs across frames.
- Zone manager: determines whether a detection center sits inside a polygon.
- Event engine: converts discrete detections into structured events.
- Anomaly detector: scores unusual patterns using explainable rules.
- AI provider: optional summarization layer for incident reporting.
- Automation dispatch: emits notifications and webhooks.
- Database: persists detections, metrics, events, and zones.
- API: exposes status and operational data.
- Frontend dashboard: renders live and historical monitoring data.

## Data flow

1. The camera captures frames.
2. The detector identifies objects and scores them.
3. The tracker associates objects across frames.
4. The zone manager checks object centers against configured polygons.
5. The event engine raises actionable events.
6. The anomaly module scores unusual behavior.
7. The database stores events and metrics.
8. The REST API exposes the data to the dashboard and operators.

## Deployment

The project is designed for local-first processing. Databases and model inference remain local unless the operator enables optional external AI integrations.
