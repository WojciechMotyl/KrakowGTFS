import zipfile
import pandas as pd
from stops import Stop
from typing import BinaryIO, Callable, Any, Dict

# particular read stops.txt with csv stylist and gtfs specifation
def read_stops_file(file: BinaryIO) -> pd.DataFrame:
    data = pd.read_csv(file,
                       dtype=str,
                       usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"]
                       )
    data.rename(columns={"stop_lat": "stop_latitude", "stop_lon": "stop_longitude"}, inplace=True)
    return data

#
def creating_dict_of_stops_objects(data_stops: pd.DataFrame)-> Dict[str, Stop]:
    stops = {rekord["stop_id"]: Stop(**rekord) for rekord in data_stops.to_dict("records")}
    return stops


# reading file from zip archive and parse using particular functions
def read_file_from_zip(path_to_zip_file: str, file_name: str, parser_func: Callable[[BinaryIO], Any]) -> pd.DataFrame:
    with zipfile.ZipFile(path_to_zip_file, "r") as zf:
        if file_name not in zf.namelist():
            raise FileNotFoundError(f"File {file_name} not found in zip file.")

        with zf.open(file_name) as file:
            data = parser_func(file)
            return data

