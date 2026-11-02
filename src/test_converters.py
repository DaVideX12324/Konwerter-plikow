import csv
import json
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from converters import (
    available_targets,
    csv_check,
    csv_to_json,
    json_to_csv,
    validate_paths,
)

class TestCsvCheck(unittest.TestCase):
    def check_csv(self, content):
        reader = csv.DictReader(StringIO(content), strict=True)
        headers = reader.fieldnames
        data = list(reader)

        csv_check(headers, data)

    def test_valid_csv(self):
        self.check_csv("imie,wiek\nAdam,20\nOla,21\n")

    def test_empty_value(self):
        self.check_csv("imie,wiek\nAdam,\n")

    def test_headers_only(self):
        self.check_csv("imie,wiek\n")

    def test_missing_headers(self):
        with self.assertRaises(ValueError):
            self.check_csv("")

    def test_empty_column_name(self):
        with self.assertRaises(ValueError):
            self.check_csv("imie,\nAdam,20\n")

    def test_whitespace_column_name(self):
        with self.assertRaises(ValueError):
            self.check_csv("imie,   \nAdam,20\n")

    def test_duplicate_headers(self):
        with self.assertRaises(ValueError):
            self.check_csv("imie,imie\nAdam,Ola\n")

    def test_extra_field(self):
        with self.assertRaises(ValueError):
            self.check_csv("imie,wiek\nAdam,20,Krakow\n")

    def test_missing_field(self):
        with self.assertRaises(ValueError):
            self.check_csv("imie,wiek\nAdam\n")


class TestCsvJsonConversion(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)

    def test_csv_to_json(self):
        source = self.directory / "wejscie.csv"
        target = self.directory / "wynik.json"

        source.write_text(
            "imię,miasto,uwagi\nŁukasz,Łódź,\n",
            encoding="utf-8",
        )

        result = csv_to_json(source, target)

        self.assertEqual(result, target)
        self.assertTrue(target.is_file())

        with target.open(encoding="utf-8") as file:
            data = json.load(file)

        self.assertEqual(
            data,
            [{"imię": "Łukasz", "miasto": "Łódź", "uwagi": ""}],
        )
        self.assertEqual(
            list(data[0].keys()),
            ["imię", "miasto", "uwagi"],
        )

    def test_json_to_csv(self):
        source = self.directory / "wejscie.json"
        target = self.directory / "wynik.csv"

        data = [
            {"imię": "Łukasz", "miasto": "Łódź", "uwagi": ""},
        ]

        source.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )

        result = json_to_csv(source, target)

        self.assertEqual(result, target)
        self.assertTrue(target.is_file())

        with target.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            records = list(reader)

        self.assertEqual(headers, ["imię", "miasto", "uwagi"])
        self.assertEqual(records, data)

    def test_csv_to_json_rejects_extra_field(self):
        source = self.directory / "bledne.csv"
        target = self.directory / "wynik.json"

        source.write_text(
            "imie,wiek\nAdam,20,Krakow\n",
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            csv_to_json(source, target)

        self.assertFalse(target.exists())


class TestValidatePaths(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)

        self.source = self.directory / "wejscie.csv"
        self.source.write_text(
            "imie\nAdam\n",
            encoding="utf-8",
        )

        self.target = self.directory / "wynik.json"

    def test_valid_paths(self):
        validate_paths(self.source, self.target)

    def test_missing_input(self):
        missing = self.directory / "brak.csv"

        with self.assertRaises(FileNotFoundError):
            validate_paths(missing, self.target)

    def test_missing_output_directory(self):
        target = self.directory / "brak_katalogu" / "wynik.json"

        with self.assertRaises(NotADirectoryError):
            validate_paths(self.source, target)

    def test_output_is_directory(self):
        with self.assertRaises(IsADirectoryError):
            validate_paths(self.source, self.directory)

    def test_input_equals_output(self):
        with self.assertRaises(ValueError):
            validate_paths(self.source, self.source)

class TestAvailableTargets(unittest.TestCase):
    def test_csv_targets(self):
        self.assertEqual(
            available_targets(Path("dane.csv")),
            [".json"],
        )

    def test_json_targets(self):
        self.assertEqual(
            available_targets(Path("dane.json")),
            [".csv"],
        )

    def test_docx_targets(self):
        self.assertEqual(
            available_targets(Path("dokument.docx")),
            [".odt", ".pdf", ".txt"],
        )

    def test_uppercase_extension(self):
        self.assertEqual(
            available_targets(Path("DANE.CSV")),
            [".json"],
        )

    def test_unsupported_extension(self):
        self.assertEqual(
            available_targets(Path("archiwum.zip")),
            [],
        )

    def test_missing_extension(self):
        self.assertEqual(
            available_targets(Path("plik")),
            [],
        )
        
if __name__ == "__main__":
    unittest.main(verbosity=2)
