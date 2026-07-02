"""
POC - Recherche de profils LinkedIn via script Python (Playwright)
====================================================================

Objectif : valider qu'on peut extraire, depuis une page de résultats de
recherche LinkedIn, les infos de base (nom, titre, localisation, URL)
pour un petit lot de profils correspondant à une requête donnée.

Principe :
- Le script ouvre une fenêtre Chrome pilotée par Playwright.
- TU te connectes toi-même à LinkedIn dans cette fenêtre (identifiants,
  2FA...). Le script ne manipule jamais ton mot de passe.
- La session est sauvegardée localement (dossier ./browser_profile),
  donc les prochaines exécutions n'auront plus besoin de reconnexion
  tant que la session reste valide.
- Le script va ensuite sur une URL de recherche LinkedIn (à construire
  manuellement une fois dans le navigateur, cf. instructions ci-dessous)
  et extrait les résultats visibles.

IMPORTANT :
- Volume volontairement faible (quelques dizaines de profils, pas plus).
- Pauses aléatoires entre les actions pour rester "humain".
- Ce script ne fait AUCUNE invitation, AUCUN message : lecture seule.
- À faire tourner ponctuellement, pas en tâche de fond H24.

Installation :
    pip install playwright
    playwright install chromium

Usage :
    python linkedin_search_poc.py
"""

import csv
import random
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------

# Colle ici l'URL de recherche LinkedIn une fois que tu l'as construite
# à la main dans ton navigateur (recherche avec ta requête booléenne +
# filtres géographiques), puis copie l'URL depuis la barre d'adresse.
# Exemple de forme :
# https://www.linkedin.com/search/results/people/?keywords=coach%20business
SEARCH_URL = "COLLE_TON_URL_DE_RECHERCHE_ICI"

# Nombre de profils max à extraire pour ce test (reste petit au début)
MAX_PROFILES = 25

# Dossier où la session de connexion est sauvegardée entre deux runs
PROFILE_DIR = Path("./browser_profile")

# Fichier de sortie
OUTPUT_CSV = Path("./profils_extraits.csv")


def pause_humaine(min_s=1.5, max_s=4.0):
    """Petite pause aléatoire pour éviter un rythme trop régulier."""
    time.sleep(random.uniform(min_s, max_s))


def main():
    PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        # Contexte persistant = la session reste sauvegardée localement
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,  # visible, pour pouvoir te connecter à la main
        )
        page = context.new_page()

        print("Ouverture de LinkedIn...")
        page.goto("https://www.linkedin.com/", timeout=60000)

        if "feed" not in page.url and "login" in page.url or "authwall" in page.url:
            input(
                "\n>>> Connecte-toi manuellement dans la fenêtre Chrome qui "
                "s'est ouverte, puis reviens ici et appuie sur Entrée...\n"
            )

        if SEARCH_URL == "COLLE_TON_URL_DE_RECHERCHE_ICI":
            print(
                "\nATTENTION : renseigne SEARCH_URL en haut du script avant "
                "de continuer. Va d'abord faire ta recherche à la main dans "
                "la fenêtre ouverte, copie l'URL, colle-la dans le script, "
                "puis relance.\n"
            )
            input("Appuie sur Entrée pour fermer...")
            context.close()
            return

        print(f"Navigation vers la recherche...")
        page.goto(SEARCH_URL, timeout=60000)
        pause_humaine(2, 4)

        results = []
        page_num = 1

        while len(results) < MAX_PROFILES:
            print(f"Lecture de la page de résultats #{page_num}...")

            # Sélecteurs à ajuster : LinkedIn change régulièrement son DOM.
            # On cible les cartes de résultats de recherche "people".
            cards = page.locator("li.reusable-search__result-container")
            count = cards.count()

            if count == 0:
                print(
                    "Aucun résultat trouvé avec ce sélecteur — la structure "
                    "de la page a probablement changé. Il faudra inspecter "
                    "le DOM (clic droit > Inspecter) et ajuster les "
                    "sélecteurs CSS ci-dessus."
                )
                break

            for i in range(count):
                if len(results) >= MAX_PROFILES:
                    break
                card = cards.nth(i)
                try:
                    name = card.locator("span[aria-hidden='true']").first.inner_text(timeout=3000)
                    title = card.locator(".entity-result__primary-subtitle").first.inner_text(timeout=3000)
                    location = card.locator(".entity-result__secondary-subtitle").first.inner_text(timeout=3000)
                    url = card.locator("a.app-aware-link").first.get_attribute("href")
                    results.append({
                        "nom": name.strip(),
                        "titre": title.strip(),
                        "localisation": location.strip(),
                        "url": url.split("?")[0] if url else "",
                    })
                except Exception as e:
                    # Une carte n'a pas le format attendu, on l'ignore
                    print(f"  (profil ignoré, erreur d'extraction : {e})")
                    continue

            pause_humaine(1, 2.5)

            # Pagination : bouton "Suivant"
            next_button = page.locator("button[aria-label='Suivant']")
            if len(results) < MAX_PROFILES and next_button.count() > 0 and next_button.is_enabled():
                next_button.click()
                page_num += 1
                pause_humaine(3, 6)
            else:
                break

        # Sauvegarde
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["nom", "titre", "localisation", "url"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n{len(results)} profils extraits -> {OUTPUT_CSV.resolve()}")
        context.close()


if __name__ == "__main__":
    main()
