from __future__ import annotations

import time

import cv2

from app.core.config import settings
from app.vision.camera import CameraManager
from app.vision.detector import ObjectDetector
from app.vision.tracker import ObjectTracker
from app.vision.zones import ZoneManager


def main() -> None:
    camera = CameraManager(source=settings.camera_index, width=settings.frame_width, height=settings.frame_height)
    detector = ObjectDetector(model_name=settings.model_name, confidence_threshold=settings.confidence_threshold)
    tracker = ObjectTracker()
    zones = ZoneManager()
    zones.create_zone("restricted-zone", "Restricted Area", "restricted", [[100, 100], [500, 100], [500, 400], [100, 400]])

    camera.open()
    while True:
        try:
            frame = camera.read_frame()
        except RuntimeError:
            print("Camera unavailable. Exiting.")
            break

        detections = detector.detect(frame)
        tracked = tracker.update(detections, time.time())
        for current in tracked:
            bbox = current["bbox"]
            for zone in zones.list_zones():
                if zones.is_object_in_zone(bbox, zone):
                    print(f"Track {current['track_id']} in {zone.name}")

        display = detector.draw_detections(frame, detections)
        cv2.imshow("VisionOps AI", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
