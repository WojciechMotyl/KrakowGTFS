from dataclasses import dataclass

@dataclass
class Trip:
    trip_id: str
    route_id: str
    trip_headsign: str
    direction_id: int

    def __post_init__(self):
        # changing direction_id to int, if we get str

        try:
            if self.direction_id is not None:
                self.direction_id = int(self.direction_id)
        except ValueError:
            self.direction_id = None

    def print_info(self):
        print(f"Trip ID: {self.trip_id}")
        print(f"Route ID: {self.route_id}")
        print(f"Trip Headsign: {self.trip_headsign}")
        print(f"Direction ID: {self.direction_id}")