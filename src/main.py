import argparse
import converters
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

def main():
    parser = argparse.ArgumentParser(
        description="Konwerter plików CSV i JSON."
    )

    parser.add_argument("input_file", nargs="?")
    parser.add_argument("output_file", nargs="?")

    args = parser.parse_args()
    
    if args.input_file is None:
        while args.input_file is None:
            entered_file = input(
                "Podaj plik wejściowy (? = pokaż dostępne pliki): "
            ).strip()

            if entered_file == "?":
                show_available_files()
            elif entered_file:
                args.input_file = entered_file
            else:
                print("Nazwa pliku nie może być pusta.")

    if args.output_file is None:
        args.output_file = input("Podaj plik wyjściowy: ").strip()
        
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = converters.convert(
            input_path,
            output_path
        )
        print(f"Utworzono plik: {result}")

    except (ValueError, FileNotFoundError) as error:
        print(f"Błąd: {error}")
    pause()


def show_available_files():
    print("\nPliki w data/:")
    for file in sorted(DATA_DIR.glob("*")):
        if file.is_file():
            print(f"  {file.name}")

    print("\nPliki w output/:")
    for file in sorted(OUTPUT_DIR.glob("*")):
        if file.is_file():
            print(f"  {file.name}")

def pause():
    input("\nNaciśnij Enter, aby zamknąć program...")








    
if __name__ == "__main__":
    main()

