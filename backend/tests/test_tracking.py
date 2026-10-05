from types import SimpleNamespace

from app.vision.detector import ObjectDetector


class FakeBox:
    xyxy = [SimpleNamespace(tolist=lambda: [10.0, 20.0, 50.0, 80.0])]
    cls = [0]
    conf = [0.91]
    id = [17]


class FakeModel:
    names = {0: "person"}

    def __init__(self) -> None:
        self.calls = []

    def track(self, frame, **kwargs):
        self.calls.append(kwargs)
        return [SimpleNamespace(boxes=[FakeBox()])]


def test_tracker_uses_persistent_ids_from_ultralytics() -> None:
    detector = ObjectDetector()
    model = FakeModel()
    detector.model = model

    first = detector.track(object(), "bytetrack")
    second = detector.track(object(), "bytetrack")

    assert first[0]["track_id"] == 17
    assert second[0]["track_id"] == 17
    assert all(call["persist"] is True for call in model.calls)
    assert all(call["tracker"] == "bytetrack.yaml" for call in model.calls)


def test_tracker_omits_detections_without_tracker_ids() -> None:
    detector = ObjectDetector()
    detector.model = FakeModel()
    detector.model.track = lambda frame, **kwargs: [SimpleNamespace(boxes=[SimpleNamespace(**{
        "xyxy": FakeBox.xyxy,
        "cls": [0],
        "conf": [0.91],
        "id": None,
    })])]

    assert detector.track(object()) == []
