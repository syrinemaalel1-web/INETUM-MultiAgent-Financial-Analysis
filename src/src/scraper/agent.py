"""
CMF PDF Scraper — CrewAI + Gemini 2.5 Flash
Architecture corrigée :
  - Agent CrewAI  : scrape les pages et sauvegarde les URLs dans urls.json
  - Script Python : lit urls.json et télécharge les PDFs (sans LLM)
"""

import os
import re
import json
import time
import random
import logging
import argparse
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

BASE_URL   = "https://www.cmf.tn"
PAGE_URL   = (
    "https://www.cmf.tn/?q=consultation-des-tats-financier"
    "-des-soci-t-s-faisant-ape&page={page}"
)
OUTPUT_DIR    = Path("data/raw")
URLS_FILE     = Path("data/urls.json")       # résultat du scraping
PROGRESS_FILE = Path("progress.json")
LOG_FILE      = "cmf_scraper.log"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.1,
)

# ─────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────

def clean_filename(text: str) -> str:
    """Nettoie un texte pour l'utiliser comme nom de fichier."""
    text = text.strip().upper()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text)
    return text[:80]


def load_progress() -> dict:
    """Charge la progression depuis progress.json."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Reprise : dernière page = {data.get('last_page_scraped', -1)}")
        return data
    return {"last_page_scraped": -1, "downloaded_files": []}


def save_progress(last_page: int, downloaded_files: list) -> None:
    """Sauvegarde la progression dans progress.json."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"last_page_scraped": last_page, "downloaded_files": downloaded_files},
            f, ensure_ascii=False, indent=2,
        )


def fetch_with_retry(url: str, max_retries: int = 3) -> Optional[requests.Response]:
    """GET avec retry automatique et rate limiting."""
    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(random.uniform(1.0, 2.0))
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                return resp
            logger.warning(f"HTTP {resp.status_code} pour {url} (tentative {attempt})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erreur réseau tentative {attempt}/{max_retries} : {e}")
    logger.error(f"Échec définitif : {url}")
    return None


def load_urls_file() -> list:
    """Charge la liste d'URLs depuis data/urls.json si elle existe."""
    if URLS_FILE.exists():
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_urls_file(entries: list) -> None:
    """Sauvegarde la liste d'URLs dans data/urls.json."""
    URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    logger.info(f"URLs sauvegardées dans {URLS_FILE} ({len(entries)} entrées)")

# ─────────────────────────────────────────────────────────────
# OUTIL CREWAI — SCRAPING UNIQUEMENT
# L'outil sauvegarde directement dans urls.json après chaque page.
# Le LLM ne manipule jamais la liste complète → pas de problème de tokens.
# ─────────────────────────────────────────────────────────────

@tool("Scraper une page CMF et sauvegarder les URLs")
def scrape_and_save_page(page_number: int) -> str:
    """
    Scrape une page du site CMF, extrait les liens PDF,
    et les ajoute immédiatement dans data/urls.json.

    Paramètre : page_number (int) — numéro de page (0 à 389).
    Retourne : résumé texte court (ex: 'Page 3 : 25 PDFs ajoutés. Total : 87')
    Le LLM reçoit uniquement ce résumé — jamais la liste complète des URLs.
    """
    url = PAGE_URL.format(page=page_number)
    logger.info(f"Scraping page {page_number} : {url}")

    response = fetch_with_retry(url)
    if not response:
        return f"Page {page_number} : ÉCHEC (pas de réponse HTTP)"

    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a", href=lambda h: h and h.endswith(".pdf"))
    new_entries = []

    for link in links:
        pdf_url = link.get("href", "")
        if not pdf_url.startswith("http"):
            pdf_url = BASE_URL + pdf_url

        filename = pdf_url.split("/")[-1].replace(".pdf", "")

        # Remonter 4 niveaux dans le DOM pour atteindre la ligne complète
        # Structure CMF niveau 4 : "date | NOM SOCIÉTÉ | année | type"
        societe_nom = filename  # fallback
        annee = "inconnue"

        parent = link.find_parent()
        for _ in range(6):
            if parent is None:
                break
            texte = parent.get_text(separator=" | ", strip=True)
            # La ligne complète contient la date (mar/fév/jan...) et l'année (20xx)
            if re.search(r"\b(jan|fév|mar|avr|mai|jun|jul|aoû|sep|oct|nov|déc)\b", texte, re.IGNORECASE) and re.search(r"\b20\d{2}\b", texte):
                # Découper par " | " et extraire le 2ème élément = nom société
                parties = [p.strip() for p in texte.split("|") if p.strip()]
                # parties[0] = date, parties[1] = nom société, parties[2] = année
                if len(parties) >= 3:
                    societe_nom = parties[1].strip()
                    year_match = re.search(r"\b(20\d{2})\b", parties[2])
                    annee = year_match.group(1) if year_match else "inconnue"
                break
            parent = parent.find_parent()

        type_match = re.search(r"\b(EFD|EFC|EFI)\b", pdf_url, re.IGNORECASE)
        type_etat = type_match.group(1).upper() if type_match else "EF"

        new_entries.append({
            "société": societe_nom,   # ✅ "Sté. TUNISIENNE DES INDUSTRIES DE PNEUMATIQUES - STIP -"
            "fichier": filename,      # ✅ "stip_efi300625"
            "année": annee,
            "type_état": type_etat,
            "pdf_url": pdf_url,
        })

    # Déduplication et sauvegarde immédiate
    existing = load_urls_file()
    existing_urls = {e["pdf_url"] for e in existing}
    added = [e for e in new_entries if e["pdf_url"] not in existing_urls]
    existing.extend(added)
    save_urls_file(existing)

    # Mise à jour progression
    progress = load_progress()
    save_progress(page_number, progress["downloaded_files"])

    # Retour COURT au LLM (pas la liste complète)
    msg = f"Page {page_number} : {len(added)} PDFs ajoutés. Total dans urls.json : {len(existing)}"
    logger.info(msg)
    return msg

# ─────────────────────────────────────────────────────────────
# AGENT CREWAI — SCRAPING SEULEMENT
# ─────────────────────────────────────────────────────────────

scraper_agent = Agent(
    role="Web Scraper CMF",
    goal=(
        "Appeler scrape_and_save_page() pour chaque page assignée. "
        "L'outil sauvegarde automatiquement les URLs — tu n'as pas à les stocker. "
        "Retourner uniquement un résumé final."
    ),
    backstory=(
        "Tu es un expert en scraping de sites gouvernementaux tunisiens. "
        "Tu appelles l'outil une page à la fois, dans l'ordre, sans en sauter."
    ),
    tools=[scrape_and_save_page],
    llm=llm,
    verbose=True,
    max_retry_limit=2,
)

# ─────────────────────────────────────────────────────────────
# PHASE 2 — TÉLÉCHARGEMENT PYTHON PUR (sans LLM)
# Raison : le LLM ne peut pas gérer des boucles de 500+ téléchargements
# sans timeout ou réponse vide. Un script Python classique est fiable ici.
# ─────────────────────────────────────────────────────────────

import asyncio
import httpx

async def fetch_pdf_async(client: httpx.AsyncClient, url: str, filepath: Path, semaphore: asyncio.Semaphore) -> bool:
    """Télécharge un PDF de manière asynchrone avec gestion des erreurs et sémaphore."""
    async with semaphore:
        for attempt in range(1, 4):
            try:
                # Random delay to be nice to the server
                await asyncio.sleep(random.uniform(0.5, 1.5))
                response = await client.get(url, timeout=30.0)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return True
                logger.warning(f"HTTP {response.status_code} pour {url} (tentative {attempt})")
            except Exception as e:
                logger.warning(f"Erreur tentative {attempt} pour {url} : {e}")
        return False

async def download_all_pdfs_async(societe_filter: Optional[str] = None) -> None:
    """Version asynchrone ultra-rapide du téléchargement des PDFs."""
    entries = load_urls_file()
    if not entries:
        logger.error("urls.json vide ou introuvable.")
        return

    if societe_filter:
        filtre = societe_filter.upper()
        entries = [e for e in entries if filtre in e["société"].upper()]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    progress = load_progress()
    already_done = set(progress["downloaded_files"])
    
    # Limiter à 5 téléchargements simultanés pour ne pas saturer le serveur CMF
    semaphore = asyncio.Semaphore(5)
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        tasks = []
        for entry in entries:
            societe = entry.get("société", "inconnu")
            annee = entry.get("année", "0000")
            type_ef = entry.get("type_état", "EF")
            pdf_url = entry.get("pdf_url", "")
            
            filename = f"{clean_filename(societe)}_{annee}_{type_ef}.pdf"
            filepath = OUTPUT_DIR / filename
            
            if filename in already_done or (filepath.exists() and filepath.stat().st_size > 0):
                continue
                
            tasks.append(fetch_pdf_async(client, pdf_url, filepath, semaphore))
        
        if not tasks:
            logger.info("Aucun nouveau PDF à télécharger.")
            return

        logger.info(f"Démarrage du téléchargement asynchrone de {len(tasks)} PDFs...")
        results = await asyncio.gather(*tasks)
        
        # Mise à jour de la progression
        success_count = sum(1 for r in results if r)
        logger.info(f"Téléchargement terminé : {success_count}/{len(tasks)} succès.")

def download_all_pdfs(societe_filter: Optional[str] = None) -> None:
    """Wrapper synchrone pour la version asynchrone."""
    asyncio.run(download_all_pdfs_async(societe_filter))

# ─────────────────────────────────────────────────────────────
# PHASE 1 — SCRAPING VIA CREWAI
# ─────────────────────────────────────────────────────────────

def run_scraping_phase(page_start: int, page_end: int) -> None:
    """Lance l'agent CrewAI pour scraper les pages et remplir urls.json."""
    logger.info(f"=== PHASE 1 : Scraping pages {page_start} à {page_end} ===")

    progress = load_progress()
    resume_from = max(progress["last_page_scraped"] + 1, page_start)

    if resume_from > page_end:
        logger.info("Toutes les pages déjà scrapées. Passage au téléchargement.")
        return

    pages_list = list(range(resume_from, page_end + 1))
    logger.info(f"Pages à traiter : {pages_list}")

    task_scraping = Task(
        description=(
            f"Appeler scrape_and_save_page() pour chaque numéro de page dans cette liste : {pages_list}. "
            "Traiter dans l'ordre croissant, une page à la fois. "
            "Chaque appel d'outil sauvegarde automatiquement les URLs dans urls.json — "
            "tu n'as pas à manipuler ni retourner les URLs. "
            "À la fin, retourner uniquement : 'X pages traitées. Total PDFs : Y'"
        ),
        expected_output="Résumé court : 'X pages traitées. Total PDFs : Y'",
        agent=scraper_agent,
    )

    crew = Crew(
        agents=[scraper_agent],
        tasks=[task_scraping],
        verbose=True,
    )

    result = crew.kickoff()
    logger.info(f"Phase 1 terminée : {result}")
    print(f"\n✅ Scraping terminé : {result}\n")


# ─────────────────────────────────────────────────────────────
# PIPELINE COMPLET
# ─────────────────────────────────────────────────────────────

def run(page_start: int, page_end: int, societe_filter: Optional[str] = None) -> None:
    """Lance Phase 1 (scraping CrewAI) puis Phase 2 (téléchargement Python)."""
    run_scraping_phase(page_start, page_end)
    logger.info("=== PHASE 2 : Téléchargement des PDFs ===")
    download_all_pdfs(societe_filter=societe_filter)

# ─────────────────────────────────────────────────────────────
# ENTRÉE CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CMF PDF Scraper — CrewAI + Gemini")
    parser.add_argument("--test", action="store_true",
                        help="Mode test : pages 0 à 2 seulement")
    parser.add_argument("--scrape-only", action="store_true",
                        help="Phase 1 seulement (scraping, sans téléchargement)")
    parser.add_argument("--download-only", action="store_true",
                        help="Phase 2 seulement (téléchargement depuis urls.json)")
    parser.add_argument("--societe", type=str, default=None,
                        help='Filtre société (ex: --societe "ATTIJARI BANK")')
    args = parser.parse_args()

    page_end = 2 if args.test else 19

    if args.scrape_only:
        run_scraping_phase(page_start=0, page_end=page_end)
    elif args.download_only:
        download_all_pdfs(societe_filter=args.societe)
    else:
        run(page_start=0, page_end=page_end, societe_filter=args.societe)