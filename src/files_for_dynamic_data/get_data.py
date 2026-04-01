from google.transit import gtfs_realtime_pb2
import requests
import datetime

URL_TO_TRIP_UPDATES = "https://gtfs.ztp.krakow.pl/TripUpdates_A.pb"
URL_TO_VEHICLE_POSITIONS = "https://gtfs.ztp.krakow.pl/VehiclePositions_A.pb"

def get_data(url: str) -> gtfs_realtime_pb2.FeedMessage:
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(url)
    feed.ParseFromString(response.content)
    return feed


def get_info_from_trip_updates(feed, amount_of_results: int) -> list:
    k = 0
    wyniki = []

    for entity in feed.entity:
        # Zatrzymujemy szukanie dopiero wtedy, gdy ZNALAZŁEŚ odpowiednią liczbę wyników
        if k >= amount_of_results:
            break

        # Jeśli ten element ma trip_update, to super - wchodzimy i wypisujemy
        if entity.HasField("trip_update"):
            trip_update = entity.trip_update

            # Teraz ten print na 100% zadziała i wypluje całą strukturę!
            print(trip_update)

            # Dodajemy ID do naszej listy wyników (odwołując się do małego .trip)
            wyniki.append(trip_update.trip.trip_id)
            k += 1

        # Jeśli nie ma HasField("trip_update"), pętla po prostu leci dalej
        # do następnego entity. Nie dajemy żadnego 'else: break'!

    return wyniki


def get_info_from_vehicle_positions(feed, amount_of_results: int) -> list:
    k = 0
    wyniki = []

    for entity in feed.entity:
        # Sprawdzamy czy w ogóle osiągnęliśmy już Twój limit
        if k >= amount_of_results:
            break

        # Szukamy tylko encji, które mają dane o pozycjach pojazdów
        if entity.HasField("vehicle"):
            vehicle_position = entity.vehicle

            # TO JEST MAGIA, KTÓREJ SZUKASZ:
            # Wypisuje CAŁE dostępne drzewo dla tego pojazdu
            print(vehicle_position)
            print("=========================================")

            # Zwracamy cokolwiek do listy (np. id pojazdu), żeby funkcja miała sens
            if vehicle_position.HasField("vehicle"):
                wyniki.append(vehicle_position.vehicle.id)
            else:
                wyniki.append("Brak ID")

            k += 1

    return wyniki


# for tests

if __name__ == "__main__":
    URL_TO_TRIP_UPDATES = "https://gtfs.ztp.krakow.pl/TripUpdates_A.pb"
    URL_TO_VEHICLE_POSITIONS = "https://gtfs.ztp.krakow.pl/VehiclePositions_A.pb"

    trip_updates_feed = get_data(URL_TO_TRIP_UPDATES)
    get_info_from_trip_updates(trip_updates_feed, 1)

   # vehicle_positions_feed = get_data(URL_TO_VEHICLE_POSITIONS)
   # get_info_from_vehicle_positions(vehicle_positions_feed, 5)