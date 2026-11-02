# Konwerter plików

Desktopowy konwerter plików napisany w Pythonie z interfejsem Tkinter/ttk i dodatkowym trybem CLI. Logika konwersji jest oddzielona od interfejsów. Projekt nie obsługuje dowolnych par formatów.

## Autorzy

Dawid Borowski 

## Wymagania

- Python 3.10 lub nowszy (kod używa zapisu Path | None).
- Tkinter/ttk dostępny w instalacji Pythona.
- Pakiety Python z requirements.txt.
- LibreOffice dla ODT → PDF, DOCX → ODT i ODT → DOCX oraz jako alternatywa przy konwersji DOCX → PDF.
- Microsoft Word jest opcjonalnym silnikiem DOCX → PDF na Windows; jeżeli ta próba zawiedzie, aplikacja próbuje LibreOffice.
- Katalog docelowy musi istnieć i umożliwiać zapis.

Głównym środowiskiem używanym podczas prac jest Windows. Nie zadeklarowano testów całej aplikacji na innych systemach.

## Instalacja — Windows

W terminalu w głównym katalogu projektu:

```bat
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m tkinter
```

Ostatnie polecenie pozwala sprawdzić dostępność Tkinter. Zainstaluj także LibreOffice, jeżeli chcesz korzystać z konwersji biurowych. Domyślna ścieżka w converters.py to C:\Program Files\LibreOffice\program\soffice.com. Funkcja find_libreoffice() sprawdza skonfigurowaną ścieżkę i rejestr Windows; po zastosowaniu poprawki wyszukiwania sprawdza również PATH oraz typową lokalizację macOS.

## Uruchomienie GUI

```bat
.venv\Scripts\python src\gui.py
```

1. Wybierz plik wejściowy.
2. Wybierz format docelowy z listy zależnej od rozszerzenia.
3. Użyj „Zapisz jako”, aby wybrać katalog i nazwę wyniku.
4. Kliknij „Konwertuj”.
5. Jeżeli plik istnieje, potwierdź nadpisanie albo anuluj.

W trakcie konwersji kontrolki są blokowane, a pasek sygnalizuje pracę. Wynik lub błąd pojawia się w oknie dialogowym. Błędy są zapisywane w converter.log w głównym katalogu projektu. Zmiana pliku wejściowego lub formatu usuwa wcześniejszy wybór ścieżki wyjściowej.

## Uruchomienie CLI

```bat
.venv\Scripts\python src\main.py data\dane.csv output\dane.json
.venv\Scripts\python src\main.py
```

Tryb bez argumentów pyta o ścieżki. W CLI samo podanie nazwy pliku wejściowego powoduje szukanie go w data/ i output/, a sama nazwa wyjściowa kieruje zapis do output/. Przy konflikcie nazw CLI pozwala nadpisać, nadać bezpieczną nazwę lub anulować. Nie należy używać konwertera bezpośrednio jako zamiennika tej polityki: pytanie o nadpisanie należy do interfejsu.

## Macierz konwersji i ograniczenia

Poniższa tabela opisuje zaimplementowany zakres, nie wyniki testów każdego kierunku.

| Grupa | Wejście | Wyjście | Ograniczenia / zależności |
|---|---|---|---|
| A | CSV | JSON | Płaska tabela, przecinek jako separator, nagłówki obowiązkowe; wartości pozostają tekstem. |
| A | JSON | CSV | Niepusta lista płaskich obiektów o takim samym zestawie kluczy; brak zagnieżdżeń. |
| B | TXT | DOCX | Tekst UTF-8, wiersze przenoszone do akapitów; bez zaawansowanego formatowania. |
| B | TXT | PDF | Etap pośredni DOCX; wymaga Worda lub LibreOffice. |
| B | DOCX | TXT | Eksport tekstu akapitów; bez obrazów, formatowania i tekstu tabel. |
| C | DOCX | PDF | Próba Worda, następnie LibreOffice; możliwe różnice układu i fontów. |
| C | ODT | PDF | LibreOffice; brak gwarancji identycznego układu stron. |
| C | DOCX | ODT | LibreOffice; możliwa utrata złożonego formatowania. |
| C | ODT | DOCX | LibreOffice; możliwa utrata złożonego formatowania. |

## Semantyka CSV i JSON

- CSV wejściowy jest czytany jako UTF-8 z obsługą BOM (utf-8-sig); separator to przecinek, a standardowym znakiem cytowania jest cudzysłów.
- Nagłówki CSV muszą istnieć, nie mogą być puste ani składać się wyłącznie z białych znaków i nie mogą się powtarzać.
- Każdy rekord CSV musi mieć tyle pól co nagłówek. Puste pole jest dozwolone; brak pola jest błędem.
- Same nagłówki CSV są dozwolone i dają pustą listę JSON. Taki wynik nie jest akceptowany w kierunku odwrotnym, ponieważ nie zawiera informacji o kolumnach.
- JSON wyjściowy jest UTF-8, bez zamiany polskich liter na sekwencje escape, z wcięciem 4 spacji.
- JSON wejściowy musi być niepustą listą obiektów. Każdy obiekt ma ten sam zestaw kluczy; nazwy kolumn nie mogą być puste. Obiekty i listy jako wartości są odrzucane.
- Kolejność kolumn wynika z kolejności kluczy pierwszego obiektu. Kolejne rekordy mogą mieć klucze zapisane w innej kolejności.
- CSV wyjściowy jest UTF-8 z BOM, z nagłówkiem.
- W CSV liczby i wartości logiczne są tekstową reprezentacją wartości. null jest zapisywany jako puste pole. Po ponownej konwersji CSV → JSON wszystkie wartości są tekstem; typy JSON nie są odtwarzane.

Przykład akceptowanego JSON:

```json
[
  {"imię": "Łukasz", "miasto": "Łódź", "uwagi": ""},
  {"imię": "Żaneta", "miasto": "Gdańsk", "uwagi": "Zażółć gęślą jaźń"}
]
```

## Architektura i błędy

- src/converters.py: rejestr par formatów, walidacja i funkcje konwersji.
- src/gui.py: formularz, dialogi, potwierdzenie nadpisania, wątek roboczy i kolejka wyników.
- src/main.py: CLI i interaktywna obsługa ścieżek.
- src/test_converters.py: testy automatyczne.

convert() normalizuje ścieżki, waliduje je, wybiera funkcję z REGISTRY, tworzy wynik tymczasowy w katalogu docelowym, sprawdza wynik i dopiero wtedy zastępuje plik docelowy. Pozwala to uniknąć zastąpienia poprzedniego wyniku nieudaną konwersją. Funkcje poszczególnych konwerterów wywoływane bezpośrednio nie zapewniają tego całego przepływu.

Model błędów wykorzystuje standardowe wyjątki: ValueError dla błędnych danych/par formatów, OSError i jego podklasy dla problemów plikowych oraz RuntimeError dla nieudanej pracy narzędzia lub braku wyniku. Interfejs przechwytuje wyjątki i prezentuje komunikat zamiast tracebacku.

LibreOffice jest uruchamiany bez shell=True, z kontrolą kodu zakończenia, limitem czasu i sprawdzeniem wyniku. GUI nie ma przycisku anulowania trwającej konwersji. Ścieżka Word/docx2pdf nie ma własnego limitu czasu w obecnej implementacji.

## Testy

```bat
.venv\Scripts\python -m unittest discover -s src -p "test_*.py" -v
```

Wynik dla końcowej wersji (2026-11-02): 23 testy, OK. Szczegóły i lista testów ręcznych są w docs/raport-testow.md. Opis danych znajduje się w data/README.md.

## Źródła i narzędzia

- Instrukcja projektowa: projekt-1-konwerter.pdf, wersja 5 października 2026.
- Python / Tkinter: https://docs.python.org/3/library/tkinter.html
- Dialogi plikowe: https://docs.python.org/3/library/dialog.html
- CSV: https://docs.python.org/3/library/csv.html
- JSON: https://docs.python.org/3/library/json.html
- subprocess: https://docs.python.org/3/library/subprocess.html
- unittest: https://docs.python.org/3/library/unittest.html
- python-docx: https://python-docx.readthedocs.io/
- docx2pdf: https://github.com/AlJohri/docx2pdf
- LibreOffice: https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html
- AI:
  - GPT 6.1 w Perplexity — pomoc przy kodowaniu. Wymagane części zadania, w tym podstawowe funkcje GUI, napisałem samodzielnie, a asystent prowadził mnie krok po kroku przez kod. Trudniejsze elementy GUI (np. konwersja w tle, obsługa nadpisywania i blokada kontrolek) przygotowała AI. Elementy dodatkowe — interfejs terminalowy (TUI, src/main.py uruchomiony bez argumentów), wyszukiwanie LibreOffice itp. — oraz dokumentację przygotowała AI.
  - Claude (Claude Code) — uruchomienie testów automatycznych i skryptowych, uzupełnienie raportu testów (docs/raport-testow.md) na podstawie moich testów ręcznych i zrzutów.
