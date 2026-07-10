import csv

from source.backend.adapters.storage.csv_export import (
    PROFILE_CSV_FIELDS,
    export_profiles_to_csv,
)


def test_export_writes_expected_fields_including_email(tmp_path):
    profiles = [
        {
            "nom": "Marie Dupont",
            "url": "https://www.linkedin.com/in/marie-dupont",
            "localisation": "Paris, Île-de-France",
            "titre": "Coach business expérimentée",
            "email": "marie.dupont@example.com",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == PROFILE_CSV_FIELDS
    assert "email" in reader.fieldnames
    assert rows[0]["nom"] == "Marie Dupont"
    assert rows[0]["localisation"] == "Paris, Île-de-France"
    assert rows[0]["email"] == "marie.dupont@example.com"


def test_export_defaults_missing_email_to_empty_string(tmp_path):
    profiles = [
        {
            "nom": "Jean Martin",
            "url": "https://www.linkedin.com/in/jean-martin",
            "localisation": "Lyon",
            "titre": "Coach business",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows[0]["email"] == ""


def test_export_defaults_missing_email_web_and_site_web_to_empty_string(tmp_path):
    profiles = [
        {
            "nom": "Jean Martin",
            "url": "https://www.linkedin.com/in/jean-martin",
            "localisation": "Lyon",
            "titre": "Coach business",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == PROFILE_CSV_FIELDS
    assert rows[0]["email_web"] == ""
    assert rows[0]["site_web"] == ""


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
