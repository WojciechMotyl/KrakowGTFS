import requests
from pathlib import Path
from time import strftime

def check_file_update(url:str, etag: str) -> bool:
    headers = {"If-None-Match": etag}
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def create_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "static_data"

def create_file_name(file_name:str, id: int) -> str:
    return f"{file_name.partition(".")[0]}_{strftime('%d_%m_%Y')}_id_{id}.zip"

def get_file(url:str, file_name: str, timeout: int = 15) -> bool:
    file_path = create_path() / file_name

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True

    except (requests.exceptions.RequestException, OSError) as e:
        file_path.unlink(missing_ok=True)
        print(f"Error occurred while fetching the file: {e}")
        return False



if __name__ == "__main__":
    url = "https://gtfs.ztp.krakow.pl/GTFS_KRK_T.zip"

    print("test")

    test_etag = '"4a888d-6afb0b1c-95e40ca18c36f86e;;;"'
    naglowki = {}

    if check_file_update(url, test_etag):
        print("Nowy plik do pobrania")
    else:
        print("Brak nowego pliku do pobrania")

    get_file(url, create_file_name("GTFS_KRK_T", 1))