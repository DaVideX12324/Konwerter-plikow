import csv
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


LIBREOFFICE_PATH = Path(
    r"C:\Program Files\LibreOffice\program\soffice.com"
)

REGISTRY = {}


def register(source_format, target_format):
    def decorator(function):
        key = (source_format.lower(), target_format.lower())
        REGISTRY[key] = function
        return function

    return decorator


def available_targets(input_file_path: Path) -> list[str]:
    source_format = Path(input_file_path).suffix.lower()

    return sorted(
        target
        for source, target in REGISTRY
        if source == source_format
    )


def normalize_path(file_path: Path) -> Path:
    return Path(file_path).expanduser().resolve()


def validate_paths(
    input_file_path: Path,
    output_file_path: Path,
) -> None:
    if not input_file_path.is_file():
        raise FileNotFoundError(
            f"Nie znaleziono pliku wejściowego: {input_file_path}"
        )

    if not output_file_path.parent.is_dir():
        raise NotADirectoryError(
            f"Katalog docelowy nie istnieje: {output_file_path.parent}"
        )

    if output_file_path.is_dir():
        raise IsADirectoryError(
            f"Ścieżka wyjściowa wskazuje katalog: {output_file_path}"
        )

    if input_file_path == output_file_path:
        raise ValueError(
            "Plik wejściowy i wyjściowy nie mogą być takie same."
        )


def require_result(
    output_file_path: Path,
    *,
    allow_empty: bool = False,
) -> Path:
    if not output_file_path.is_file():
        raise RuntimeError(
            "Konwerter nie utworzył pliku wynikowego: "
            f"{output_file_path}"
        )

    if not allow_empty and output_file_path.stat().st_size == 0:
        raise RuntimeError(
            f"Konwerter utworzył pusty plik: {output_file_path}"
        )

    return output_file_path


def create_document(input_file_path=None):
    try:
        from docx import Document
    except ImportError as error:
        raise RuntimeError(
            "Brak biblioteki python-docx. "
            "Zainstaluj zależności: "
            "python -m pip install -r requirements.txt"
        ) from error

    if input_file_path is None:
        return Document()

    return Document(input_file_path)

def docx_to_pdf_word(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    try:
        from docx2pdf import convert as word_to_pdf
    except ImportError as error:
        raise RuntimeError(
            "Brak biblioteki docx2pdf. "
            "Zainstaluj zależności: "
            "python -m pip install -r requirements.txt"
        ) from error

    word_to_pdf(input_file_path, output_file_path)

    return require_result(output_file_path)



def find_libreoffice() -> Path:
    if LIBREOFFICE_PATH.is_file():
        return LIBREOFFICE_PATH.resolve()

    if os.name == "nt":
        import winreg

        registry_path = r"SOFTWARE\LibreOffice\UNO\InstallPath"

        for root in (
            winreg.HKEY_CURRENT_USER,
            winreg.HKEY_LOCAL_MACHINE,
        ):
            for view in (
                winreg.KEY_WOW64_64KEY,
                winreg.KEY_WOW64_32KEY,
            ):
                try:
                    with winreg.OpenKey(
                        root,
                        registry_path,
                        0,
                        winreg.KEY_READ | view,
                    ) as key:
                        install_path, _ = winreg.QueryValueEx(key, "")

                except OSError:
                    continue

                if not isinstance(install_path, str):
                    continue

                program_directory = Path(
                    os.path.expandvars(install_path.strip('"'))
                )

                for name in ("soffice.com", "soffice.exe"):
                    executable = program_directory / name

                    if executable.is_file():
                        return executable.resolve()

    for name in ("libreoffice", "soffice"):
        found = shutil.which(name)

        if found:
            return Path(found).resolve()

    macos_path = Path(
        "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    )

    if macos_path.is_file():
        return macos_path.resolve()

    raise FileNotFoundError(
        "Nie znaleziono LibreOffice. "
        "Zainstaluj program i dodaj go do PATH "
        "lub ustaw poprawne LIBREOFFICE_PATH w converters.py."
    )


def run_command(command: list[str], label: str):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )

    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"{label}: przekroczono limit czasu."
        ) from error

    if result.returncode != 0:
        details = (
            result.stderr.strip()
            or result.stdout.strip()
            or f"Kod zakończenia: {result.returncode}"
        )

        raise RuntimeError(f"{label}: {details}")

    return result


def csv_check(headers, data) -> None:
    if not headers:
        raise ValueError("CSV nie zawiera nagłówków.")

    if any(not header.strip() for header in headers):
        raise ValueError("Nazwy kolumn CSV nie mogą być puste.")

    if len(set(headers)) != len(headers):
        raise ValueError(
            "Nazwy kolumn CSV nie mogą się powtarzać."
        )

    for number, record in enumerate(data, start=1):
        if None in record:
            raise ValueError(
                f"Rekord {number} ma więcej pól niż nagłówek."
            )

        if any(value is None for value in record.values()):
            raise ValueError(
                f"Rekord {number} ma mniej pól niż nagłówek."
            )


def json_check(data) -> None:
    if not isinstance(data, list):
        raise ValueError("JSON musi zawierać listę rekordów.")

    if not data:
        raise ValueError(
            "JSON nie zawiera rekordów — nie można utworzyć CSV."
        )

    for number, record in enumerate(data, start=1):
        if not isinstance(record, dict):
            raise ValueError(
                f"Rekord {number} musi być obiektem JSON."
            )

    headers = list(data[0].keys())

    if not headers:
        raise ValueError(
            "Rekordy muszą zawierać przynajmniej jedną kolumnę."
        )

    if any(not header.strip() for header in headers):
        raise ValueError("Nazwy kolumn nie mogą być puste.")

    for number, record in enumerate(data, start=1):
        if set(record.keys()) != set(headers):
            raise ValueError(
                f"Rekord {number} ma inny zestaw kolumn "
                "niż pierwszy rekord."
            )

        for column, value in record.items():
            if isinstance(value, (dict, list)):
                raise ValueError(
                    f"Rekord {number}, kolumna '{column}': "
                    "zagnieżdżone obiekty i listy nie są obsługiwane."
                )


def convert_with_libreoffice(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    source = normalize_path(input_file_path)
    target = normalize_path(output_file_path)

    filters = {
        ".pdf": "pdf:writer_pdf_Export",
        ".docx": "docx:Office Open XML Text",
        ".odt": "odt:writer8",
    }

    extension = target.suffix.lower()

    if extension not in filters:
        raise ValueError(
            "Nieobsługiwany format wyjściowy LibreOffice."
        )

    executable = find_libreoffice()

    with TemporaryDirectory() as directory:
        temporary = Path(directory).resolve()
        profile_uri = (temporary / "profile").as_uri()

        result = run_command(
            [
                str(executable),
                f"-env:UserInstallation={profile_uri}",
                "--headless",
                "--convert-to",
                filters[extension],
                "--outdir",
                str(temporary),
                str(source),
            ],
            "LibreOffice",
        )

        generated = temporary / f"{source.stem}{extension}"

        if not generated.is_file():
            details = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Brak dodatkowych informacji."
            )

            raise RuntimeError(
                "LibreOffice nie utworzył oczekiwanego pliku. "
                f"{details}"
            )

        require_result(generated)
        shutil.copyfile(generated, target)

    return require_result(target)


def convert(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    source = normalize_path(input_file_path)
    target = normalize_path(output_file_path)

    validate_paths(source, target)

    key = (source.suffix.lower(), target.suffix.lower())

    if key not in REGISTRY:
        raise ValueError(
            f"Nieobsługiwana konwersja: {key[0]} -> {key[1]}"
        )

    converter = REGISTRY[key]

    with TemporaryDirectory(
        dir=target.parent,
        prefix=".conversion-",
    ) as directory:
        temporary_file = Path(directory) / target.name

        converter(source, temporary_file)

        require_result(
            temporary_file,
            allow_empty=target.suffix.lower() == ".txt",
        )

        os.replace(temporary_file, target)

    return target


@register(".csv", ".json")
def csv_to_json(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    with open(
        input_file_path,
        mode="r",
        newline="",
        encoding="utf-8-sig",
    ) as csvfile:
        reader = csv.DictReader(csvfile, strict=True)
        headers = reader.fieldnames
        data = list(reader)

    csv_check(headers, data)

    with open(
        output_file_path,
        mode="w",
        encoding="utf-8",
    ) as jsonfile:
        json.dump(
            data,
            jsonfile,
            ensure_ascii=False,
            indent=4,
        )

    return require_result(output_file_path)


@register(".json", ".csv")
def json_to_csv(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    with open(
        input_file_path,
        mode="r",
        encoding="utf-8",
    ) as jsonfile:
        data = json.load(jsonfile)

    json_check(data)

    headers = list(data[0].keys())

    with open(
        output_file_path,
        mode="w",
        newline="",
        encoding="utf-8-sig",
    ) as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=headers,
        )
        writer.writeheader()
        writer.writerows(data)

    return require_result(output_file_path)



@register(".odt", ".pdf")
def odt_to_pdf(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    return convert_with_libreoffice(
        input_file_path,
        output_file_path,
    )


@register(".docx", ".odt")
def docx_to_odt(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    return convert_with_libreoffice(
        input_file_path,
        output_file_path,
    )


@register(".odt", ".docx")
def odt_to_docx(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    return convert_with_libreoffice(
        input_file_path,
        output_file_path,
    )


@register(".docx", ".pdf")
def docx_to_pdf(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    try:
        return docx_to_pdf_word(
            input_file_path,
            output_file_path,
        )

    except Exception as word_error:
        logging.warning(
            "Word zawiódł, próba LibreOffice. Błąd: %s",
            word_error,
        )

        return convert_with_libreoffice(
            input_file_path,
            output_file_path,
        )


@register(".txt", ".docx")
def txt_to_docx(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    doc = create_document()

    with open(
        input_file_path,
        mode="r",
        encoding="utf-8-sig",
    ) as file:
        for line in file:
            doc.add_paragraph(line.rstrip("\r\n"))

    doc.save(output_file_path)

    return require_result(output_file_path)
    
    
@register(".txt", ".odt")
def txt_to_odt(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    with TemporaryDirectory() as directory:
        temporary_docx = Path(directory) / "document.docx"

        txt_to_docx(
            input_file_path,
            temporary_docx,
        )
        docx_to_odt(
            temporary_docx,
            output_file_path,
        )

    return require_result(output_file_path)

@register(".txt", ".pdf")
def txt_to_pdf(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    with TemporaryDirectory() as directory:
        temporary_docx = Path(directory) / "document.docx"

        txt_to_docx(
            input_file_path,
            temporary_docx,
        )
        docx_to_pdf(
            temporary_docx,
            output_file_path,
        )

    return require_result(output_file_path)


@register(".docx", ".txt")
def docx_to_txt(
    input_file_path: Path,
    output_file_path: Path,
) -> Path:
    doc = create_document(input_file_path)

    with open(
        output_file_path,
        mode="w",
        encoding="utf-8",
    ) as file:
        for paragraph in doc.paragraphs:
            file.write(paragraph.text + "\n")

    return require_result(
        output_file_path,
        allow_empty=True,
    )