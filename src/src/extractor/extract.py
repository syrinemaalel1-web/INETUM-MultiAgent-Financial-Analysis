"""
extract.py — Phase 3 du pipeline CMF Tunisie
Extraction Docling des PDFs → fichiers Markdown structurés
Optimisation : Jinja2, Multiprocessing, Clean Code Architecture, Robust Regex.
Compatible Python 3.10+
"""

import re
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal
import multiprocessing
import concurrent.futures

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pydantic import BaseModel, ValidationError
from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

# Essayer d'importer depuis le config central si disponible
try:
    from config import TIMEOUT_SECONDS, DO_OCR, SAFE_MODE
except ImportError:
    TIMEOUT_SECONDS = 600
    DO_OCR = False
    SAFE_MODE = False

DEFAULT_INPUT_DIR   = Path("data/raw")
DEFAULT_OUTPUT_DIR  = Path("data/processed")
PROGRESS_FILE       = Path("extract_progress.json")
LOG_FILE            = "extract.log"

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
# MODÈLES PYDANTIC v2
# ─────────────────────────────────────────────────────────────

class DocumentFrontmatter(BaseModel):
    """Valide le frontmatter YAML avant écriture dans le Markdown (Template)."""
    société: str
    année: str
    type_état: str
    source_file: str
    date_extraction: str
    nb_pages: int
    nb_tableaux: int
    nb_sections: int
    statut: Literal["succès", "partiel", "échec"]

# ─────────────────────────────────────────────────────────────
# CLEAN CODE : GESTION SÉMANTIQUE CMF (Regex Robustes)
# ─────────────────────────────────────────────────────────────

class CMFSemantics:
    """Classe utilitaire pour l'analyse des textes et noms liés à la CMF."""

    @staticmethod
    def clean_text(titre: str) -> str:
        """Supprime les espaces et met en majuscules pour palier aux erreurs d'encodage OCR."""
        return re.sub(r"\s+", "", titre.upper())

    @classmethod
    def detect_section_type(cls, titre: str) -> str:
        """Classe un titre de section selon les états financiers tunisiens de manière robuste."""
        t = cls.clean_text(titre)
        if "BILAN" in t:
            return "BILAN_PASSIF" if "PASSIF" in t else "BILAN_ACTIF"
        if "RÉSULTAT" in t or "RESULTAT" in t:
            return "ETAT_RESULTAT"
        if "FLUX" in t or "TRÉSORERIE" in t or "TRESORERIE" in t:
            return "FLUX_TRESORERIE"
        if "CAPITAUXPROPRES" in t or "VARIATION" in t:
            return "VARIATION_CAPITAUX"
        if "NOTE" in t or "ANNEXE" in t:
            return "NOTES_ANNEXES"
        return "AUTRE"

    @staticmethod
    def parse_filename_metadata(pdf_path: Path) -> dict:
        """Extrait société, année et type_état depuis le nom du fichier. Conventions Phase 2."""
        parts = pdf_path.stem.split("_")
        type_état = parts[-1] if parts[-1] in ("EFI", "EFD", "EFC", "EF") else "EF"
        année     = parts[-2] if len(parts) >= 2 and re.match(r"20\d{2}", parts[-2]) else "inconnue"
        société   = "_".join(parts[:-2]) if len(parts) >= 3 else pdf_path.stem
        return {
            "société"    : société.replace("_", " "),
            "année"      : année,
            "type_état"  : type_état,
            "source_file": pdf_path.name,
        }

# ─────────────────────────────────────────────────────────────
# CLEAN CODE : RENDU MARKDOWN (Jinja2)
# ─────────────────────────────────────────────────────────────

class MarkdownRenderer:
    """Gère le rendu final en injectant les données dans un template Jinja2."""
    
    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(searchpath=str(template_dir)))
        self.template = self.env.get_template("report.md.j2")
        
    def render(self, metadata: dict, sections: list, tables: list, full_text: str) -> str:
        """Organise les données et rend le Markdown injecté."""
        # Grouper les tables par section
        used_tables = set()
        organized_sections = []
        
        for sec in sections:
            sec_copy = sec.copy()
            sec_copy["tables"] = []
            for i, tbl in enumerate(tables):
                if i in used_tables:
                    continue
                if tbl["type_tableau"] == sec["type_section"] or sec["type_section"] == "AUTRE":
                    sec_copy["tables"].append(tbl)
                    used_tables.add(i)
            organized_sections.append(sec_copy)
            
        unassigned_tables = [tbl for i, tbl in enumerate(tables) if i not in used_tables]
        
        return self.template.render(
            metadata=metadata,
            organized_sections=organized_sections,
            unassigned_tables=unassigned_tables,
            full_text=full_text
        )

# ─────────────────────────────────────────────────────────────
# CLEAN CODE : LE MOTEUR D'EXTRACTION DOCLING
# ─────────────────────────────────────────────────────────────

class ExtractionEngine:
    """Isole et configure le moteur Docling pour la récupération du contenu brut."""
    
    def __init__(self, do_ocr: bool = False, safe_mode: bool = False, max_pages_per_chunk: int = 15):
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = do_ocr              
        self.pipeline_options.do_table_structure = not safe_mode # Désactivé en mode safe pour économiser la RAM
        
        # Optimisation mémoire agressive pour éviter std::bad_alloc
        self.pipeline_options.generate_page_images = False
        self.pipeline_options.generate_table_images = False
        self.pipeline_options.images_scale = 1.0 
        
        # Réduire le nombre de threads internes pour le layout et l'OCR (très important pour la RAM)
        try:
            self.pipeline_options.num_threads = 1
        except Exception:
            pass
        
        # Configuration du chunking
        self.max_pages_per_chunk = max_pages_per_chunk
        self.use_chunking = True  # Activé par défaut pour les gros documents
        
        self.converter = DocumentConverter(
            format_options={".pdf": PdfFormatOption(pipeline_options=self.pipeline_options)}
        )

    def extract(self, pdf_path: Path):
        """Exécute l'extraction avec gestion robuste de la mémoire et fallbacks successifs."""
        
        # Estimer le nombre de pages
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
        except Exception:
            # Si on ne peut pas lire le nombre de pages, on essaie quand même
            total_pages = None
        
        # Décider si on utilise le chunking
        should_chunk = (
            self.use_chunking and 
            total_pages is not None and 
            total_pages > self.max_pages_per_chunk
        )
        
        if should_chunk:
            logger.info(f"📄 Document {pdf_path.name} : {total_pages} pages")
            logger.info(f"🔄 Traitement par chunks de {self.max_pages_per_chunk} pages pour économiser la mémoire")
            return self._extract_by_chunks(pdf_path, total_pages)
        else:
            # Traitement normal pour les petits documents
            return self._extract_with_fallback(pdf_path)
    
    def _extract_by_chunks(self, pdf_path: Path, total_pages: int):
        """Extrait le PDF par chunks pour économiser la mémoire"""
        import PyPDF2
        from PyPDF2 import PdfWriter
        import tempfile
        
        all_sections = []
        all_tables = []
        all_text = []
        
        num_chunks = (total_pages + self.max_pages_per_chunk - 1) // self.max_pages_per_chunk
        
        logger.info(f"📦 Division en {num_chunks} chunks")
        
        for chunk_idx in range(num_chunks):
            start_page = chunk_idx * self.max_pages_per_chunk
            end_page = min((chunk_idx + 1) * self.max_pages_per_chunk, total_pages)
            
            logger.info(f"   Chunk {chunk_idx + 1}/{num_chunks} : pages {start_page + 1}-{end_page}")
            
            try:
                # Créer un PDF temporaire avec seulement ce chunk
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_path = Path(tmp_file.name)
                    
                    # Extraire les pages du chunk
                    pdf_writer = PdfWriter()
                    with open(pdf_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page_num in range(start_page, end_page):
                            pdf_writer.add_page(pdf_reader.pages[page_num])
                    
                    # Écrire le chunk temporaire
                    with open(tmp_path, 'wb') as out_f:
                        pdf_writer.write(out_f)
                
                # Extraire ce chunk
                chunk_data = self._extract_with_fallback(tmp_path)
                
                # Fusionner les résultats
                all_sections.extend(chunk_data["sections"])
                all_tables.extend(chunk_data["tables"])
                all_text.append(chunk_data["full_text"])
                
                # Nettoyer le fichier temporaire
                tmp_path.unlink()
                
                logger.info(f"   ✅ Chunk {chunk_idx + 1} traité : {len(chunk_data['sections'])} sections, {len(chunk_data['tables'])} tableaux")
                
            except Exception as e:
                logger.error(f"   ❌ Erreur sur chunk {chunk_idx + 1} : {e}")
                # Continuer avec les autres chunks même si un échoue
                continue
        
        logger.info(f"✅ Extraction par chunks terminée : {len(all_sections)} sections, {len(all_tables)} tableaux au total")
        
        return {
            "sections": all_sections,
            "tables": all_tables,
            "full_text": "\n\n".join(all_text),
            "nb_pages": total_pages
        }
    
    def _extract_with_fallback(self, pdf_path: Path):
        """Exécute l'extraction avec fallbacks successifs en cas d'erreur mémoire"""
        while True:
            try:
                return self._perform_extraction(pdf_path)
            except Exception as e:
                error_str = str(e).lower()
                is_mem_error = any(msg in error_str for msg in ["bad_alloc", "bad allocation", "out of memory"])
                
                if is_mem_error:
                    if self.pipeline_options.do_ocr:
                        logger.warning(f"RAM insuffisante pour l'OCR sur {pdf_path.name}. Fallback sans OCR.")
                        self.pipeline_options.do_ocr = False
                        # Recréer le convertisseur avec les options réduites
                        self.converter = DocumentConverter(
                            format_options={".pdf": PdfFormatOption(pipeline_options=self.pipeline_options)}
                        )
                        continue  # Réessayer avec OCR désactivé
                    elif self.pipeline_options.do_table_structure:
                        logger.warning(f"RAM insuffisante pour les tableaux sur {pdf_path.name}. Fallback sans tableaux.")
                        self.pipeline_options.do_table_structure = False
                        # Recréer le convertisseur avec les options réduites
                        self.converter = DocumentConverter(
                            format_options={".pdf": PdfFormatOption(pipeline_options=self.pipeline_options)}
                        )
                        continue  # Réessayer sans tableaux
                    else:
                        logger.error(f"Erreur mémoire critique sur {pdf_path.name} même en mode minimal.")
                        raise e
                else:
                    # Autre type d'erreur, on la propage
                    raise e

    def _perform_extraction(self, pdf_path: Path) -> dict:
        """Logique interne de conversion Docling."""
        result = self.converter.convert(str(pdf_path))
        doc = result.document
        full_text = doc.export_to_markdown()
        
        # Logique d'OCR conditionnel : si le texte extrait est trop court 
        # (souvent signe d'un PDF scanné sans couche texte)
        if not self.pipeline_options.do_ocr and len(full_text) < 500:
            logger.info(f"Texte trop court ({len(full_text)} chars). Tentative avec OCR...")
            try:
                # Créer un convertisseur temporaire avec OCR
                temp_options = PdfPipelineOptions()
                temp_options.do_ocr = True
                temp_options.do_table_structure = self.pipeline_options.do_table_structure
                temp_options.generate_page_images = False
                temp_options.generate_table_images = False
                temp_options.images_scale = 1.0
                
                temp_converter = DocumentConverter(
                    format_options={".pdf": PdfFormatOption(pipeline_options=temp_options)}
                )
                result = temp_converter.convert(str(pdf_path))
                doc = result.document
                full_text = doc.export_to_markdown()
            except Exception as ocr_err:
                logger.warning(f"Échec de l'OCR de secours (mémoire ?) : {ocr_err}. On garde le texte court.")

        return {
            "sections": self._extract_sections(doc),
            "tables": self._extract_tables(doc),
            "full_text": full_text,
            "nb_pages": len(doc.pages) if hasattr(doc, "pages") else 0
        }

    def _extract_sections(self, doc) -> list:
        sections = []
        for element, _level in doc.iterate_items():
            label = getattr(element, "label", "")
            if str(label) not in ("section_header", "text", "title"):
                continue
            titre   = element.text.strip() if hasattr(element, "text") else ""
            niveau  = getattr(element, "level", 2) or 2
            page    = self._get_page(element)
            sections.append({
                "titre"       : titre,
                "niveau"      : int(niveau),
                "contenu"     : titre,
                "page"        : page,
                "type_section": CMFSemantics.detect_section_type(titre)
            })
        return sections

    def _extract_tables(self, doc) -> list:
        tables = []
        for i, table in enumerate(doc.tables):
            page        = self._get_page(table)
            titre       = getattr(table, "caption", f"Tableau {i + 1}") or f"Tableau {i + 1}"
            if hasattr(titre, "text"): titre = titre.text
            type_tableau = CMFSemantics.detect_section_type(str(titre))
            
            tables.append({
                "titre"       : str(titre).strip(),
                "page"        : page,
                "type_tableau": type_tableau,
                "markdown_table": self._table_to_markdown(table),
            })
        return tables

    def _table_to_markdown(self, table) -> str:
        try:
            grid = table.data.grid if hasattr(table, "data") else []
            if not grid: return ""
            rows = []
            for row in grid:
                cells = [c.text.strip() if c and hasattr(c, "text") else "" for c in row]
                rows.append("| " + " | ".join(cells) + " |")
            if len(rows) >= 1:
                sep = "| " + " | ".join(["---"] * len(grid[0])) + " |"
                rows.insert(1, sep)
            return "\n".join(rows)
        except Exception as exc:
            logger.warning(f"Table non convertible : {exc}")
            return ""

    def _get_page(self, element) -> int:
        try:
            prov = element.prov[0] if hasattr(element, "prov") and element.prov else None
            return int(prov.page_no) if prov and hasattr(prov, "page_no") else 0
        except Exception:
            return 0


# ─────────────────────────────────────────────────────────────
# WORKER FUNCTION (Point d'accès pour un seul PDF / Multiprocessing)
# ─────────────────────────────────────────────────────────────

def process_single_pdf(pdf_path: Path, output_dir: Path, templates_dir: Path, do_ocr: bool = False, safe_mode: bool = False) -> dict:
    """Fonction isolée appelée par le ProcessPoolExecutor (ou directement en Single)"""
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        return {"status": "error", "path": str(pdf_path), "message": "Introuvable/Vide", "file": pdf_path.name}

    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / (pdf_path.stem + ".md")
    
    try:
        # Import de l'optimiseur mémoire
        try:
            from .memory_optimizer import memory_optimizer
        except ImportError:
            memory_optimizer = None
        
        engine = ExtractionEngine(do_ocr=do_ocr, safe_mode=safe_mode)
        renderer = MarkdownRenderer(templates_dir)
        
        extracted_data = engine.extract(pdf_path)
        metadata = CMFSemantics.parse_filename_metadata(pdf_path)
        
        tables = extracted_data["tables"]
        sections = extracted_data["sections"]
        
        metadata.update({
            "nb_pages"    : extracted_data["nb_pages"],
            "nb_tableaux" : len(tables),
            "nb_sections" : len(sections),
            "statut"      : "succès" if sections or tables else "partiel",
            "date_extraction": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })

        try:
            DocumentFrontmatter(**metadata)
        except ValidationError as exc:
            logger.warning(f"Valid. Pydantic échouée pour {pdf_path.name}: {exc}")

        markdown = renderer.render(
            metadata=metadata, 
            sections=sections, 
            tables=tables, 
            full_text=extracted_data["full_text"]
        )

        md_path.write_text(markdown, encoding="utf-8")
        return {"status": "success", "path": str(md_path), "message": "OK", "file": pdf_path.name}
        
    except Exception as exc:
        error_str = str(exc).lower()
        
        # Détection d'erreur mémoire
        if "bad_alloc" in error_str or "not enough memory" in error_str or "runtimeerror" in error_str:
            logger.error(f"❌ ERREUR MÉMOIRE détectée pour {pdf_path.name}")
            logger.error(f"   Taille: {pdf_path.stat().st_size / (1024 * 1024):.2f} MB")
            logger.error(f"   Pages estimées: {pdf_path.stat().st_size // 50000}")
            
            # Créer un fichier Markdown de fallback
            if memory_optimizer:
                error_info = memory_optimizer.handle_memory_error(pdf_path, exc)
                fallback_md = memory_optimizer.create_fallback_markdown(pdf_path, error_info)
                md_path.write_text(fallback_md, encoding="utf-8")
                
                return {
                    "status": "memory_error",
                    "path": str(md_path),
                    "message": f"Erreur mémoire - Fallback créé. Recommandation: Utiliser Agno Framework",
                    "file": pdf_path.name,
                    "error_type": "memory",
                    "recommendation": "use_agno"
                }
            else:
                return {
                    "status": "error",
                    "path": str(pdf_path),
                    "message": f"Erreur mémoire: {str(exc)[:100]}",
                    "file": pdf_path.name,
                    "error_type": "memory"
                }
        
        # Autres erreurs
        return {"status": "error", "path": str(pdf_path), "message": str(exc)[:100], "file": pdf_path.name}

# ─────────────────────────────────────────────────────────────
# CONTROLLEUR PRINCIPAL (Multiprocessing & CLI)
# ─────────────────────────────────────────────────────────────

class PDFBatchProcessor:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        
    def execute_single(self, pdf_path: Path, output_dir: Path, do_ocr: bool = False, safe_mode: bool = False):
        logger.info(f"Mode Single : Traitement de {pdf_path.name} avec Timeout de {TIMEOUT_SECONDS}s")
        # Même en single, on utilise l'executor pour bénéficier du timeout propre.
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(process_single_pdf, pdf_path, output_dir, self.templates_dir, do_ocr, safe_mode)
            try:
                result = future.result(timeout=TIMEOUT_SECONDS)
                if result["status"] == "success":
                    print(f"\n✅ {pdf_path.name} extrait avec succès dans {result['path']}")
                else:
                    print(f"\n❌ Erreur sur {pdf_path.name} : {result['message']}")
            except concurrent.futures.TimeoutError:
                logger.error(f"TIMEOUT: Abandon de {pdf_path.name} (>{TIMEOUT_SECONDS}s)")
                print(f"\n❌ Timeout (>{TIMEOUT_SECONDS}s) sur {pdf_path.name}")

    def execute_batch(self, input_dir: Path, output_dir: Path, force_retry: bool):
        pdfs = sorted(input_dir.glob("*.pdf"))
        if not pdfs:
            logger.warning(f"Aucun PDF trouvé dans {input_dir}")
            return

        progress = self._load_progress()
        done_set = set(progress["processed_files"])
        to_process = [p for p in pdfs if force_retry or (p.name not in done_set and not (output_dir / (p.stem + ".md")).exists())]

        logger.info(f"Mode Batch : {len(to_process)} fichiers à extraire via Multiprocessing (Timeouts actifs)")
        
        ok_count = skip_count = err_count = 0
        skip_count = len(pdfs) - len(to_process)
        
        # Forcer à 1 seul worker pour éviter std::bad_alloc sur les machines à RAM limitée
        max_workers = 1
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Map des futures vers les fichiers
            future_to_pdf = {executor.submit(process_single_pdf, p, output_dir, self.templates_dir, DO_OCR, SAFE_MODE): p for p in to_process}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_pdf, timeout=None), total=len(to_process), desc="Extraction Parallèle"):
                pdf_path = future_to_pdf[future]
                try:
                    res = future.result(timeout=TIMEOUT_SECONDS) # Le as_completed n'applique qu'un timeout global, pas per-task, mais process_single_pdf l'a au global... Wait, as_completed gère le rendu direct. Si un process bloque, d'autres tournent.
                    if res["status"] == "success":
                        ok_count += 1
                        progress["processed_files"].append(res["file"])
                    else:
                        err_count += 1
                        progress["failed_files"].append({"file": res["file"], "reason": res["message"]})
                except concurrent.futures.TimeoutError:
                    err_count += 1
                    logger.error(f"TIMEOUT: {pdf_path.name}")
                    progress["failed_files"].append({"file": pdf_path.name, "reason": f"Timeout {TIMEOUT_SECONDS}s"})
                except Exception as exc:
                    err_count += 1
                    logger.error(f"Erreur Fatale Process {pdf_path.name} : {exc}")

                progress["last_processed"] = datetime.now(timezone.utc).isoformat()
                self._save_progress(progress)

        print("\n" + "=" * 50)
        print(f"  Total PDFs      : {len(pdfs)}")
        print(f"  ✅ Extraits      : {ok_count}")
        print(f"  ⏭️ Skippés       : {skip_count}")
        print(f"  ❌ Erreurs       : {err_count}")
        print("=" * 50)

    def _load_progress(self) -> dict:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"processed_files": [], "failed_files": [], "last_processed": ""}

    def _save_progress(self, progress: dict):
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────────────────────
# ENTRÉE CLI
# ─────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CMF PDF Extractor — Multiprocessing + Jinja2")
    parser.add_argument("--pdf", type=Path, default=None, help="Chemin vers un PDF unique à extraire (Priorité absolue)")
    parser.add_argument("--batch", action="store_true", help=f"Extraire tous les PDFs de {DEFAULT_INPUT_DIR}")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Dossier de sortie")
    parser.add_argument("--force-retry", action="store_true", help="Retraiter même les fichiers déjà extraits")
    return parser.parse_args()

def main():
    args = parse_args()
    # Configuration des chemins locaux (résilients)
    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / "templates"
    
    processor = PDFBatchProcessor(templates_dir)

    if args.pdf:
        processor.execute_single(args.pdf, args.output)
    elif args.batch:
        processor.execute_batch(DEFAULT_INPUT_DIR, args.output, args.force_retry)
    else:
        print("Usage :")
        print("  1. Tester un seul fichier : python src/extractor/extract.py --pdf data/raw/mon_fic.pdf")
        print("  2. Traitement en masse    : python src/extractor/extract.py --batch")

if __name__ == "__main__":
    # Nécessaire sous Windows pour ProcessPoolExecutor
    multiprocessing.freeze_support()
    main()