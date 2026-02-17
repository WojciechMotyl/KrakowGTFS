# file with test to load_static_date f
import zipfile
import load_static_data
import pandas as pd
from stops import Stop

PATH_TO_ZIP = r"GTFS_KRK_T.zip"

FILE_NAME = "test.txt"

def test_read_stops_file(FILE_NAME):
    data = load_static_data.read_stops_file(FILE_NAME)
    print(data.to_string())
    print("test_read_stops_file()")

# test_read_stops_file(FILE_NAME)

def test_creating_dict_of_stops_objects(data_stops: pd.DataFrame):
    stops = load_static_data.creating_dict_of_stops_objects(data_stops)
    for s in stops.values():
        print(s.stop_id, s.stop_name, s.stop_latitude, s.stop_longitude)

# test_creating_dict_of_stops_objects(load_static_data.read_stops_file(FILE_NAME))

def test_final_stops_reading():
    data = load_static_data.read_file_from_zip(PATH_TO_ZIP,"stops.txt", load_static_data.read_stops_file)
    stops = load_static_data.creating_dict_of_stops_objects(data)
    for s in stops.values():
        print(s.stop_id, s.stop_name, s.stop_latitude, s.stop_longitude)

test_final_stops_reading()