from app.events.event_engine import EventEngine
from app.vision.zones import ZoneManager


def test_event_engine_generates_enter_and_dwell_events() -> None:
    zone_manager = ZoneManager()
    zone_manager.create_zone("restricted-zone", "Restricted Area", "restricted", [[100, 100], [500, 100], [500, 400], [100, 400]])
    event_engine = EventEngine(zone_manager=zone_manager)
    current_time = 1000.0
    event_engine._now = lambda: current_time

    tracked_objects = [{
        "track_id": 7,
        "class_name": "person",
        "confidence": 0.93,
        "bbox": {"x1": 200, "y1": 200, "x2": 260, "y2": 280},
    }]

    events = event_engine.process(tracked_objects, zone_manager.list_zones())
    assert any(event["event_type"] == "PERSON_ENTERED_ZONE" for event in events)

    current_time += 13
    events = event_engine.process(tracked_objects, zone_manager.list_zones())
    dwell_event = next(event for event in events if event["event_type"] == "UNUSUAL_DWELL_TIME")
    assert dwell_event["track_id"] == 7
    assert dwell_event["duration_seconds"] == 13
