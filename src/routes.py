from dataclasses import dataclass

@dataclass
class Route:
    route_id: int
    route_short_name: str
    route_long_name: str
    route_type: str