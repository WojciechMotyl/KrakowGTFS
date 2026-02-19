from dataclasses import dataclass

@dataclass
class Stop:
    stop_id: str
    stop_name: str
    stop_latitude: float
    stop_longitude: float

    def __post_init__(self):
        # from pandas object get stop_latitude and stop_longitude like a string, this method converse it after creating instance

        try:
            if self.stop_latitude is not None:
                self.stop_latitude = float(self.stop_latitude)
        except ValueError:
            self.stop_latitude = None

        try:
            if self.stop_longitude is not None:
                self.stop_longitude = float(self.stop_longitude)
        except ValueError:
            self.stop_longitude = None

