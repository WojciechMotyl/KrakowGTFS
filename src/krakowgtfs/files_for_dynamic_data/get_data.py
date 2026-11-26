"""Download, parse, and store Krakow GTFS realtime vehicle data."""

import sqlite3
import time
import urllib.error
import urllib.request

from google.transit import gtfs_realtime_pb2


RealtimeRow = tuple[
    int,
    int,
    str,
    str,
    str | None,
    int | None,
    int | None,
    float | None,
    float | None,
    float | None,
    int | None,
    int | None,
]


def init_db(db_name: str = "ztp_krakow.db") -> None:
    """Create the realtime positions table and its indexes.

    Args:
        db_name: Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS realtime_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            feed_timestamp INTEGER NOT NULL,
            vehicle_type TEXT NOT NULL,
            trip_id TEXT NOT NULL,
            stop_id TEXT,
            current_status INTEGER,
            current_stop_sequence INTEGER,
            speed REAL,
            latitude REAL,
            longitude REAL,
            arrival_delay INTEGER,
            departure_delay INTEGER
        )
        """
    )

    # Indexes for faster joins and queries.
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_trip_id "
        "ON realtime_positions(trip_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_timestamp "
        "ON realtime_positions(feed_timestamp);"
    )

    conn.commit()
    conn.close()


def _parse_trip_updates(
    tu_bytes: bytes,
) -> dict[str, tuple[int | None, int | None]]:
    """Extract first-stop arrival and departure delays from a TripUpdates feed.

    Args:
        tu_bytes: Serialized GTFS-Realtime TripUpdates feed.

    Returns:
        A mapping from trip IDs to first-stop arrival and departure delays.
    """
    delay_map: dict[str, tuple[int | None, int | None]] = {}
    tu_feed = gtfs_realtime_pb2.FeedMessage()

    try:
        tu_feed.ParseFromString(tu_bytes)
        for entity in tu_feed.entity:
            if entity.HasField("trip_update"):
                trip_update = entity.trip_update
                trip_id = trip_update.trip.trip_id

                if len(trip_update.stop_time_update) > 0:
                    first_stop_update = trip_update.stop_time_update[0]
                    arrival_delay = (
                        first_stop_update.arrival.delay
                        if first_stop_update.HasField("arrival")
                        else None
                    )
                    departure_delay = (
                        first_stop_update.departure.delay
                        if first_stop_update.HasField("departure")
                        else None
                    )
                    delay_map[trip_id] = (arrival_delay, departure_delay)
    except Exception as error:
        # Delays are optional; errors do not stop vehicle parsing.
        print(
            "Błąd rozkodowywania TripUpdates "
            f"(ignoruję opóźnienia w tej pętli): {error}"
        )

    return delay_map


def parse_ztp_pb(
    vp_bytes: bytes,
    schedule_id: int,
    tu_bytes: bytes | None = None,
    vehicle_type: str = "A",
) -> list[RealtimeRow]:
    """Parse GTFS-Realtime vehicle positions and optional trip delays.

    Args:
        vp_bytes: Serialized GTFS-Realtime VehiclePositions feed.
        schedule_id: Identifier for the schedule associated with the feed.
        tu_bytes: Optional serialized TripUpdates feed.
        vehicle_type: Vehicle category stored with each parsed position.

    Returns:
        Rows ready to insert into the ``realtime_positions`` table.
    """
    extracted_rows: list[RealtimeRow] = []

    # Parse VehiclePositions.
    vp_feed = gtfs_realtime_pb2.FeedMessage()
    try:
        vp_feed.ParseFromString(vp_bytes)
    except Exception as error:
        print(f"Błąd rozkodowywania pliku VehiclePositions: {error}")
        return []

    if not vp_feed.HasField("header"):
        print("Pobrany plik nie ma nagłówka (header). Ignoruję.")
        return []

    feed_timestamp = vp_feed.header.timestamp

    # TripUpdates are optional; parsing errors leave delays empty or partial.
    delay_map = _parse_trip_updates(tu_bytes) if tu_bytes else {}

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
                schedule_id,
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


def save_to_db(
    rows: list[RealtimeRow], db_name: str = "ztp_krakow.db"
) -> None:
    """Insert parsed realtime position rows into the SQLite database.

    Args:
        rows: Parsed position rows to insert.
        db_name: Path to the SQLite database file.
    """
    if not rows:
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    query = """
        INSERT INTO realtime_positions (
            feed_timestamp,
            schedule_id,
            vehicle_type,
            trip_id,
            stop_id,
            current_status,
            current_stop_sequence,
            speed,
            latitude,
            longitude,
            arrival_delay,
            departure_delay
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.executemany(query, rows)
    conn.commit()
    conn.close()


def get_data_from_url(
    url: str, headers: dict[str, str], timeout: int = 15
) -> bytes:
    """Download a URL and return its response body.

    Args:
        url: Address to request.
        headers: HTTP headers to send with the request.
        timeout: Maximum wait time for the response, in seconds.

    Returns:
        The response body as bytes.
    """
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def check_data_correctness(vehicle_positions_data: bytes) -> bool:
    """Check whether downloaded data resembles a GTFS-Realtime binary feed.

    Args:
        vehicle_positions_data: Downloaded VehiclePositions response body.

    Returns:
        Whether the response passes the basic size and format checks.
    """
    if len(vehicle_positions_data) < 100:
        print(
            f"[{time.strftime('%H:%M:%S')}] Serwer zwrócił pusty plik "
            f"({len(vehicle_positions_data)} bajtów)! "
            "Prawdopodobnie blokada anty-spamowa. "
            "Czekam do następnej pętli."
        )
        return False
    if (
        vehicle_positions_data.startswith(b"<")
        or vehicle_positions_data.startswith(b"{")
    ):
        print(
            f"[{time.strftime('%H:%M:%S')}] "
            "Serwer zwrócił tekst HTML/JSON zamiast danych binarnych. "
            "Czekam."
        )
        return False
    return True


if __name__ == "__main__":
    URL_VEHICLE_POSITIONS_BUS = (
        "https://gtfs.ztp.krakow.pl/VehiclePositions_A.pb"
    )
    URL_TRIP_UPDATES_BUS = "https://gtfs.ztp.krakow.pl/TripUpdates_A.pb"
    INTERVAL = 30

    init_db()

    print(
        "Rozpoczynam zbieranie danych dla AUTOBUSÓW "
        "(Ctrl+C aby zatrzymać)..."
    )

    while True:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }

            vehicle_positions_data = get_data_from_url(
                URL_VEHICLE_POSITIONS_BUS, headers
            )
            trip_updates_data = get_data_from_url(
                URL_TRIP_UPDATES_BUS, headers
            )

            if check_data_correctness(vehicle_positions_data):
                bus_rows = parse_ztp_pb(
                    vehicle_positions_data,
                    1,
                    trip_updates_data,
                    vehicle_type="A",
                )
                save_to_db(bus_rows)
                print(
                    f"[{time.strftime('%H:%M:%S')}] POBRANO: "
                    f"{len(vehicle_positions_data)} bajtów. "
                    f"Zapisano {len(bus_rows)} rekordów."
                )

        except urllib.error.URLError as error:
            print(
                f"[{time.strftime('%H:%M:%S')}] "
                f"Problem z siecią/Timeout: {error}"
            )
        except Exception as error:
            print(
                f"[{time.strftime('%H:%M:%S')}] "
                f"Inny błąd pobierania: {error}"
            )

        time.sleep(INTERVAL)
