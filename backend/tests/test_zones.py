from app.vision.zones import ZoneManager


def test_zone_manager_point_in_polygon() -> None:
    zone_manager = ZoneManager()
    zone = zone_manager.create_zone(
        "restricted-zone",
        "Restricted Area",
        "restricted",
        [[100, 100], [500, 100], [500, 400], [100, 400]],
    )

    assert zone_manager.is_object_in_zone({"x1": 200, "y1": 200, "x2": 250, "y2": 250}, zone) is True
    assert zone_manager.is_object_in_zone({"x1": 50, "y1": 50, "x2": 80, "y2": 80}, zone) is False
    assert zone_manager.point_in_polygon((250, 200), zone.polygon) is True
