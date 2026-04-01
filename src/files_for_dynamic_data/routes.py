from dataclasses import dataclass

@dataclass
class Route:
    route_id: int
    route_short_name: str
    route_long_name: str
    route_type: str

    def print_info(self):
        print(f"Route ID: {self.route_id}")
        print(f"Route Short Name: {self.route_short_name}")
        print(f"Route Long Name: {self.route_long_name}")
        print(f"Route Type: {self.route_type}")