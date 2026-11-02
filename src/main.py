import argparse
from pathlib import Path
import shlex
import logging

import converters


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

def choose_output_path(output_file_path: Path) -> Path | None:
    if output_file_path.is_dir():
        raise IsADirectoryError(f"Ścieżka wyjściowa wskazuje katalog: {output_file_path}")

    if not output_file_path.exists():
        return output_file_path

    while True:
        answer = input(f"Plik {output_file_path.name} już istnieje. [n]adpisz / [z]mień nazwę / [a]nuluj: ").strip().lower()

        if answer in ("n", "nadpisz"):
            return output_file_path

        if answer in ("z", "zmień", "zmien"):
            number = 1
            candidate = output_file_path.with_name(f"{output_file_path.stem} ({number}){output_file_path.suffix}")

            while candidate.exists():
                number += 1
                candidate = output_file_path.with_name(f"{output_file_path.stem} ({number}){output_file_path.suffix}")

            return candidate

        if answer in ("a", "anuluj"):
            return None

        print("Wpisz n, z lub a.")


def main():
    parser = argparse.ArgumentParser(
        description="Konwerter plików."
    )

    parser.add_argument("input_file", nargs="?")
    parser.add_argument("output_file", nargs="?")

    args = parser.parse_args()
    
    interactive_mode = args.input_file is None or args.output_file is None
    
    input_file = args.input_file
    output_file = args.output_file

    while True:
        while input_file is None:
            entered_file = input(
                "Podaj plik wejściowy lub wejściowy i wyjściowy"
                "(? = pokaż dostępne pliki): "
            ).strip()

            if entered_file == "?":
                show_available_files()
                continue

            if not entered_file:
                print("Nazwa pliku nie może być pusta.")
                continue

            try:
                files = shlex.split(entered_file, posix=False)
            except ValueError:
                print("Nieprawidłowe cudzysłowy w nazwie pliku.")
                continue

            if len(files) > 2:
                print(
                    "Podaj jeden lub dwa pliki. "
                    "Nazwy zawierające spacje umieść w cudzysłowach."
                )
                continue

            # Usuwamy otaczające cudzysłowy pozostawione przez posix=False.
            files = [file.strip("\"'") for file in files]

            if any(not file.strip() for file in files):
                print("Nazwa pliku nie może być pusta.")
                continue

            input_file = files[0]

            if len(files) == 2:
                output_file = files[1]


        while output_file is None:
            entered_file = input("Podaj plik wyjściowy: ").strip()

            # Pozwala wkleić również ścieżkę otoczoną cudzysłowami.
            entered_file = entered_file.strip("\"'")

            if entered_file.strip():
                output_file = entered_file
            else:
                print("Nazwa pliku nie może być pusta.")

        input_path = Path(input_file)
        output_path = Path(output_file)

        if input_path.parent == Path("."):
            data_path = DATA_DIR / input_path
            output_path_candidate = OUTPUT_DIR / input_path

            if data_path.is_file():
                input_path = data_path
            elif output_path_candidate.is_file():
                input_path = output_path_candidate
            else:
                input_path = data_path

        if output_path.parent == Path("."):
            output_path = OUTPUT_DIR / output_path

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            selected_path = choose_output_path(output_path)

            if selected_path is None:
                print("Anulowano konwersję.")
            else:
                result = converters.convert(input_path, selected_path)
                print(f"Utworzono plik: {result}")

        except (ValueError, OSError, RuntimeError, csv.Error) as error:
            logging.exception("Błąd konwersji: %s -> %s", input_path, output_path)
            print(f"Błąd: {error}")

        if not interactive_mode or not ask_next_conversion():
            break

        # W kolejnej iteracji pytamy o nowe pliki.
        input_file = None
        output_file = None

        print()


def ask_next_conversion() -> bool:
    while True:
        answer = input(
            "\nCzy wykonać kolejną konwersję? [t/n]: "
        ).strip().lower()

        if answer in ("t", "tak"):
            return True

        if answer in ("n", "nie"):
            return False

        print("Wpisz t — kolejna konwersja lub n — wyjście.")


def show_available_files():
    print("\nPliki w data/:")
    for file in sorted(DATA_DIR.glob("*")):
        if file.is_file():
            print(f"  {file.name}")

    print("\nPliki w output/:")
    for file in sorted(OUTPUT_DIR.glob("*")):
        if file.is_file():
            print(f"  {file.name}")


if __name__ == "__main__":
    logging.basicConfig(filename=PROJECT_ROOT / "converter.log", encoding="utf-8", level=logging.WARNING, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
