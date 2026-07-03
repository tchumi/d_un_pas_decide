import csv

from source.backend.adapters.storage.csv_export import (
    PROFILE_CSV_FIELDS,
    export_profiles_to_csv,
)


def test_export_writes_expected_fields_and_no_email(tmp_path):
    profiles = [
        {
            "nom": "Marie Dupont",
            "url": "https://www.linkedin.com/in/marie-dupont",
            "localisation": "Paris, Île-de-France",
            "titre": "Coach business expérimentée",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == PROFILE_CSV_FIELDS
    assert "email" not in reader.fieldnames
    assert rows[0]["nom"] == "Marie Dupont"
    assert rows[0]["localisation"] == "Paris, Île-de-France"


def test_export_handles_empty_profile_list(tmp_path):
    output_path = tmp_path / "empty.csv"

    export_profiles_to_csv([], output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows == []
    assert reader.fieldnames == PROFILE_CSV_FIELDS


def test_export_creates_missing_parent_directory(tmp_path):
    output_path = tmp_path / "nested" / "profils.csv"

    export_profiles_to_csv([], output_path)

    assert output_path.exists()
