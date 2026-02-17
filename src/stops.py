from dataclasses import dataclass

@dataclass
class Stop:
    stop_id: str = ""
    stop_name: str = ""
    stop_latitude: float = 0
    stop_longitude: float = 0