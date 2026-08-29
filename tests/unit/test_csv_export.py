import csv

from source.backend.adapters.storage.csv_export import (
    EXPORT_CSV,
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


def test_export_writes_scoring_columns(tmp_path):
    profiles = [
        {
            "nom": "Marie Dupont",
            "url": "https://www.linkedin.com/in/marie-dupont",
            "localisation": "Paris",
            "titre": "Coach business certifiée ICF",
            "categorie": "coach_business_indifferencie",
            "score": "85",
            "justification": "base_coach +20 (coach) | focus_business +40 (coach business)",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == PROFILE_CSV_FIELDS
    assert rows[0]["categorie"] == "coach_business_indifferencie"
    assert rows[0]["score"] == "85"
    assert rows[0]["justification"].startswith("base_coach +20")
    # Filled in by the client, blank when we export.
    assert rows[0]["commentaire_client"] == ""


def test_export_defaults_missing_scoring_columns_to_empty_string(tmp_path):
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
        rows = list(csv.DictReader(f))

    assert rows[0]["categorie"] == ""
    assert rows[0]["score"] == ""
    assert rows[0]["justification"] == ""
    assert rows[0]["commentaire_client"] == ""


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


def test_export_writes_store_columns(tmp_path):
    profiles = [
        {
            "nom": "Marie Dupont",
            "url": "https://www.linkedin.com/in/marie-dupont",
            "localisation": "Paris",
            "titre": "Coach business",
            "date_collecte": "2026-08-26",
            "ne_plus_traiter": "0",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # POC-006: the CSV is a view of the store, RGPD columns included so the
    # client can express an objection directly in the file.
    assert reader.fieldnames == PROFILE_CSV_FIELDS
    assert rows[0]["date_collecte"] == "2026-08-26"
    assert rows[0]["ne_plus_traiter"] == "0"


def test_export_defaults_missing_store_columns_to_empty_string(tmp_path):
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
        rows = list(csv.DictReader(f))

    assert rows[0]["date_collecte"] == ""
    assert rows[0]["ne_plus_traiter"] == ""


def test_export_writes_poc009_columns(tmp_path):
    profiles = [
        {
            "nom": "Marie Dupont",
            "url": "https://www.linkedin.com/in/marie-dupont",
            "localisation": "Paris",
            "titre": "Coach business",
            "email_web": "marie@mycoach.fr",
            "site_web": "mycoach.fr",
            "date_visite_email": "2026-08-28",
            "date_enrichissement_web": "2026-08-28",
            "statut_coordonnees": "candidat",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # POC-009: the status is exported because that is how the human review
    # comes back into the store, exactly like commentaire_client.
    assert reader.fieldnames == PROFILE_CSV_FIELDS
    assert rows[0]["date_visite_email"] == "2026-08-28"
    assert rows[0]["date_enrichissement_web"] == "2026-08-28"
    assert rows[0]["statut_coordonnees"] == "candidat"


def test_export_defaults_missing_poc009_columns_to_empty_string(tmp_path):
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
        rows = list(csv.DictReader(f))

    assert rows[0]["date_visite_email"] == ""
    assert rows[0]["date_enrichissement_web"] == ""
    assert rows[0]["statut_coordonnees"] == ""


def test_export_csv_est_le_fichier_unique_partage_par_les_scripts():
    # POC-009 hygiene point: run_poc001 wrote profils_extraits.csv and
    # run_poc003 profils_extraits_scores.csv - two names for two views of the
    # same store. One name now, and it says what the file is.
    assert EXPORT_CSV.name == "profils_magasin.csv"


def test_export_preserves_emoji_in_names(tmp_path):
    # Real LinkedIn names carry emoji (two such profiles in the store,
    # 28/08/2026). They broke the console output of a run script; the data
    # path must stay UTF-8 clean whatever the console can display.
    profiles = [
        {
            "nom": "Charlotte Leveque🔥Coaching Professionnel",
            "url": "https://www.linkedin.com/in/charlotte-leveque",
            "localisation": "Lille",
            "titre": "Coach business",
        }
    ]
    output_path = tmp_path / "profils.csv"

    export_profiles_to_csv(profiles, output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["nom"] == "Charlotte Leveque🔥Coaching Professionnel"
