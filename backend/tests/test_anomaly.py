from app.anomaly.detector import AnomalyDetector


def test_anomaly_detector_flags_unusual_density() -> None:
    detector = AnomalyDetector(max_object_count=3)
    tracked_objects = [{"track_id": i, "class_name": "person", "confidence": 0.92, "bbox": {"x1": 10 * i, "y1": 10, "x2": 30 + 10 * i, "y2": 60}} for i in range(5)]
    anomaly = detector.detect(tracked_objects)
    assert anomaly["is_anomaly"] is True
    assert anomaly["score"] > 0.0
