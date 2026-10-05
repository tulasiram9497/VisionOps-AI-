from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrackState:
    track_id: int
    class_name: str
    last_bbox: dict[str, float]
    last_seen: float
    age: int = 0
    in_zone: bool = False
    dwell_seconds: float = 0.0
    stationary_seconds: float = 0.0
    metadata: dict[str, float | str] = field(default_factory=dict)


class ObjectTracker:
    """Track objects across frames using center-point matching."""

    def __init__(self, max_age: int = 12, iou_threshold: float = 0.2) -> None:
        self.max_age = max_age
        self.iou_threshold = iou_threshold
        self.tracks: dict[int, TrackState] = {}
        self.next_track_id = 1

    def _center(self, bbox: dict[str, float]) -> tuple[float, float]:
        return ((bbox["x1"] + bbox["x2"]) / 2, (bbox["y1"] + bbox["y2"]) / 2)

    def _distance(self, a: dict[str, float], b: dict[str, float]) -> float:
        ax, ay = self._center(a)
        bx, by = self._center(b)
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def update(self, detections: list[dict[str, object]], now: float) -> list[dict[str, object]]:
        if not detections:
            for track_id in list(self.tracks):
                self.tracks[track_id].age += 1
                if self.tracks[track_id].age > self.max_age:
                    del self.tracks[track_id]
            return []

        active_track_ids = set(self.tracks.keys())
        matched_ids: set[int] = set()
        tracked: list[dict[str, object]] = []

        for detection in detections:
            matching_track_id: int | None = None
            best_distance: float | None = None
            for track_id in active_track_ids:
                if track_id in matched_ids:
                    continue
                previous = self.tracks[track_id]
                current_distance = self._distance(previous.last_bbox, detection["bbox"])
                if best_distance is None or current_distance < best_distance:
                    best_distance = current_distance
                    matching_track_id = track_id

            if matching_track_id is not None and (best_distance is not None and best_distance < 200):
                track = self.tracks[matching_track_id]
                track.last_bbox = detection["bbox"]
                track.last_seen = now
                track.age = 0
                track.class_name = str(detection["class_name"])
                track.dwell_seconds = max(track.dwell_seconds, now - track.last_seen)
                tracked_item = {
                    "track_id": matching_track_id,
                    "class_name": track.class_name,
                    "confidence": float(detection["confidence"]),
                    "bbox": detection["bbox"],
                }
                matched_ids.add(matching_track_id)
                tracked.append(tracked_item)
                continue

            new_track_id = self.next_track_id
            self.next_track_id += 1
            self.tracks[new_track_id] = TrackState(
                track_id=new_track_id,
                class_name=str(detection["class_name"]),
                last_bbox=detection["bbox"],
                last_seen=now,
            )
            tracked.append({
                "track_id": new_track_id,
                "class_name": str(detection["class_name"]),
                "confidence": float(detection["confidence"]),
                "bbox": detection["bbox"],
            })

        for track_id in list(self.tracks):
            if track_id not in matched_ids and track_id in self.tracks:
                self.tracks[track_id].age += 1
                if self.tracks[track_id].age > self.max_age:
                    del self.tracks[track_id]

        return tracked
