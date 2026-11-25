"""Download static GTFS files and track their ETags in a CSV file."""

import csv
from collections import deque
from pathlib import Path
from time import strftime

import requests


def check_file_update(url: str, etag: str) -> bool:
    """Check whether the remote file has changed.

    Args:
        url: URL of the remote file.
        etag: ETag of the previously downloaded file.

    Returns:
        True if the server returns a 200 status code; otherwise, False.
    """
    headers = {"If-None-Match": etag}
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def get_new_etag(url: str) -> str:
    """Fetch the current ETag for a remote file.

    Args:
        url: URL of the remote file.

    Returns:
        The ETag value, or an empty string if the request fails or has none.
    """
    try:
        response = requests.get(url)
        return response.headers.get("ETag", "")
    except requests.exceptions.RequestException as error:
        print(f"Error occurred while fetching the ETag: {error}")
        return ""


def create_path() -> Path:
    """Return the directory used to store static data.

    Returns:
        The path to the project's static data directory.
    """
    return (
        Path(__file__).resolve().parent.parent.parent.parent / "static_data"
    )


def get_date() -> str:
    """Return today's date in day_month_year format.

    Returns:
        The current date formatted as DD_MM_YYYY.
    """
    return strftime("%d_%m_%Y")


def create_file_name(file_name: str, id: int) -> str:
    """Build a dated ZIP filename for a downloaded file.

    Args:
        file_name: Original filename.
        id: Identifier to include in the filename.

    Returns:
        The generated filename.
    """
    return f"{file_name.partition('.')[0]}_{strftime('%d_%m_%Y')}_id_{id}.zip"


def create_new_csvfile(file_path: Path) -> bool:
    """Create a CSV file with the download-history header.

    Args:
        file_path: Path where the CSV file will be created.

    Returns:
        True after the file and its header are created.
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, mode="w", encoding="utf-8", newline="") as csvfile:
        fieldnames = ["id", "etag", "date_of_download"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
    return True


def get_file_id(file_path: Path) -> int:
    """Get the next download identifier from the CSV history.

    Args:
        file_path: Path to the download-history CSV file.

    Returns:
        The next identifier, starting at 1 for an empty or new file.
    """
    if Path(file_path).exists():
        with open(
            file_path, mode="r", encoding="utf-8", newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            last_row = deque(reader, maxlen=1)
            if not last_row:
                return 1
            else:
                last_row = last_row[0]
                return int(last_row["id"]) + 1
    else:
        if create_new_csvfile(file_path):
            return 1
        else:
            return -1


def get_last_etag(file_path: Path) -> str:
    """Get the ETag from the most recent download-history entry.

    Args:
        file_path: Path to the download-history CSV file.

    Returns:
        The most recent ETag, or an empty string if no entry exists.
    """
    if Path(file_path).exists():
        with open(
            file_path, mode="r", encoding="utf-8", newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            last_row = deque(reader, maxlen=1)
            if not last_row:
                return ""
            else:
                last_row = last_row[0]
                return last_row["etag"]
    return ""


def write_new_entry(
    file_path: Path, id: int, etag: str, date_of_download: str
) -> bool:
    """Append a download record to the CSV history.

    Args:
        file_path: Path to the download-history CSV file.
        id: Identifier assigned to the downloaded file.
        etag: ETag of the downloaded file.
        date_of_download: Date the file was downloaded.

    Returns:
        True if the record is written; otherwise, False.
    """
    try:
        with open(
            file_path, mode="a", encoding="utf-8", newline=""
        ) as csvfile:
            fieldnames = ["id", "etag", "date_of_download"]
            writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, delimiter=","
            )
            writer.writerow(
                {
                    "id": id,
                    "etag": etag,
                    "date_of_download": date_of_download,
                }
            )
        return True
    except (OSError, csv.Error) as error:
        print(f"Error occurred while writing to the CSV file: {error}")
        return False


def get_file(url: str, file_name: str | Path, timeout: int = 15) -> bool:
    """Download a remote file into the static data directory.

    Args:
        url: URL of the remote file.
        file_name: Name or path of the file to save.
        timeout: Maximum wait time for the request, in seconds.

    Returns:
        True if the file is downloaded; otherwise, False.
    """
    file_path = create_path() / file_name

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True

    except (requests.exceptions.RequestException, OSError) as error:
        file_path.unlink(missing_ok=True)
        print(f"Error occurred while fetching the file: {error}")
        return False


def all_in_one(url: str, file_name: str, file_with_data: str) -> bool:
    """Check for an update, download the file, and record its metadata.

    Args:
        url: URL of the remote file.
        file_name: Original filename used to generate the saved filename.
        file_with_data: Name of the CSV download-history file.

    Returns:
        True if the file is downloaded and its history entry is written;
        otherwise, False.
    """
    file_with_data = create_path() / file_with_data
    last_etag = get_last_etag(file_with_data)
    if check_file_update(url, last_etag):
        new_etag = get_new_etag(url)
        file_id = get_file_id(file_with_data)
        file_to_save = create_path() / create_file_name(
            file_name=file_name, id=file_id
        )
        if get_file(url, file_to_save):
            if write_new_entry(file_with_data, file_id, new_etag, get_date()):
                return True
        return False
    return False


if __name__ == "__main__":
    url = "https://gtfs.ztp.krakow.pl/GTFS_KRK_T.zip"

    print("test")

    if all_in_one(url, "GTFS_KRK_T.zip", "file.csv"):
        print("Plik zostal pomyslnie pobrany i zapisany.")
    else:
        print("Plik nie zostal pobrany")
