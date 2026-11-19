import sqlite3
import time
import urllib.request

from google.transit import gtfs_realtime_pb2


# ==========================================
# 1. TWORZENIE BAZY DANYCH I TABELI
# ==========================================
def init_db(db_name="ztp_krakow.db"):
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS realtime_positions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       feed_timestamp
                       INTEGER
                       NOT
                       NULL,
                       vehicle_type
                       TEXT
                       NOT
                       NULL,
                       trip_id
                       TEXT
                       NOT
                       NULL,
                       stop_id
                       TEXT,
                       current_status
                       INTEGER, -- 0=INCOMING_AT, 1=STOPPED_AT, 2=IN_TRANSIT_TO
                       current_stop_sequence
                       INTEGER,
                       speed
                       REAL,
                       latitude
                       REAL,
                       longitude
                       REAL,
                       arrival_delay
                       INTEGER,
                       departure_delay
                       INTEGER
                   )
                   """)

    # Czyste indeksy pod szybkie złączenia pod ML
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_trip_id ON"
        " realtime_positions(trip_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON"
        " realtime_positions(feed_timestamp);"
    )

    conn.commit()
    conn.close()


# ==========================================
# 2. FUNKCJA PARSUJĄCA (Z PARAMETREM VEHICLE_TYPE)
# ==========================================
def parse_ztp_pb(vp_bytes, tu_bytes=None, vehicle_type="A"):
    extracted_rows = []

    # 1. Bezpieczne parsowanie VehiclePositions
    vp_feed = gtfs_realtime_pb2.FeedMessage()
    try:
        vp_feed.ParseFromString(vp_bytes)
    except Exception as e:
        print(f"Błąd rozkodowywania pliku VehiclePositions: {e}")
        return []  # Przerywamy i zwracamy pustą listę (0 rekordów)

    # Upewniamy się, że w pliku na pewno znajduje się nagłówek z czasem
    if not vp_feed.HasField("header"):
        print("Pobrany plik nie ma nagłówka (header). Ignoruję.")
        return []

    feed_timestamp = vp_feed.header.timestamp

    # 2. Bezpieczne parsowanie TripUpdates (Opóźnienia)
    delay_map = {}
    if tu_bytes:
        tu_feed = gtfs_realtime_pb2.FeedMessage()
        try:
            tu_feed.ParseFromString(tu_bytes)
            for entity in tu_feed.entity:
                if entity.HasField("trip_update"):
                    tu = entity.trip_update
                    t_id = tu.trip.trip_id
                    if len(tu.stop_time_update) > 0:
                        first_stu = tu.stop_time_update[0]
                        arr_delay = (
                            first_stu.arrival.delay
                            if first_stu.HasField("arrival")
                            else None
                        )
                        dep_delay = (
                            first_stu.departure.delay
                            if first_stu.HasField("departure")
                            else None
                        )
                        delay_map[t_id] = (arr_delay, dep_delay)
        except Exception as e:
            # Opóźnienia to dodatek - jeśli tu jest błąd, nie przerywamy całości!
            print(f"Błąd rozkodowywania TripUpdates (ignoruję opóźnienia w tej pętli): {e}")

    # 3. Wyciąganie danych głównych
    for entity in vp_feed.entity:
        if entity.HasField("vehicle"):
            v = entity.vehicle
            trip_id = v.trip.trip_id if v.HasField("trip") else None

            # Ignoruj pojazdy bez przypisanego kursu
            if not trip_id:
                continue

            arr_delay, dep_delay = delay_map.get(trip_id, (None, None))

            extracted_rows.append((
                feed_timestamp,
                vehicle_type,
                trip_id,
                v.stop_id if v.HasField("stop_id") else None,
                v.current_status if v.HasField("current_status") else None,
                v.current_stop_sequence
                if v.HasField("current_stop_sequence")
                else None,
                v.position.speed if v.position.HasField("speed") else None,
                v.position.latitude if v.HasField("position") else None,
                v.position.longitude if v.HasField("position") else None,
                arr_delay,
                dep_delay,
            ))

    return extracted_rows


# ==========================================
# 3. ZAPIS DO BAZY
# ==========================================
def save_to_db(rows, db_name="ztp_krakow.db"):
    if not rows:
        return
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    query = """
            INSERT INTO realtime_positions (feed_timestamp, vehicle_type, trip_id,
                                            stop_id, current_status, current_stop_sequence, speed,
                                            latitude, longitude, arrival_delay, departure_delay)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
            """
    cursor.executemany(query, rows)
    conn.commit()
    conn.close()


def get_data_from_url(url : str, headers : dict, timeout=15):
    req_vp = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req_vp, timeout=timeout) as response:
        vp_data = response.read()
        return vp_data

# Sprawdza czy pobrane dane to poprawny plik binarny do parserowania
def check_data_correctness(vehicle_positions_data):
    if len(vehicle_positions_data) < 100:
        print(f"[{time.strftime('%H:%M:%S')}] Serwer zwrócił pusty plik ({len(vehicle_positions_data)} bajtów)! Prawdopodobnie blokada anty-spamowa. Czekam do następnej pętli.")
        return False
    elif vehicle_positions_data.startswith(b'<') or vehicle_positions_data.startswith(b'{'):
        print(f"[{time.strftime('%H:%M:%S')}] Serwer zwrócił tekst HTML/JSON zamiast danych binarnych. Czekam.")
        return False
    return True
# for tests

if __name__ == "__main__":
    URL_VEHICLE_POSITIONS_BUS = "https://gtfs.ztp.krakow.pl/VehiclePositions_A.pb"
    URL_TRIP_UPDATES_BUS = "https://gtfs.ztp.krakow.pl/TripUpdates_A.pb"
    INTERVAL = 30
    # Inicjalizacja bazy przy pierwszym uruchomieniu
    init_db()

    print("Rozpoczynam zbieranie danych dla AUTOBUSÓW (Ctrl+C aby zatrzymać)...")

    while True:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}

            # getting data
            vehicle_positions_data = get_data_from_url(URL_VEHICLE_POSITIONS_BUS, headers)
            trip_updates_data = get_data_from_url(URL_TRIP_UPDATES_BUS, headers)

            # Sprawdzenie poprawnosc i parserowanie danych
            if check_data_correctness(vehicle_positions_data):
                bus_rows = parse_ztp_pb(vehicle_positions_data, trip_updates_data, vehicle_type='A')
                save_to_db(bus_rows)
                print(
                    f"[{time.strftime('%H:%M:%S')}] POBRANO: {len(vehicle_positions_data)} bajtów. Zapisano {len(bus_rows)} rekordów.")

        except urllib.error.URLError as e:
            print(f"[{time.strftime('%H:%M:%S')}] Problem z siecią/Timeout: {e}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Inny błąd pobierania: {e}")

        time.sleep(INTERVAL)
