"""Tests for the xlsx deliverable and its return trip (POC-013).

What these tests really guard is not the conversion code but what Excel does
to the data in transit: csv.DictReader yields str, openpyxl yields int, float,
datetime and None. Several tests below therefore forge a workbook with those
native types on purpose, because that is what a real Excel round trip
produces.
"""

import csv
from datetime import datetime

import pytest
from openpyxl import Workbook, load_workbook

from source.backend.adapters.storage.csv_export import (
    PROFILE_CSV_FIELDS,
    export_profiles_to_csv,
)
from source.backend.adapters.storage.profile_store import (
    RapportReimport,
    enregistrer_profils,
    importer_commentaires_csv,
    lister_profils,
    ouvrir_magasin,
)
from source.backend.adapters.storage.run_poc006 import _afficher_rapport, _resoudre_source
from source.backend.adapters.storage.xlsx_export import (
    EnteteXlsxInvalide,
    convertir_csv_en_xlsx,
    lire_xlsx,
    xlsx_vers_csv,
)

# Two of the store's real profiles carry an emoji in their name - that is what
# crashed a POC-009 run on a cp1252 console. justification is deliberately the
# long, separator-laden column it is in production.
PROFILS_REELS = [
    {
        "nom": "Marie Dupont 🌿",
        "url": "https://www.linkedin.com/in/marie-dupont",
        "localisation": "Remiremont, Grand Est",
        "titre": "Coach professionnel certifié Coaching Ways France, Level 2 ICF",
        "email": "",
        "email_web": "marie@example.com",
        "site_web": "https://example.com",
        "categorie": "coach_business",
        "score": "75",
        "justification": "cible_business (+10) ; certification_icf (+40) ; coach (+20) ; total borné à 75",
        "commentaire_client": "",
        "date_collecte": "2026-08-26",
        "ne_plus_traiter": "0",
        "date_visite_email": "2026-08-28",
        "date_enrichissement_web": "2026-08-28",
        "statut_coordonnees": "candidat",
    },
    {
        "nom": "Jean Martin ⚡",
        "url": "https://www.linkedin.com/in/jean-martin",
        "localisation": "Paris, Île-de-France",
        "titre": "Executive coach & mentor",
        "email": "jean.martin@example.org",
        "email_web": "",
        "site_web": "",
        "categorie": "coach_business",
        "score": "85",
        "justification": "coach (+20), cible_business (+10), executive (+15)",
        "commentaire_client": "Profil déjà connu, à recontacter",
        "date_collecte": "2026-07-07",
        "ne_plus_traiter": "0",
        "date_visite_email": "2026-08-28",
        "date_enrichissement_web": "",
        "statut_coordonnees": "valide",
    },
]


def _ecrire_csv(tmp_path, profils=PROFILS_REELS):
    """Produce a CSV export exactly as the pipeline does."""
    chemin = tmp_path / "profils_magasin.csv"
    export_profiles_to_csv(profils, chemin)
    return chemin


def _lire_csv(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _forger_xlsx(chemin, lignes, entete=None):
    """Write a workbook with native Python types, the way Excel hands them back."""
    classeur = Workbook()
    feuille = classeur.active
    feuille.append(list(entete if entete is not None else PROFILE_CSV_FIELDS))
    for ligne in lignes:
        feuille.append(ligne)
    classeur.save(chemin)
    return chemin


# --- 1-2. Fidelity of the conversion -------------------------------------


def test_aller_retour_rend_les_memes_dictionnaires_que_le_csv(tmp_path):
    """CSV -> xlsx -> rows must equal what csv.DictReader gives on the source."""
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "profils_magasin.xlsx"

    convertir_csv_en_xlsx(csv_source, xlsx)

    assert lire_xlsx(xlsx) == _lire_csv(csv_source)


def test_entete_du_xlsx_est_les_17_colonnes_dans_l_ordre(tmp_path):
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "profils_magasin.xlsx"

    convertir_csv_en_xlsx(csv_source, xlsx)

    feuille = load_workbook(xlsx, read_only=True).worksheets[0]
    entete = [c.value for c in next(feuille.iter_rows(max_row=1))]
    assert entete == PROFILE_CSV_FIELDS
    assert len(entete) == 17


# --- 3-4. What Excel does to the values ----------------------------------


def test_cellule_vide_est_relue_en_chaine_vide_jamais_none(tmp_path):
    """_importer_statut_coordonnees calls .strip().lower(): None would raise."""
    xlsx = _forger_xlsx(tmp_path / "vide.xlsx", [[None] * len(PROFILE_CSV_FIELDS)])
    # Give the row one non-empty cell, otherwise it is a blank row.
    classeur = load_workbook(xlsx)
    classeur.worksheets[0]["B2"] = "https://www.linkedin.com/in/x"
    classeur.save(xlsx)

    ligne = lire_xlsx(xlsx)[0]

    assert ligne["statut_coordonnees"] == ""
    assert ligne["commentaire_client"] == ""
    assert all(isinstance(v, str) for v in ligne.values())
    assert ligne["statut_coordonnees"].strip().lower() == ""


def test_types_natifs_excel_sont_ramenes_en_texte(tmp_path):
    """int, float, datetime and None are what openpyxl really yields."""
    ligne = [
        "Marie Dupont",                      # nom
        "https://www.linkedin.com/in/marie", # url
        "Remiremont",                        # localisation
        None,                                # departement
        "Coach",                             # titre
        None,                                # email
        None,                                # email_web
        None,                                # site_web
        "coach_business",                    # categorie
        75.0,                                # score, retyped as a float by Excel
        "cible_business (+10)",              # justification
        "avis client",                       # commentaire_client
        datetime(2026, 8, 26),               # date_collecte, retyped as a date
        0,                                   # ne_plus_traiter, retyped as an int
        datetime(2026, 8, 28),               # date_visite_email
        None,                                # date_enrichissement_web
        "Valide",                            # statut_coordonnees, capitalised
    ]
    xlsx = _forger_xlsx(tmp_path / "excel.xlsx", [ligne])

    relue = lire_xlsx(xlsx)[0]

    assert relue["score"] == "75"          # not "75.0"
    assert relue["date_collecte"] == "2026-08-26"  # not a serial, not 26/08/2026
    assert relue["ne_plus_traiter"] == "0"
    assert relue["date_visite_email"] == "2026-08-28"
    assert relue["date_enrichissement_web"] == ""
    assert relue["email"] == ""
    # The store compares lowercased strings; the value must survive .lower().
    assert relue["statut_coordonnees"].strip().lower() == "valide"
    assert all(isinstance(v, str) for v in relue.values())


def test_booleen_excel_est_relu_en_minuscules_pour_ne_plus_traiter(tmp_path):
    """Excel writes TRUE; _VALEURS_OPPOSITION accepts the lowercase form."""
    ligne = [""] * len(PROFILE_CSV_FIELDS)
    ligne[PROFILE_CSV_FIELDS.index("url")] = "https://www.linkedin.com/in/marie"
    ligne[PROFILE_CSV_FIELDS.index("ne_plus_traiter")] = True
    xlsx = _forger_xlsx(tmp_path / "bool.xlsx", [ligne])

    assert lire_xlsx(xlsx)[0]["ne_plus_traiter"] == "true"


# --- 5-7. The real data that has already broken a run --------------------


def test_nom_a_emoji_survit_a_l_aller_retour(tmp_path):
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "emoji.xlsx"

    convertir_csv_en_xlsx(csv_source, xlsx)
    lignes = lire_xlsx(xlsx)

    assert lignes[0]["nom"] == "Marie Dupont 🌿"
    assert lignes[1]["nom"] == "Jean Martin ⚡"


def test_justification_longue_avec_separateurs_survit(tmp_path):
    profil = dict(PROFILS_REELS[0])
    profil["justification"] = "règle A (+10) ; règle B (−25), règle C\nsuite de la ligne"
    csv_source = _ecrire_csv(tmp_path, [profil])
    xlsx = tmp_path / "justif.xlsx"

    convertir_csv_en_xlsx(csv_source, xlsx)

    assert lire_xlsx(xlsx)[0]["justification"] == profil["justification"]


def test_url_reste_du_texte_et_une_valeur_en_egal_n_est_pas_une_formule(tmp_path):
    profil = dict(PROFILS_REELS[0])
    profil["commentaire_client"] = "=SOMME(A1:A2) à ne pas évaluer"
    csv_source = _ecrire_csv(tmp_path, [profil])
    xlsx = tmp_path / "formule.xlsx"

    convertir_csv_en_xlsx(csv_source, xlsx)

    feuille = load_workbook(xlsx).worksheets[0]
    assert feuille["B2"].data_type == "s"
    assert feuille["L2"].data_type == "s"  # commentaire_client, not a formula
    relue = lire_xlsx(xlsx)[0]
    assert relue["url"] == profil["url"]
    assert relue["commentaire_client"] == profil["commentaire_client"]


# --- 8-11. A non-conforming header is reported, never guessed ------------


def test_colonne_inseree_par_le_client_bloque_la_relecture(tmp_path):
    entete = PROFILE_CSV_FIELDS[:5] + ["priorite"] + PROFILE_CSV_FIELDS[5:]
    xlsx = _forger_xlsx(tmp_path / "insere.xlsx", [["x"] * 17], entete=entete)

    with pytest.raises(EnteteXlsxInvalide, match="priorite"):
        lire_xlsx(xlsx)


def test_colonne_supprimee_par_le_client_bloque_la_relecture(tmp_path):
    entete = [c for c in PROFILE_CSV_FIELDS if c != "justification"]
    xlsx = _forger_xlsx(tmp_path / "supprime.xlsx", [["x"] * len(entete)], entete=entete)

    with pytest.raises(EnteteXlsxInvalide, match="justification"):
        lire_xlsx(xlsx)


def test_colonnes_reordonnees_par_le_client_bloquent_la_relecture(tmp_path):
    """The dangerous case: same names, so nothing is missing or unknown."""
    entete = list(reversed(PROFILE_CSV_FIELDS))
    xlsx = _forger_xlsx(tmp_path / "reordonne.xlsx", [["x"] * len(entete)], entete=entete)

    with pytest.raises(EnteteXlsxInvalide, match="reordonnees"):
        lire_xlsx(xlsx)


def test_classeur_vide_bloque_la_relecture(tmp_path):
    classeur = Workbook()
    chemin = tmp_path / "vide_total.xlsx"
    classeur.save(chemin)

    with pytest.raises(EnteteXlsxInvalide):
        lire_xlsx(chemin)


# --- The intermediate CSV, hinge of the return trip ----------------------


def test_xlsx_vers_csv_reproduit_le_csv_source_a_l_identique(tmp_path):
    """On a workbook nobody annotated, the trace must equal the export."""
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "aller.xlsx"
    csv_retour = tmp_path / "retour.csv"

    convertir_csv_en_xlsx(csv_source, xlsx)
    lignes = xlsx_vers_csv(xlsx, csv_retour)

    assert lignes == len(PROFILS_REELS)
    assert csv_retour.read_bytes() == csv_source.read_bytes()


def test_lignes_vides_ajoutees_par_excel_sont_ignorees(tmp_path):
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "trailing.xlsx"
    convertir_csv_en_xlsx(csv_source, xlsx)

    classeur = load_workbook(xlsx)
    feuille = classeur.worksheets[0]
    feuille.append([None] * len(PROFILE_CSV_FIELDS))
    feuille.append([None] * len(PROFILE_CSV_FIELDS))
    classeur.save(xlsx)

    assert len(lire_xlsx(xlsx)) == len(PROFILS_REELS)


# --- The routing in run_poc006 -------------------------------------------
#
# These tests exercise _resoudre_source and the store, never run_poc006.main:
# main() opens DEFAULT_DB_PATH, which is the real ./profils.db.


def _rejouer_reimport(conn, chemin):
    """Run the two passes of run_poc006.main, in their order, on one file."""
    lignes = _lire_csv(chemin)
    enregistrer_profils(conn, lignes)
    return importer_commentaires_csv(conn, chemin)


def test_resoudre_source_laisse_un_csv_intact(tmp_path):
    csv_source = _ecrire_csv(tmp_path)

    assert _resoudre_source(csv_source) == csv_source


def test_resoudre_source_convertit_un_xlsx_en_csv_voisin(tmp_path):
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "retour_client.xlsx"
    convertir_csv_en_xlsx(csv_source, xlsx)

    trace = _resoudre_source(xlsx)

    assert trace == tmp_path / "retour_client.reimport.csv"
    assert trace.exists()
    assert _lire_csv(trace) == _lire_csv(csv_source)


def test_resoudre_source_ne_mange_pas_un_point_interne_du_nom(tmp_path):
    csv_source = _ecrire_csv(tmp_path)
    xlsx = tmp_path / "retour.v2.xlsx"
    convertir_csv_en_xlsx(csv_source, xlsx)

    assert _resoudre_source(xlsx) == tmp_path / "retour.v2.reimport.csv"


def test_resoudre_source_refuse_un_entete_modifie_sans_rien_ecrire(tmp_path, capsys):
    entete = PROFILE_CSV_FIELDS[:5] + ["priorite"] + PROFILE_CSV_FIELDS[5:]
    xlsx = _forger_xlsx(tmp_path / "casse.xlsx", [["x"] * 17], entete=entete)

    assert _resoudre_source(xlsx) is None
    assert "refuse" in capsys.readouterr().out
    assert not (tmp_path / "casse.reimport.csv").exists()


def test_reimport_xlsx_et_csv_menent_au_meme_etat_de_base(tmp_path):
    """The whole point of the ticket: the format must not change the outcome."""
    annotes = []
    for profil in PROFILS_REELS:
        annote = dict(profil)
        annote["commentaire_client"] = f"avis client sur {profil['nom']}"
        annote["statut_coordonnees"] = "rejete"
        annotes.append(annote)

    csv_source = _ecrire_csv(tmp_path, annotes)
    xlsx = tmp_path / "retour_client.xlsx"
    convertir_csv_en_xlsx(csv_source, xlsx)

    etats = []
    for source in (csv_source, _resoudre_source(xlsx)):
        conn = ouvrir_magasin(tmp_path / f"{source.name}.db")
        try:
            enregistrer_profils(conn, _lire_csv(csv_source))
            # Blank the feedback so the re-import has something to write.
            conn.execute("UPDATE profils SET commentaire_client = '', statut_coordonnees = ''")
            conn.commit()
            rapport = _rejouer_reimport(conn, source)
            etats.append(([dict(p) for p in lister_profils(conn)], rapport))
        finally:
            conn.close()

    (profils_csv, rapport_csv), (profils_xlsx, rapport_xlsx) = etats
    assert profils_xlsx == profils_csv
    assert rapport_xlsx == rapport_csv
    assert sorted(rapport_xlsx.commentaires_ajoutes) == sorted(p["url"] for p in annotes)
    assert rapport_xlsx.statuts_refuses == []


def test_le_rapport_annonce_les_statuts_tranches_et_refuses(capsys):
    """Found by the real POC-013 round trip: both blocks were missing.

    RapportReimport has carried the two fields since POC-009 and
    _importer_statut_coordonnees fills them, but run_poc006 printed neither -
    so a client ruling entered the store with no trace, and an unrecognised
    one was dropped in silence, which the POC-009 rule forbids.
    """
    rapport = RapportReimport()
    rapport.statuts_tranches.append(("https://www.linkedin.com/in/eric", "rejete"))
    rapport.statuts_refuses.append(("https://www.linkedin.com/in/marie", "ok"))

    _afficher_rapport(rapport)
    sortie = capsys.readouterr().out

    assert "1 statuts de coordonnees tranches" in sortie
    assert "https://www.linkedin.com/in/eric -> rejete" in sortie
    assert "REFUSES" in sortie
    assert "https://www.linkedin.com/in/marie" in sortie
    assert "'ok'" in sortie


# --- POC-015: the derived departement column and the return trip ---------


def _profils_localises():
    """PROFILS_REELS with locations in the three-part form LinkedIn mostly gives."""
    strasbourg = dict(PROFILS_REELS[0], localisation="Strasbourg, Grand Est, France")
    peripherie = dict(PROFILS_REELS[1], localisation="Paris et périphérie")
    return [strasbourg, peripherie]


def _etat_du_magasin(conn):
    return {p["url"]: dict(p) for p in lister_profils(conn)}


def test_departement_est_une_cellule_texte_du_classeur(tmp_path):
    csv_source = _ecrire_csv(tmp_path, _profils_localises())
    xlsx = tmp_path / "departement.xlsx"

    convertir_csv_en_xlsx(csv_source, xlsx)

    feuille = load_workbook(xlsx).worksheets[0]
    assert feuille["D1"].value == "departement"
    assert feuille["D2"].value == "67 - Bas-Rhin"
    assert feuille["D2"].number_format == "@"
    # Not attachable: an empty cell, not a guessed "75 - Paris".
    assert lire_xlsx(xlsx)[1]["departement"] == ""


def test_classeur_annote_ne_modifie_que_commentaire_et_statut(tmp_path):
    """The POC-013 loop still holds with the 17th column, even if it was edited."""
    profils = _profils_localises()
    conn = ouvrir_magasin(tmp_path / "profils.db")
    try:
        enregistrer_profils(conn, profils)
        conn.execute("UPDATE profils SET statut_coordonnees = 'candidat'")
        conn.commit()
        avant = _etat_du_magasin(conn)

        csv_source = _ecrire_csv(tmp_path, lister_profils(conn))
        xlsx = tmp_path / "retour_client.xlsx"
        convertir_csv_en_xlsx(csv_source, xlsx)

        # The client annotates, and also retypes the derived cell.
        classeur = load_workbook(xlsx)
        feuille = classeur.worksheets[0]
        colonne = {c.value: c.column for c in feuille[1]}
        url_annotee = feuille.cell(row=2, column=colonne["url"]).value
        feuille.cell(row=2, column=colonne["commentaire_client"], value="bon profil")
        feuille.cell(row=2, column=colonne["statut_coordonnees"], value="valide")
        feuille.cell(row=2, column=colonne["departement"], value="88 - Vosges")
        feuille.cell(row=3, column=colonne["departement"], value="75 - Paris")
        classeur.save(xlsx)

        _rejouer_reimport(conn, _resoudre_source(xlsx))
        apres = _etat_du_magasin(conn)
    finally:
        conn.close()

    ecarts = {
        (url, champ)
        for url in avant
        for champ in avant[url]
        if avant[url][champ] != apres[url][champ]
    }
    assert ecarts == {(url_annotee, "commentaire_client"), (url_annotee, "statut_coordonnees")}
    assert all("departement" not in profil for profil in apres.values())


def test_ancien_classeur_sans_departement_est_accepte_et_signale(tmp_path, capsys):
    """A workbook delivered before POC-015 must come back: accepted, and said so."""
    profils = _profils_localises()
    ancien_entete = [c for c in PROFILE_CSV_FIELDS if c != "departement"]
    lignes = [
        [dict(p, commentaire_client="mauvais profil")[c] for c in ancien_entete] for p in profils
    ]
    xlsx = _forger_xlsx(tmp_path / "envoi_septembre.xlsx", lignes, entete=ancien_entete)

    conn = ouvrir_magasin(tmp_path / "profils.db")
    try:
        enregistrer_profils(conn, [dict(p, commentaire_client="") for p in profils])
        trace = _resoudre_source(xlsx)
        sortie = capsys.readouterr().out
        rapport = _rejouer_reimport(conn, trace)
        commentaires = {p["commentaire_client"] for p in lister_profils(conn)}
    finally:
        conn.close()

    assert "Ancien format reconnu" in sortie
    assert "departement" in sortie
    assert len(rapport.commentaires_ajoutes) == len(profils)
    assert commentaires == {"mauvais profil"}
    # The trace carries the current header, the missing column left blank.
    assert list(_lire_csv(trace)[0]) == PROFILE_CSV_FIELDS
    assert {ligne["departement"] for ligne in _lire_csv(trace)} == {""}


def test_classeur_au_format_courant_n_est_pas_annonce_comme_ancien(tmp_path, capsys):
    csv_source = _ecrire_csv(tmp_path, _profils_localises())
    xlsx = tmp_path / "courant.xlsx"
    convertir_csv_en_xlsx(csv_source, xlsx)

    _resoudre_source(xlsx)

    assert "Ancien format" not in capsys.readouterr().out


def test_ancien_format_amoindri_reste_refuse(tmp_path):
    """The tolerance is one exact header, not "any column may be missing"."""
    entete = [c for c in PROFILE_CSV_FIELDS if c not in ("departement", "justification")]
    xlsx = _forger_xlsx(tmp_path / "ampute.xlsx", [["x"] * len(entete)], entete=entete)

    with pytest.raises(EnteteXlsxInvalide, match="justification"):
        lire_xlsx(xlsx)


def test_export_d_un_csv_sans_departement_est_refuse(tmp_path):
    """Strict on the way out: a stale CSV must not become a 16-column deliverable."""
    ancien_entete = [c for c in PROFILE_CSV_FIELDS if c != "departement"]
    csv_perime = tmp_path / "perime.csv"
    with open(csv_perime, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ancien_entete, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(PROFILS_REELS)

    with pytest.raises(EnteteXlsxInvalide, match="departement"):
        convertir_csv_en_xlsx(csv_perime, tmp_path / "perime.xlsx")
    assert not (tmp_path / "perime.xlsx").exists()
