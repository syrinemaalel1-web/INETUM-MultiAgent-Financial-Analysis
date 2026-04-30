"""
agents_agno.py — Pipeline CMF Tunisie avec Agno Framework
RAG avec FAISS pour les grands documents (aucune perte de données)

ARCHITECTURE :
- Documents courts (<50k chars) : envoyés directement au LLM
- Documents longs (>50k chars)  : chunking + FAISS embeddings + retrieval ciblé
- Fallback intelligent : Gemini Pro → Flash sur quota/erreur
- Retry avec exponential backoff
"""

import argparse
import os
import json
import logging
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

# Charger les variables d'environnement
env_path = Path(__file__).parents[3] / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logging.warning("GOOGLE_API_KEY non trouvée. L'analyse IA risque d'échouer.")

# Imports Agno
from agno.agent import Agent
from agno.team import Team
from agno.models.google import Gemini
from agno.models.fallback import FallbackConfig

# Import des outils de calcul financier
from .financial_calculator import FinancialCalculator

# ════════════════════════════════════════════════════════
# 0. MODÈLES DE DONNÉES (Structured Output)
# ════════════════════════════════════════════════════════

class FinancialKPIs(BaseModel):
    """Modèle structuré pour les KPI financiers SCE tunisiens"""
    unit: str = Field(description="L'unité monétaire détectée (DT, MDT, etc.)")

    marge_exploitation: Optional[float] = Field(None, description="KPI_R1: Marge d'Exploitation (%)")
    marge_nette: Optional[float] = Field(None, description="KPI_R2: Marge Nette (%)")
    roe: Optional[float] = Field(None, description="KPI_R3: ROE (%)")
    roa: Optional[float] = Field(None, description="KPI_R4: ROA (%)")

    autonomie_financiere: Optional[float] = Field(None, description="KPI_S1: Autonomie Financière (%)")
    ratio_endettement: Optional[float] = Field(None, description="KPI_S2: Ratio d'Endettement")
    frng: Optional[float] = Field(None, description="KPI_S4: Fonds de Roulement Net Global (DT)")
    bfr: Optional[float] = Field(None, description="KPI_S5: BFR (DT)")
    tresorerie_nette: Optional[float] = Field(None, description="KPI_S6: Trésorerie Nette (DT)")

    liquidite_generale: Optional[float] = Field(None, description="KPI_L1: Liquidité Générale")
    liquidite_immediate: Optional[float] = Field(None, description="KPI_L2: Liquidité Immédiate")

    missing_data: List[str] = Field(default_factory=list, description="Rubriques manquantes")
    extraction_confidence: Optional[float] = Field(None, description="Niveau de confiance")
    processing_notes: List[str] = Field(default_factory=list, description="Notes de traitement")


class FinancialReport(BaseModel):
    """Modèle pour le rapport d'analyse financière"""
    title: str = Field(description="Titre du rapport")
    company_name: str = Field(description="Nom de l'entreprise analysée")
    analysis_date: str = Field(description="Date d'analyse")

    executive_summary: str = Field(description="Résumé exécutif")
    performance_analysis: str = Field(description="Analyse de performance")
    financial_structure: str = Field(description="Structure financière")
    liquidity_analysis: str = Field(description="Analyse de liquidité")
    recommendations: List[str] = Field(description="Recommandations stratégiques")

    reliability_score: str = Field(description="Score de fiabilité de l'analyse")
    limitations: List[str] = Field(default_factory=list, description="Limitations")


# ════════════════════════════════════════════════════════
# I. RAG FAISS — Chunking + Embeddings + Retrieval
# ════════════════════════════════════════════════════════

class FAISSDocumentRAG:
    """
    RAG local avec FAISS pour les grands documents financiers.
    Aucune perte de données : tout le document est indexé,
    seuls les chunks pertinents sont envoyés au LLM.

    Stratégie d'embedding (par ordre de priorité) :
    1. sentence-transformers/all-MiniLM-L6-v2 (local, aucun quota)
    2. gemini-embedding-001 (fallback si sentence-transformers indisponible)
    """

    CHUNK_SIZE = 3000      # BGE-M3 supporte 8192 tokens → chunks plus grands
    CHUNK_OVERLAP = 300
    TOP_K = 8

    # BGE-M3 : 100+ langues, 1024d, state-of-the-art multilingual (~570MB)
    LOCAL_MODEL = "BAAI/bge-m3"
    GEMINI_EMBED_MODEL = "models/gemini-embedding-exp-03-07"  # fallback Gemini

    def __init__(self):
        self.chunks: List[str] = []
        self.index = None
        self._st_model = None   # sentence-transformers model
        self._use_local = True  # sera mis à False si ST non dispo

    def _get_local_model(self):
        """Charge BGE-M3 (une seule fois, ~570MB, puis mis en cache)."""
        if self._st_model is None:
            from sentence_transformers import SentenceTransformer
            logging.info(f"🔄 Chargement BGE-M3 (premier lancement ~570MB, puis cache local)...")
            self._st_model = SentenceTransformer(self.LOCAL_MODEL)
            logging.info("✅ BGE-M3 chargé — 100+ langues, 1024d")
        return self._st_model

    def _embed_local(self, texts: List[str]) -> np.ndarray:
        """Embeddings locaux via BGE-M3 (no quota, French/Arabic natif)."""
        model = self._get_local_model()
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=16,        # traitement par batch pour économiser la RAM
        )
        return np.array(vectors, dtype=np.float32)

    def _embed_gemini(self, texts: List[str], task_type: str = "retrieval_document") -> np.ndarray:
        """Fallback : embeddings via gemini-embedding-001."""
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        vectors = []
        for text in texts:
            result = genai.embed_content(
                model=self.GEMINI_EMBED_MODEL,
                content=text,
                task_type=task_type,
            )
            vectors.append(result["embedding"])
        return np.array(vectors, dtype=np.float32)

    def _embed(self, texts: List[str], task_type: str = "retrieval_document") -> np.ndarray:
        """Embed avec local en priorité, Gemini en fallback."""
        if self._use_local:
            try:
                return self._embed_local(texts)
            except Exception as e:
                logging.warning(f"⚠️ sentence-transformers indisponible ({e}), fallback Gemini")
                self._use_local = False
        return self._embed_gemini(texts, task_type)

    def _split_chunks(self, text: str) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunks.append(text[start:end])
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP
        return chunks

    def build_index(self, document: str):
        """Indexe tout le document dans FAISS."""
        import faiss
        self.chunks = self._split_chunks(document)
        logging.info(f"📚 RAG FAISS : indexation de {len(self.chunks)} chunks")

        embeddings = self._embed(self.chunks, task_type="retrieval_document")
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dim)  # cosine sur vecteurs normalisés
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        logging.info(f"✅ Index FAISS construit ({dim}d, {len(self.chunks)} vecteurs)")

    def retrieve(self, query: str, top_k: int = None) -> str:
        """Récupère les chunks les plus pertinents pour une requête."""
        import faiss
        if self.index is None or not self.chunks:
            return ""

        k = top_k or self.TOP_K
        query_vec = self._embed([query], task_type="retrieval_query")
        faiss.normalize_L2(query_vec)

        scores, indices = self.index.search(query_vec, min(k, len(self.chunks)))

        retrieved = []
        for idx in indices[0]:
            if idx >= 0:
                retrieved.append(self.chunks[idx])

        return "\n\n---\n\n".join(retrieved)


# ════════════════════════════════════════════════════════
# II. CONFIGURATION FALLBACK
# ════════════════════════════════════════════════════════

def create_fallback_config() -> FallbackConfig:
    return FallbackConfig(
        on_rate_limit=[
            Gemini(id="gemini-2.5-flash", api_key=GOOGLE_API_KEY),
            Gemini(id="gemini-1.5-flash", api_key=GOOGLE_API_KEY),
        ],
        on_context_overflow=[
            Gemini(id="gemini-2.5-flash", api_key=GOOGLE_API_KEY),
        ],
        on_error=[
            Gemini(id="gemini-2.5-flash", api_key=GOOGLE_API_KEY),
        ],
    )


# ════════════════════════════════════════════════════════
# III. AGENTS
# ════════════════════════════════════════════════════════

def create_calculateur_agent() -> Agent:
    return Agent(
        name="Expert Comptable SCE Tunisie",
        role="Extracteur de Données Financières et Calculateur KPI",
        model=Gemini(id="gemini-2.5-pro", api_key=GOOGLE_API_KEY, temperature=0.0),
        fallback_config=create_fallback_config(),
        exponential_backoff=True,
        delay_between_retries=2,
        retries=5,
        output_schema=FinancialKPIs,
        tools=[FinancialCalculator()],
        debug_mode=True,
        markdown=True,
        instructions="""
Tu es un expert-comptable agréé en Tunisie (OECT), spécialisé dans les rapports CMF.

MISSION : Extraire les données financières et calculer les KPI SCE tunisiens.

EXTRACTION :
- Extrais UNIQUEMENT les valeurs numériques explicitement présentes
- Identifie l'unité monétaire (DT, MDT, KDTE)
- Pour toute donnée introuvable : marque 'DONNÉE MANQUANTE'
- Ne devine jamais, n'estime jamais

CALCULS KPI :
- Marge Exploitation (%) = (Résultat Exploitation / CA) × 100
- Marge Nette (%) = (Résultat Net / CA) × 100
- ROE (%) = (Résultat Net / Capitaux Propres) × 100
- ROA (%) = (Résultat Net / Total Actif) × 100
- Autonomie Financière (%) = (Capitaux Propres / Total Actif) × 100
- Ratio Endettement = Total Dettes / Capitaux Propres
- FRNG = (Capitaux Propres + Dettes LT) - Actif Non Courant
- BFR = Actifs Courants - Passifs Courants
- Trésorerie Nette = FRNG - BFR
- Liquidité Générale = (Actifs Courants + Trésorerie) / Dettes Courantes
- Liquidité Immédiate = Trésorerie / Dettes Courantes

RÈGLE : Précision avant tout. Un KPI non calculable vaut mieux qu'un KPI faux.
""",
    )


def create_rapporteur_agent() -> Agent:
    return Agent(
        name="Analyste Financier Senior BVMT",
        role="Rédacteur de Rapports d'Analyse Financière",
        model=Gemini(id="gemini-2.5-flash", api_key=GOOGLE_API_KEY, temperature=0.1),
        fallback_config=create_fallback_config(),
        exponential_backoff=True,
        delay_between_retries=1,
        retries=3,
        output_schema=FinancialReport,
        markdown=True,
        instructions="""
Tu es un analyste financier senior accrédité BVMT/CMF Tunisie.

MISSION : Transformer les KPI calculés en rapport d'analyse professionnel.

RÈGLES :
- Cite UNIQUEMENT les chiffres fournis par l'agent Calculateur
- Pour tout KPI 'DONNÉE MANQUANTE', indique clairement l'absence
- Contextualise selon les seuils SCE tunisiens :
  * Autonomie financière saine : > 30%
  * Liquidité générale correcte : > 1.0
  * Endettement acceptable : < 1.0

STRUCTURE :
1. Résumé Exécutif (3-4 phrases)
2. Performance Opérationnelle (marges, ROE, ROA)
3. Structure Financière (autonomie, endettement, FRNG/BFR/TN)
4. Liquidité et Risque Court Terme
5. Recommandations Stratégiques (2-4 actions concrètes)
""",
    )


# ════════════════════════════════════════════════════════
# IV. FONCTION D'ANALYSE PRINCIPALE
# ════════════════════════════════════════════════════════

LARGE_DOC_THRESHOLD = 50_000  # caractères

# Requêtes de retrieval pour chaque section financière
RAG_QUERIES = [
    "bilan actif passif total actif capitaux propres",
    "résultat net résultat exploitation chiffre affaires",
    "dettes long terme dettes courantes passif",
    "actifs courants trésorerie liquidités",
    "fonds roulement BFR trésorerie nette",
    "capitaux propres variation résultat exercice",
    "tableau flux trésorerie activités opérationnelles",
    "notes annexes engagements hors bilan",
]


def _build_context_for_large_doc(rapport_md: str) -> str:
    """
    Pour les grands documents : utilise FAISS pour récupérer
    tous les chunks financièrement pertinents sans rien perdre.
    """
    rag = FAISSDocumentRAG()
    rag.build_index(rapport_md)

    all_retrieved = set()
    for query in RAG_QUERIES:
        chunks = rag.retrieve(query, top_k=5)
        for chunk in chunks.split("\n\n---\n\n"):
            all_retrieved.add(chunk.strip())

    combined = "\n\n---\n\n".join(c for c in all_retrieved if c)
    logging.info(f"📊 RAG : {len(all_retrieved)} chunks pertinents récupérés sur {len(rag.chunks)} total")
    return combined


def analyser_rapport_agno(
    rapport_md: str,
    output_path: Path = None,
    md_file_path: Path = None,
    company_name: str = "Entreprise Tunisienne",
) -> Dict[str, Any]:
    """
    Analyse financière complète avec Agno + RAG FAISS pour grands documents.
    Aucune perte de données : FAISS indexe tout, récupère le pertinent.
    """
    try:
        # Choisir la stratégie selon la taille du document
        if len(rapport_md) > LARGE_DOC_THRESHOLD:
            logging.info(f"📄 Grand document ({len(rapport_md):,} chars) → RAG FAISS activé")
            context_content = _build_context_for_large_doc(rapport_md)
        else:
            logging.info(f"📄 Document standard ({len(rapport_md):,} chars) → contexte direct")
            context_content = rapport_md

        analysis_prompt = f"""
RAPPORT FINANCIER À ANALYSER :
Entreprise : {company_name}
Source : {md_file_path}

DONNÉES FINANCIÈRES :
{context_content}

MISSION :
1. Extraire toutes les données financières pertinentes
2. Calculer les 12 KPI SCE tunisiens
3. Générer un rapport d'analyse professionnel
"""

        # Créer les agents
        calculateur = create_calculateur_agent()
        rapporteur = create_rapporteur_agent()

        # Étape 1 : Extraction + calcul KPI
        logging.info("🔢 Étape 1 : Extraction et calcul des KPI...")
        kpi_result = calculateur.run(analysis_prompt)
        kpis_data = kpi_result.content if hasattr(kpi_result, "content") else kpi_result

        # Étape 2 : Génération du rapport
        logging.info("📝 Étape 2 : Génération du rapport...")
        rapport_prompt = f"""
Sur la base des KPI calculés ci-dessous, génère un rapport d'analyse financière professionnel.

KPI CALCULÉS :
{json.dumps(kpis_data.model_dump() if hasattr(kpis_data, 'model_dump') else str(kpis_data), indent=2, ensure_ascii=False)}

Entreprise : {company_name}
"""
        rapport_result = rapporteur.run(rapport_prompt)
        rapport_data = rapport_result.content if hasattr(rapport_result, "content") else rapport_result

        # Sauvegarder les résultats
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            kpis_dict = kpis_data.model_dump() if hasattr(kpis_data, "model_dump") else {}
            rapport_dict = rapport_data.model_dump() if hasattr(rapport_data, "model_dump") else {}

            rapport_final = f"""# {rapport_dict.get('title', 'Rapport Financier')}

## Résumé Exécutif
{rapport_dict.get('executive_summary', '')}

## Performance Opérationnelle
{rapport_dict.get('performance_analysis', '')}

## Structure Financière et Solvabilité
{rapport_dict.get('financial_structure', '')}

## Liquidité et Risque de Court Terme
{rapport_dict.get('liquidity_analysis', '')}

## Recommandations Stratégiques
{chr(10).join(f"- {rec}" for rec in rapport_dict.get('recommendations', []))}

## Fiabilité de l'Analyse
**Score de fiabilité** : {rapport_dict.get('reliability_score', 'N/A')}

---
*Rapport généré par l'architecture Agno + RAG FAISS - CMF Tunisie*
"""
            output_path.write_text(rapport_final, encoding="utf-8")

            kpi_path = output_path.with_suffix("").with_suffix("") / (output_path.stem.replace("_rapport", "_kpis") + ".json")
            kpi_path = output_path.parent / (output_path.stem.replace("_rapport", "_kpis") + ".json")
            kpi_path.write_text(json.dumps(kpis_dict, indent=2, ensure_ascii=False), encoding="utf-8")

            logging.info(f"✅ Rapport sauvegardé : {output_path}")

        return {
            "kpis": kpis_data.model_dump() if hasattr(kpis_data, "model_dump") else None,
            "rapport": rapport_data.model_dump() if hasattr(rapport_data, "model_dump") else None,
            "success": True,
            "message": "Analyse Agno terminée avec succès",
        }

    except Exception as e:
        logging.error(f"Erreur dans l'analyse Agno : {e}")
        return {
            "kpis": None,
            "rapport": None,
            "success": False,
            "message": f"Erreur Agno : {str(e)}",
        }


# ════════════════════════════════════════════════════════
# V. INTERFACE CLI
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agents CMF Tunisie — Analyse KPI avec Agno + RAG FAISS")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--company", type=str, default="Entreprise Tunisienne")
    args = parser.parse_args()

    rapport_md = args.input.read_text(encoding="utf-8")
    result = analyser_rapport_agno(rapport_md, args.output, md_file_path=args.input, company_name=args.company)

    if result["success"]:
        print("✅ Analyse Agno terminée avec succès")
    else:
        print(f"❌ Erreur : {result['message']}")
