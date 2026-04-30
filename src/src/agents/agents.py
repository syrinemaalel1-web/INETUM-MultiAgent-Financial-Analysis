"""
agents.py — Phase 3 (Intelligence) du pipeline CMF Tunisie
Analyse des KPIs et Création de Rapports avec CrewAI + Calculateur Financier Précis

ARCHITECTURE HYBRIDE OPTIMISÉE :
- Agent Calculateur : Gemini 3.1 Pro (Long Context) pour l'extraction de données complexes
- Agent Rapporteur : Gemini 2.5 Flash (Efficace) pour la génération rapide de rapports
- MCP Tools : Calculs financiers précis avec validation SCE tunisienne
"""

import argparse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement (clé API Gemini)
env_path = Path(__file__).parents[3] / "env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv() # Fallback sur .env standard

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logging.warning("GOOGLE_API_KEY non trouvée. L'analyse IA risque de échouer.")

from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field
from typing import Optional, List

# Import des outils de calcul financier
from .crewai_tools import FINANCIAL_TOOLS

# ════════════════════════════════════════════════════════
# 0. MODÈLES DE DONNÉES (Structured Output)
# ════════════════════════════════════════════════════════

class FinancialKPIs(BaseModel):
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
    missing_data: List[str] = Field(default_factory=list, description="Liste des rubriques manquantes")

# ════════════════════════════════════════════════════════
# I. INITIALISATION LLM (Architecture Hybride Optimisée)
# ════════════════════════════════════════════════════════

# Agent Calculateur - Gemini 3.1 Pro (Long Context pour documents complexes)
llm_calculateur = LLM(
    model="gemini/gemini-3.1-pro-preview",  # Meilleur pour l'analyse de longs documents
    temperature=0.0
)

# Agent Rapporteur - Gemini 2.5 Flash (Efficace pour génération de rapports)
llm_rapporteur = LLM(
    model="gemini/gemini-2.5-flash",  # Rapide et économique pour la rédaction
    temperature=0.0
)

# ════════════════════════════════════════════════════════
# II. AGENT 1 — LE CALCULATEUR DE KPI
# ════════════════════════════════════════════════════════

agent_calculateur = Agent(
    role="Expert Comptable SCE & Extracteur de Données Financières",
    goal="""
Extraire avec précision absolue les valeurs numériques des bilans et états 
de résultat tunisiens fournis en Markdown. Tu te concentres UNIQUEMENT sur 
l'extraction des données - les calculs seront effectués par des outils 
spécialisés pour garantir la précision.
Si une donnée est introuvable dans le document, tu écris explicitement 
'DONNÉE MANQUANTE' — tu ne devines jamais, tu n'estimes jamais.
""",
    backstory="""
Tu es un expert-comptable agréé en Tunisie, certifié par l'OECT, avec 20 ans 
d'expérience dans l'analyse des rapports CMF. Ta spécialité est l'extraction 
précise de données depuis les documents SCE tunisiens.

Tu as une règle d'or absolue : si un chiffre n'est pas explicitement présent 
dans le document source, tu retournes 'DONNÉE MANQUANTE'. Tu n'estimes pas, 
tu n'approximes pas, tu n'inventes pas.

Tu identifies l'unité de mesure (DT, MDT, KDTE) et tu la signales clairement.
Les calculs de KPI seront effectués par des outils spécialisés pour éviter 
toute erreur de calcul.

Avec Gemini 3.1 Pro, tu peux analyser des documents financiers très longs 
et complexes avec une précision exceptionnelle.
""",
    allow_delegation=False,
    verbose=True,
    max_iter=5,
    max_retry_limit=2,
    llm=llm_calculateur,  # Utilise Gemini 3.1 Pro pour les longs contextes
    tools=FINANCIAL_TOOLS,  # Ajout des outils de calcul
    respect_context_window=True
)

# ════════════════════════════════════════════════════════
# III. AGENT 2 — LE RAPPORTEUR BVMT
# ════════════════════════════════════════════════════════

agent_rapporteur = Agent(
    role="Analyste Financier Senior — Bourse de Tunis (BVMT)",
    goal="""
Transformer les KPI calculés en rapport d'analyse financière professionnel,
structuré et actionnable, destiné aux investisseurs et analystes de la
Bourse de Tunis (BVMT).
Tu travailles UNIQUEMENT avec les chiffres fournis par l'agent Calculateur.
Si un KPI est marqué 'DONNÉE MANQUANTE', tu NE rédiges PAS la section
correspondante — tu indiques clairement l'absence de données et tu
précises quelles rubriques du rapport source sont manquantes.
Toutes les valeurs citées sont en Dinar Tunisien (DT).
""",
    backstory="""
Tu es un analyste financier senior accrédité par la BVMT (Bourse des
Valeurs Mobilières de Tunis) et la CMF (Commission du Marché Financier
de Tunisie). Tes rapports sont utilisés par des fonds d'investissement,
des banques et des gestionnaires de portefeuilles tunisiens.

Ta réputation repose sur deux piliers :
(1) La précision : tu ne cites que des chiffres vérifiés, en DT.
(2) L'honnêteté analytique : si les données sont insuffisantes pour
    conclure, tu le dis clairement plutôt que de formuler une analyse
    creuse. Un 'DONNÉE MANQUANTE' dans ton rapport est une information,
    pas un échec.

Tu connais parfaitement les seuils de référence tunisiens :
- Autonomie financière saine : > 30%
- Liquidité générale correcte : > 1.0
- Endettement acceptable : Dettes/CP < 1.0
Tu contextualises chaque KPI par rapport à ces seuils sectoriels locaux.

Avec Gemini 2.5 Flash, tu génères des rapports rapidement et efficacement.
""",
    allow_delegation=False,
    verbose=True,
    max_iter=5,
    max_retry_limit=2,
    llm=llm_rapporteur,  # Utilise Gemini Flash pour la génération rapide
    respect_context_window=True
)

# ════════════════════════════════════════════════════════
# IV. TASK 1 — EXTRACTION ET CALCUL DES KPI
# ════════════════════════════════════════════════════════

task_calcul = Task(
    description="""
Tu reçois un rapport financier tunisien au format Markdown :

===RAPPORT SOURCE===
{rapport_md}
===FIN DU RAPPORT===

ÉTAPE 1 — IDENTIFICATION DE L'UNITÉ MONÉTAIRE
Identifie l'unité utilisée dans le rapport (DT, MDT, KDTE, etc.).
Utilise l'outil unit_converter si nécessaire pour clarifier les conversions.

ÉTAPE 2 — EXTRACTION PURE DES VALEURS
Extrais UNIQUEMENT les valeurs numériques suivantes depuis le rapport source.
Pour chaque rubrique introuvable, écris 'DONNÉE MANQUANTE'.
NE CALCULE RIEN - contente-toi d'extraire les valeurs brutes.

RUBRIQUES À EXTRAIRE :
[BILAN — ACTIF]
  - Total Actif Non Courant
  - Actifs Courants (hors trésorerie)
  - Trésorerie Actif (disponibilités + équivalents)
  - Total Actif

[BILAN — PASSIF]
  - Capitaux Propres
  - Dettes Non Courantes (emprunts LT, provisions LT)
  - Passifs Courants (hors trésorerie passif)
  - Trésorerie Passif (concours bancaires CT)
  - Total Passif

[ÉTAT DE RÉSULTAT]
  - Chiffre d'Affaires (Revenus d'exploitation)
  - Résultat d'Exploitation (EBIT)
  - Résultat Net de l'exercice

ÉTAPE 3 — CALCUL AUTOMATISÉ DES KPI
Une fois les valeurs extraites, utilise l'outil financial_calculator 
pour calculer automatiquement tous les KPI SCE tunisiens.

Format JSON pour l'outil :
{
    "chiffre_affaires": "valeur_extraite",
    "resultat_exploitation": "valeur_extraite",
    "resultat_net": "valeur_extraite",
    "capitaux_propres": "valeur_extraite",
    "total_actif": "valeur_extraite",
    "actif_non_courant": "valeur_extraite",
    "actifs_courants": "valeur_extraite",
    "dettes_non_courantes": "valeur_extraite",
    "passifs_courants": "valeur_extraite",
    "tresorerie_actif": "valeur_extraite",
    "tresorerie_passif": "valeur_extraite"
}

ÉTAPE 4 — VALIDATION
Utilise l'outil kpi_validator pour valider les KPI calculés selon 
les seuils SCE tunisiens.

RÈGLE FINALE ABSOLUE :
Si tu n'es pas certain d'une valeur, écris 'DONNÉE MANQUANTE'.
Laisse les outils spécialisés faire les calculs pour éviter les erreurs.
""",
    expected_output="""
Un objet JSON contenant l'unité détectée, toutes les valeurs extraites,
tous les KPI calculés par l'outil, et les validations correspondantes.
""",
    agent=agent_calculateur,
    output_json=FinancialKPIs
)

# ════════════════════════════════════════════════════════
# V. TASK 2 — RÉDACTION DU RAPPORT FINANCIER
# ════════════════════════════════════════════════════════

task_rapport = Task(
    description="""
En utilisant EXCLUSIVEMENT les KPI fournis par l'agent Calculateur
dans le contexte de cette tâche, rédige un rapport d'analyse financière
professionnel en français, structuré en 4 sections.

RÈGLE ABSOLUE ANTI-HALLUCINATION :
- Tu ne cites QUE des chiffres présents dans le tableau de l'agent Calculateur.
- Pour toute section dont les KPI sont marqués 'KPI NON CALCULABLE' ou
  'DONNÉE MANQUANTE', rédige uniquement : 
  "⚠️ Analyse impossible — Données manquantes : [liste les rubriques absentes]"
- Tu ne formules JAMAIS de conclusion sur des données que tu n'as pas.
- Toutes les valeurs sont exprimées en Dinar Tunisien (DT).

STRUCTURE DU RAPPORT :

---
# Rapport d'Analyse Financière
*Basé sur les normes SCE tunisiennes | Valeurs en Dinar Tunisien (DT)*
*Données sources : Rapports CMF Tunisie*

## 1. Performance Opérationnelle
Analyse de KPI_R1 (Marge d'Exploitation), KPI_R2 (Marge Nette),
KPI_R3 (ROE), KPI_R4 (ROA).
- Compare chaque marge à la moyenne sectorielle tunisienne si connue.
- Explique la relation entre marge d'exploitation et résultat net
  (impact de la charge financière, impôts, éléments exceptionnels).
- Signale tout écart anormal entre EBIT et résultat net.

## 2. Structure Financière et Solvabilité
Analyse de KPI_S1 (Autonomie Financière), KPI_S2 (Endettement),
KPI_S4 (FRNG), KPI_S5 (BFR), KPI_S6 (Trésorerie Nette).
- Évalue la solidité du bilan selon le prisme SCE :
  FRNG positif = structure saine à long terme.
- Interprète la relation FRNG/BFR/TN de façon pédagogique.
- Signale si l'autonomie financière est < 30% (signal d'alerte CMF).

## 3. Liquidité et Risque de Court Terme
Analyse de KPI_L1 (Liquidité Générale), KPI_L2 (Liquidité Immédiate).
- Évalue la capacité de l'entreprise à honorer ses dettes CT.
- Un ratio < 1.0 est un risque immédiat à signaler.
- Contextualise par rapport au BFR calculé.

## 4. Synthèse et Recommandations
- Points Forts (✅) : liste des KPI au-dessus des seuils SCE
- Points de Vigilance (⚠️) : liste des KPI dans la zone d'alerte
- Points Critiques (❌) : liste des KPI en situation dangereuse
- Recommandations stratégiques : 2 à 4 actions concrètes
- Note de fiabilité de l'analyse : "Complète" / "Partielle [X KPI manquants]"
---
""",
    expected_output="""
Un rapport financier complet au format Markdown, en français professionnel,
avec les 4 sections définies. Les sections sans données sont signalées
avec le message d'avertissement standardisé.
Toutes les valeurs absolues sont en Dinar Tunisien (DT).
""",
    agent=agent_rapporteur,
    context=[task_calcul]
)

# ════════════════════════════════════════════════════════
# VI. CREW ET FONCTION D'ENTRÉE
# ════════════════════════════════════════════════════════

def analyser_rapport(rapport_md: str, output_path: Path = None, md_file_path: Path = None) -> str:
    """
    Lance le pipeline CrewAI complet sur un rapport financier Markdown.
    Utilise l'injection directe (Long Context) pour Gemini, évitant ainsi les erreurs RAG/OpenAI.
    """
    # Nettoyage des descriptions pour Gemini (Long Context)
    # On injecte directement le texte du rapport dans le prompt
    local_task_calcul_desc = task_calcul.description.replace("{rapport_md}", rapport_md)
    local_task_rapport_desc = task_rapport.description

    # Désactiver les outils RAG qui causent des erreurs OpenAI
    agent_calculateur.tools = []
    agent_rapporteur.tools = []

    # Recréer les instances de Task pour cet appel spécifique
    current_task_calcul = Task(
        description=local_task_calcul_desc,
        expected_output=task_calcul.expected_output,
        agent=agent_calculateur,
        output_json=FinancialKPIs
    )
    
    current_task_rapport = Task(
        description=local_task_rapport_desc,
        expected_output=task_rapport.expected_output,
        agent=agent_rapporteur,
        context=[current_task_calcul]
    )

    # Configuration du Crew avec architecture hybride optimisée
    crew = Crew(
        agents=[agent_calculateur, agent_rapporteur],
        tasks=[current_task_calcul, current_task_rapport],
        process=Process.sequential,
        verbose=True,
        memory=False, 
        tracing=True, 
        max_rpm=10,  # Réduit légèrement pour Gemini 3.1 Pro
        cache=True
    )
    
    result = crew.kickoff()
    rapport_final = result.raw
    
    # Extraire les KPIs du résultat de la première tâche
    kpis_json = result.tasks_output[0].raw

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Sauvegarder le rapport Markdown
        output_path.write_text(rapport_final, encoding="utf-8")
        
        # Sauvegarder les KPIs au format JSON
        kpi_path = output_path.with_name(output_path.name.replace("_rapport.md", "_kpis.json"))
        kpi_path.write_text(kpis_json, encoding="utf-8")
        
        print(f"✅ Rapport sauvegardé : {output_path}")
        print(f"✅ KPIs sauvegardés : {kpi_path}")

    return rapport_final

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agents CMF Tunisie — Analyse KPI SCE")
    parser.add_argument("--input", type=Path, required=True,
                        help="Fichier Markdown extrait (sortie de extract.py)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Fichier Markdown de sortie du rapport")
    args = parser.parse_args()

    rapport_md = args.input.read_text(encoding="utf-8")
    analyser_rapport(rapport_md, args.output, md_file_path=args.input)
