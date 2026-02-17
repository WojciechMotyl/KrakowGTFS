# 🗺️ Roadmapa Projektu: Mapa Pojazdów GTFS na Żywo

**Cel:** Stworzenie aplikacji webowej wyświetlającej pozycje pojazdów komunikacji miejskiej w czasie rzeczywistym.
**Stack:** Python (Backend/FastAPI) + JavaScript (Frontend/Leaflet.js).

## 🏗️ Etap 0: Przygotowanie Środowiska

Zanim napiszesz pierwszą linijkę kodu, uporządkuj warsztat.

- [ ] **Stwórz folder projektu** i otwórz go w VS Code / PyCharm.
- [ ] **Utwórz wirtualne środowisko (venv)** – aby nie śmiecić w systemie.
    * *Docs:* [Python venv (oficjalna dok.)](https://docs.python.org/3/library/venv.html)
- [ ] **Zainstaluj wymagane paczki**: `pip install fastapi uvicorn requests google-transit-gtfs-realtime-bindings geopy`
- [ ] **Stwórz plik `.gitignore`** (jeśli używasz Gita), aby nie wysyłać folderu `venv` ani plików tymczasowych.

## 🐍 Etap 1: Backend - Logika Biznesowa (Python)

Musisz przerobić swoje luźne skrypty na solidne funkcje, które będzie można wywoływać na żądanie.

- [ ] **Moduł GTFS Static:**
    * Stwórz plik `data_loader.py`.
    * Napisz funkcję `load_static_data()`, która wczytuje `stops.txt` i `routes.txt` do słowników i zwraca je.
    * *Cel:* Funkcja ma działać szybko i być wywoływana tylko raz przy starcie serwera.
- [ ] **Moduł GTFS Realtime:**
    * Stwórz plik `gtfs_client.py`.
    * Napisz funkcję `fetch_vehicles(url, static_data)`, która pobiera plik `.pb`, parsuje go i zwraca **listę słowników** (czystych danych JSON-ready).
    * *Wymaganie:* Funkcja musi zwracać np.: `[{'id': '...', 'lat': 50.0, 'lon': 19.9, 'line': '52', 'speed': 30}, ...]`.
- [ ] **Test Manualny:**
    * Stwórz plik `test_run.py`, zaimportuj powyższe funkcje i sprawdź `printem`, czy po uruchomieniu widzisz ładną listę danych.

## 🚀 Etap 2: Backend - API (FastAPI)

Wystawiamy Twoje dane na świat, aby przeglądarka mogła je pobrać.

- [ ] **Hello World w FastAPI:**
    * Stwórz plik `main.py`.
    * Uruchom prosty serwer, który zwraca `{"message": "Działa"}` pod adresem `http://127.0.0.1:8000`.
    * *Tutorial:* [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [ ] **Endpoint z Pojazdami:**
    * Dodaj endpoint `/api/vehicles`.
    * W środku tego endpointu wywołaj funkcję `fetch_vehicles` z Etapu 1 i zwróć jej wynik.
    * Sprawdź w przeglądarce, czy pod tym adresem widzisz swoje dane z GTFS.
- [ ] **Naprawa błędu CORS (Krytyczne!):**
    * Przeglądarka zablokuje połączenie JS -> Python bez tego. Musisz dodać `CORSMiddleware`.
    * *Docs:* [FastAPI CORS (Skopiuj i wklej ten fragment)](https://fastapi.tiangolo.com/tutorial/cors/)

## 🌐 Etap 3: Frontend - Podstawy (HTML + JS)

Twój pierwszy kod w JavaScript. Na razie bez mapy, tylko pobieranie danych.

- [ ] **Struktura plików:**
    * Stwórz folder `static` (lub trzymaj w głównym, jeśli wolisz prościej na start).
    * Stwórz plik `index.html`.
- [ ] **Konsola i Fetch API:**
    * W `index.html` dodaj tag `<script>`.
    * Napisz funkcję `async function getBuses()`.
    * Użyj `fetch('http://127.0.0.1:8000/api/vehicles')` aby pobrać dane.
    * Wyświetl dane w konsoli przeglądarki (`console.log(data)`).
    * *Tutorial:* [MDN: Using Fetch (Wersja przystępna)](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
    * *Wideo:* [Async/Await w 10 minut (YouTube - polecam Fireship lub Web Dev Simplified)](https://www.youtube.com/results?search_query=async+await+javascript)

## 🗺️ Etap 4: Frontend - Mapa (Leaflet.js)

Wizualizacja danych.

- [ ] **Podpięcie Leaflet:**
    * Wklej style CSS i skrypty JS Leafleta do sekcji `<head>` w `index.html`.
    * Stwórz `div` o id `map` i nadaj mu wysokość w CSS (bez tego mapa zniknie!).
    * *Docs:* [Leaflet Quick Start Guide](https://leafletjs.com/examples/quick-start/)
- [ ] **Rysowanie Markerów:**
    * Wewnątrz funkcji `getBuses()` (z Etapu 3) dodaj pętlę `for...of` lub `forEach`.
    * Dla każdego pojazdu stwórz `L.marker([lat, lon]).addTo(map)`.

## 🔄 Etap 5: Życie Aplikacji (Real-time & Optymalizacja)

Sprawiamy, że autobusy się ruszają.

- [ ] **Pętla odświeżania:**
    * Użyj `setInterval(getBuses, 10000)` (co 10 sekund), aby automatycznie pobierać nowe pozycje.
    * *Docs:* [MDN setInterval](https://developer.mozilla.org/en-US/docs/Web/API/setInterval)
- [ ] **Problem "Mrugającej Mapy" (Wyzwanie):**
    * Zauważysz, że przy każdym odświeżeniu stare markery zostają, a nowe się dodają (dublują się).
    * *Rozwiązanie:* Przed narysowaniem nowych markerów musisz wyczyścić stare. Najprostsza metoda: trzymaj markery w tablicy (LayerGroup) i użyj `.clearLayers()` przed dodaniem nowych.
    * *Docs:* [Leaflet LayerGroup](https://leafletjs.com/reference.html#layergroup)

## 🎨 Etap 6: Szlifowanie (Bonusy)

Kiedy wszystko już działa.

- [ ] **Popupy:** Dodaj `.bindPopup("Linia 152")` do markerów.
- [ ] **Ikony:** Zmień domyślną niebieską pinezkę na ikonkę autobusu (np. FontAwesome).
- [ ] **Filtrowanie:** Dodaj pole tekstowe w HTML, aby pokazywać tylko wybraną linię (wymaga prostej logiki `if` w JavaScript).