import csv
import json
from pathlib import Path


def csv_to_json(csv_file_path, json_file_path):
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        data = list(csv.DictReader(csvfile))

    with open(json_file_path, mode='w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        
    return json_file_path

def json_to_csv(json_file_path, csv_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    json_check(data)
    
    headers = list(data[0].keys())
    
    with open(csv_file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
    return csv_file_path

def json_check(data):
            
    if not isinstance(data, list):
        raise ValueError("JSON musi zawierać listę rekordów.")
    
    if not data:
        raise ValueError("JSON nie zawiera rekordów — nie można utworzyć CSV.")        

    if not isinstance(data[0], dict):
        raise ValueError("Każdy rekord JSON musi być obiektem.")



REGISTRY = {
    (".csv", ".json"): csv_to_json,
    (".json", ".csv"): json_to_csv,
}


def convert(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    key = (input_path.suffix.lower(), output_path.suffix.lower())
    if key not in REGISTRY:
        raise ValueError(
            f"Nieobsługiwana konwersja: {key[0]} -> {key[1]}"
        )

    converter = REGISTRY[key]

    return converter(input_path, output_path)
    
