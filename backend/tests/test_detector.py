from app.events.schemas import DetectionSchema
from app.vision.detector import ObjectDetector


def test_detection_schema_validation() -> None:
    payload = {
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.94,
        "bbox": {"x1": 100, "y1": 120, "x2": 300, "y2": 500},
    }
    record = DetectionSchema(**payload)
    assert record.class_name == "person"
    assert record.bbox["x2"] == 300


def test_detector_returns_empty_list_for_none_frame() -> None:
    detector = ObjectDetector(model_name="yolo11n.pt", confidence_threshold=0.5)
    assert detector.detect(None) == []
