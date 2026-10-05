from __future__ import annotations

from typing import Any

import cv2

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover
    YOLO = None


class ObjectDetector:
    """Local YOLO-based object detector with cached model loading."""

    def __init__(self, model_name: str = "yolo11n.pt", confidence_threshold: float = 0.5) -> None:
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model: Any | None = None

    def load_model(self) -> Any:
        if self.model is None:
            if YOLO is None:
                raise RuntimeError("Ultralytics is not installed; cannot load the YOLO model.")
            self.model = YOLO(self.model_name)
        return self.model

    def detect(self, frame: Any) -> list[dict[str, Any]]:
        if frame is None:
            return []
        model = self.load_model()
        results = model(frame, conf=self.confidence_threshold, verbose=False)
        return self._format_results(results, model, require_track_ids=False)

    def track(self, frame: Any, tracker_type: str = "bytetrack") -> list[dict[str, Any]]:
        """Return detections carrying IDs assigned by Ultralytics' persistent tracker."""
        if frame is None:
            return []
        model = self.load_model()
        tracker_config = tracker_type if tracker_type.endswith(".yaml") else f"{tracker_type}.yaml"
        results = model.track(
            frame,
            conf=self.confidence_threshold,
            persist=True,
            tracker=tracker_config,
            verbose=False,
        )
        return self._format_results(results, model, require_track_ids=True)

    @staticmethod
    def _format_results(results: Any, model: Any, require_track_ids: bool) -> list[dict[str, Any]]:
        detections: list[dict[str, Any]] = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            names = model.names if hasattr(model, "names") else {}
            for box in boxes:
                track_id = None
                if require_track_ids:
                    box_id = getattr(box, "id", None)
                    if box_id is None:
                        continue
                    track_id = int(box_id[0])
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                cls_id = int(box.cls[0])
                detection = {
                    "class_id": cls_id,
                    "class_name": str(names.get(cls_id, str(cls_id))),
                    "confidence": float(box.conf[0]),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                }
                if track_id is not None:
                    detection["track_id"] = track_id
                detections.append(detection)
        return detections

    def draw_detections(self, frame: Any, detections: list[dict[str, Any]]) -> Any:
        output = frame.copy()
        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{detection['class_name']} {detection['confidence']:.2f}"
            cv2.putText(output, label, (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return output
