# Vision Pipeline

## Camera

Camera capture is implemented through a local abstraction that reads frames from a webcam index, a video file, or an optional stream. The system is designed to process in local devices only.

## Detection

YOLO performs object detection. Each bounding box is converted into a standard schema including class name, confidence score, and coordinates.

## Tracking

Detections are associated across frames using center-based matching. Each object receives a persistent track ID until it is no longer observed for a configured timeout period.

## Events

The event engine checks whether a tracked object has entered a zone, left a zone, dwelled too long, or triggered a count threshold. These events are stored in SQLite and surfaced via the API.
