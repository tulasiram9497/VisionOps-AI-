# API reference

The backend exposes a FastAPI service with OpenAPI docs at http://localhost:8000/docs.

## Endpoints

- GET /health
- GET /api/system/status
- GET /api/detections
- GET /api/events
- GET /api/events/{event_id}
- POST /api/events/{event_id}/acknowledge
- GET /api/zones
- POST /api/zones
- DELETE /api/zones/{zone_id}
- GET /api/metrics
- GET /api/video/stream

## Example response

```json
{
  "status": "ok",
  "camera_status": "online",
  "fps": 15,
  "inference_latency_ms": 120,
  "object_count": 3,
  "event_count": 8
}
```
