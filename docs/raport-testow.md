# Raport testów

## Testy automatyczne

Zakres 23 testów jednostkowych:

| Obszar | Liczba | Zakres | Wynik |
|---|---:|---|---|
| csv_check | 9 | Poprawny CSV, puste pole, same nagłówki, brak nagłówków, pusta nazwa, nazwa z samych spacji, duplikaty, nadmiar i brak pola | OK |
| CSV/JSON | 3 | Oba kierunki, treść wyniku, polskie znaki, kolejność kolumn, puste wartości, odrzucenie nadmiarowego pola przez konwerter | OK |
| validate_paths | 5 | Poprawne ścieżki, brak wejścia, brak katalogu, wyjście jako katalog, identyczne ścieżki | OK |
| available_targets | 6 | CSV, JSON, DOCX, wielkie litery, nieobsługiwane rozszerzenie, brak rozszerzenia | OK |

### Uruchomienie końcowe

Polecenie użyte do uruchomienia:

```bat
python -m unittest discover -s src -p "test_*.py" -v > docs\wynik-testow.txt 2>&1
```

Wykonano 2026-11-02: Windows 11 Pro (10.0.26300), Python 3.14.6, LibreOffice 26.8.1.1 (F:\Programy\LibreOffice). Wynik: **23 testy w 0.031 s, OK** — pełny log w docs/wynik-testow.txt.

## Testy ręczne

2026-11-02: przypadki niezależne od GUI wykonano skryptem wywołującym convert(); wyniki w examples/wyniki/. Następnie wszystkie przypadki R1–R17 potwierdzono ręcznie (GUI lub podgląd wyników) — zrzuty w docs/zrzuty/.

| ID | Próba | Oczekiwany rezultat | Status / dowód |
|---|---|---|---|
| R1 | data/dane.csv → JSON w GUI | Otwieralny JSON, poprawne polskie znaki i puste pole | ZALICZONY (GUI, 2026-11-02) — wynik output/dane.json, komunikat „Konwersja zakończona”; zrzut: docs/zrzuty/R1_csv_json.png; treść zgodna z examples/wyniki/dane.json (znaki i puste pola OK) |
| R2 | data/a.json → CSV w GUI | Nagłówki w kolejności, poprawne znaki i puste pole | ZALICZONY (GUI, 2026-11-02) — wejście output/dane.json (wynik R1, identyczny z data/a.json), wynik output/dane.csv identyczny z wynikiem skryptu; zrzut: docs/zrzuty/R2_json_csv.png |
| R3 | data/tekst.txt → DOCX | Dwa akapity tekstowe, zachowana pusta linia; dokument otwiera się | ZALICZONY (skrypt, 2026-11-02) — examples/wyniki/tekst.docx; poprawność potwierdzona pośrednio: wynikowe tekst_docx.pdf i tekst.txt (R4, R17) mają oba akapity i pustą linię |
| R4 | DOCX z R3 → TXT | Tekst akapitów bez formatowania; wynik otwieralny | ZALICZONY (skrypt + podgląd, 2026-11-02) — examples/wyniki/tekst.txt: 'Zażółć gęślą jaźń.', pusta linia, 'Drugi akapit: Łódź, Gdańsk, Żaneta.'; otwarty w Notatniku (UTF-8, CRLF); zrzut: docs/zrzuty/R4_R17_txt_pdf.png |
| R5 | DOCX z R3 → ODT | LibreOffice tworzy otwieralny dokument z treścią | ZALICZONY (skrypt, 2026-11-02) — examples/wyniki/tekst.odt utworzony przez LibreOffice; treść potwierdzona pośrednio przez tekst_odt.pdf i tekst_odt.docx (R6, R17) |
| R6 | ODT z R5 → PDF | Otwieralny PDF z polskimi znakami | ZALICZONY (2026-11-02) — examples/wyniki/tekst_odt.pdf otwarty w przeglądarce: 1 strona, oba akapity z polskimi znakami; zrzut: docs/zrzuty/R6_R17_podglad_wynikow.png |
| R7 | data/bledne.json → CSV | Czytelny błąd, brak awarii i brak nowego wyniku | ZALICZONY (GUI, 2026-11-02) — okno „Błąd konwersji” (Illegal trailing comma…, odesłanie do converter.log), status „Konwersja nie powiodła się.”, output/bledne.csv nie powstał; zrzut: docs/zrzuty/R7_bledne_json.png |
| R8 | data/bledne.csv → JSON | Błąd nadmiarowego pola; brak nowego wyniku | ZALICZONY (GUI, 2026-11-02) — okno „Błąd konwersji”: „Rekord 1 ma więcej pól niż nagłówek.”, status „Konwersja nie powiodła się.”, output/bledne.json nie powstał; zrzut: docs/zrzuty/R8_bledne_csv.png |
| R9 | Wybór pliku .zip | Pusta/zablokowana lista formatów, konwersja niedostępna | ZALICZONY (GUI, 2026-11-02) — data/tekst.zip: lista formatów pusta i zablokowana, „Zapisz jako…” i „Konwertuj” nieaktywne, komunikat „Brak konwertera dla wybranego typu pliku.”; available_targets zwraca []; zrzut: docs/zrzuty/R9_zip.png |
| R10 | Brak LibreOffice: podstaw mock find_libreoffice zgłaszający FileNotFoundError i uruchom ODT → PDF | Komunikat z instrukcją instalacji, bez awarii; nie odinstalowuj programu | ZALICZONY (GUI z mockiem, 2026-11-02) — tekst.odt → output/tekst.pdf: okno „Nie znaleziono LibreOffice. Zainstaluj program lub popraw LIBREOFFICE_PATH.”, status „Konwersja nie powiodła się.”, GUI działa dalej, wynik nie powstał; czerwony traceback w IDLE to zalogowany wyjątek, nie awaria; zrzut: docs/zrzuty/R10_brak_libreoffice.png |
| R11 | Istniejący wynik, odpowiedź Nie | Zawartość pliku pozostaje bez zmian | ZALICZONY (GUI, 2026-11-02) — okno „Plik już istnieje” (Nadpisz / Zmień nazwę… / Anuluj), po „Anuluj” status „Anulowano konwersję.”, plik bez zmian; zrzuty: docs/zrzuty/R11_R12_dialog_nadpisania.png, docs/zrzuty/R11_anuluj.png |
| R12 | Istniejący wynik, odpowiedź Tak | Wynik zastąpiony poprawną konwersją | ZALICZONY (GUI, 2026-11-02) — po „Nadpisz” komunikat „Konwersja zakończona”, output/dane.json poprawny (zgodny z examples/wyniki/dane.json); zrzut: docs/zrzuty/R12_nadpisz.png |
| R13 | Błędny plik i istniejący wynik, zgoda na nadpisanie | Błąd konwersji; poprzedni wynik pozostaje bez zmian | ZALICZONY (GUI, 2026-11-02) — data/bledne.json → istniejący output/dane.csv z „Nadpisz”: okno „Błąd konwersji”, output/dane.csv bajtowo bez zmian (zgodny z wynikiem R2); także skryptem; zrzut: docs/zrzuty/R13_bledny_nadpisanie.png |
| R14 | Katalog bez prawa zapisu | Kontrolowany komunikat, brak awarii | ZALICZONY (GUI z mockiem, 2026-11-02) — converters.convert podstawiony mockiem zgłaszającym PermissionError (bez zmiany uprawnień katalogu); okno „Brak uprawnień do zapisu w wybranym katalogu. Wybierz inny katalog docelowy.”, status „Konwersja nie powiodła się.”, GUI działa dalej, wyjątek zalogowany; zrzut: docs/zrzuty/R14_brak_uprawnien.png |
| R15 | Dłuższa konwersja dokumentu | GUI reaguje, wybory zablokowane, stan pracy widoczny | ZALICZONY (GUI, 2026-11-02) — w trakcie konwersji output/asd.csv → JSON: „Wybierz plik…”, format, „Zapisz jako…” i „Konwertuj” zablokowane, pasek postępu w ruchu, status „Trwa konwersja: asd.csv → .json”, próba zamknięcia okna daje ostrzeżenie „Poczekaj na zakończenie konwersji…” (okno reaguje); po zakończeniu kontrolki odblokowane i kolejna konwersja działa; zrzuty: docs/zrzuty/R15_dluga_konwersja.png, docs/zrzuty/R15_po_konwersji.png |
| R16 | Nowe środowisko według README | Instalacja i uruchomienie bez nieopisanych kroków | ZALICZONY (2026-11-02) — świeże venv (.venv-check, Python 3.14), pip install -r requirements.txt bez błędów (python-docx 1.2.0, docx2pdf 0.1.8, pywin32 312 + zależności), src\gui.py uruchamia się do stanu początkowego „Wybierz plik do konwersji.”; LibreOffice zainstalowany wcześniej (README opisuje go jako osobny krok); zrzut: docs/zrzuty/R16_nowe_srodowisko.png |
| R17 | Pozostałe deklarowane pary: TXT → PDF, DOCX → PDF, ODT → DOCX | Każdy wynik otwieralny i zawiera oczekiwany tekst | ZALICZONY (2026-11-02) — tekst_docx.pdf (przez Word) i tekst_odt.docx (Word) otwarte, oba akapity z polskimi znakami i pustą linią; tekst_txt.pdf otwarty: oba akapity z polskimi znakami; zrzuty: docs/zrzuty/R6_R17_podglad_wynikow.png, docs/zrzuty/R4_R17_txt_pdf.png |