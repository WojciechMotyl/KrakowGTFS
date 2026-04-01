import zipfile
import pandas as pd
from stops import Stop
from typing import BinaryIO, Callable, Dict
from trips import Trip
from routes import Route

# particular read stops.txt with csv stylist and gtfs specification
def read_stops_file(file: BinaryIO) -> pd.DataFrame:
    data = pd.read_csv(file,
                       dtype=str,
                       usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"]
                       )
    data.rename(columns={"stop_lat": "stop_latitude", "stop_lon": "stop_longitude"}, inplace=True)
    return data

# create dict with keys, from stop_id and Stop object from pd dataframe
def creating_dict_of_stops_objects(data_stops: pd.DataFrame)-> Dict[str, Stop]:
    stops = {rekord["stop_id"]: Stop(**rekord) for rekord in data_stops.to_dict(orient="records")}
    return stops


# reading file from zip archive and parse using particular functions
def read_file_from_zip(path_to_zip_file: str, file_name: str, parser_func: Callable[[BinaryIO], pd.DataFrame]) -> pd.DataFrame:
    with zipfile.ZipFile(path_to_zip_file, "r") as zf:
        if file_name not in zf.namelist():
            raise FileNotFoundError(f"File {file_name} not found in zip file.")

        with zf.open(file_name) as file:
            data = parser_func(file)
            return data

# particular read trips.txt with csv stylist and gtfs specification
def read_trips_file(file: BinaryIO) -> pd.DataFrame:
    data = pd.read_csv(file,
                       dtype=str,
                       usecols=["trip_id", "route_id", "trip_headsign", "direction_id"]
                       )
    return data

# create dict with keys, from trip_id and Trip object from pd dataframe
def creating_dict_of_trips_objects(data_trips: pd.DataFrame)-> Dict[str, Trip]:
    trips = {rekord["trip_id"]: Trip(**rekord) for rekord in data_trips.to_dict(orient="records")}
    return trips

def read_routes_file(file: BinaryIO) -> pd.DataFrame:
    data = pd.read_csv(file,
                       dtype=str,
                       usecols=["route_id", "route_short_name", "route_long_name", "route_type"]
                       )
    return data

# create dict with keys, from trip_id and Trip object from pd dataframe
def creating_dict_of_routes_objects(data_routes: pd.DataFrame)-> Dict[str, Route]:
    routes = {rekord["route_id"]: Route(**rekord) for rekord in data_routes.to_dict(orient="records")}
    return routes
