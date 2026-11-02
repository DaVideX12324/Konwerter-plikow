# Dane testowe

Pliki tekstowe zapisano w UTF-8.

| Plik | Próba | Oczekiwany wynik |
|---|---|---|
| dane.csv | CSV → JSON | 10 rekordów; kolumny id, imie, nazwisko, miasto, ulubiony_napoj, notatka; znaki PL, FR, DA, TR, cyrylica, chińskie, emoji; puste pola: napój w rekordzie 8, notatka w rekordzie 9. |
| a.json | JSON → CSV | Te same 6 kolumn i 10 rekordów co dane.csv (zgodny z wynikiem CSV → JSON), zachowane wszystkie znaki. |
| tekst.txt | TXT → DOCX; następnie konwersje biurowe | Tekst „Zażółć gęślą jaźń.” i „Drugi akapit: Łódź, Gdańsk, Żaneta.”; między nimi pusta linia. |
| bledne.csv | CSV → JSON | ValueError: rekord ma więcej pól niż nagłówek. |
| bledne.json | JSON → CSV | Kontrolowany błąd parsowania JSON. |
| tekst.zip | Wybór w GUI | Nieobsługiwany typ: pusta, zablokowana lista formatów, konwersja niedostępna. |

Wyniki konwersji tych plików są w examples/wyniki/, a ich ocena w docs/raport-testow.md.
