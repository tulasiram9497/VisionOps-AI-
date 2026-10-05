from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Zone:
    id: str
    name: str
    type: str = "restricted"
    polygon: list[list[int]] = field(default_factory=list)


class ZoneManager:
    """Manage monitoring zones and point-in-polygon checks."""

    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}

    def create_zone(self, zone_id: str, name: str, zone_type: str, polygon: list[list[int]]) -> Zone:
        zone = Zone(id=zone_id, name=name, type=zone_type, polygon=polygon)
        self.zones[zone_id] = zone
        return zone

    def delete_zone(self, zone_id: str) -> None:
        self.zones.pop(zone_id, None)

    def list_zones(self) -> list[Zone]:
        return list(self.zones.values())

    def get_zone(self, zone_id: str) -> Zone | None:
        return self.zones.get(zone_id)

    @staticmethod
    def point_in_polygon(point: tuple[float, float], polygon: list[list[int]]) -> bool:
        x, y = point
        inside = False
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            intersect = ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1)
            if intersect:
                inside = not inside
        return inside

    def is_object_in_zone(self, bbox: dict[str, float], zone: Zone) -> bool:
        cx = (bbox["x1"] + bbox["x2"]) / 2
        cy = (bbox["y1"] + bbox["y2"]) / 2
        return self.point_in_polygon((cx, cy), zone.polygon)
