# 🤖 INETUM — Pipeline Multi-Agent d'Analyse Financière Automatisée

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![CrewAI](https://img.shields.io/badge/CrewAI-0.80%2B-orange)
![Agno](https://img.shields.io/badge/Agno-Framework-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-red?logo=google)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Automatisation complète de l'analyse des rapports financiers tunisiens (CMF) via un pipeline multi-agent intelligent.**

</div>

---

## 📋 Table des matières

- [Présentation du projet](#-présentation-du-projet)
- [Contexte](#-contexte)
- [Objectif et problème traité](#-objectif-et-problème-traité)
- [Architecture du système](#-architecture-du-système)
- [Rôle de chaque agent](#-rôle-de-chaque-agent)
- [Technologies utilisées](#-technologies-utilisées)
- [Structure des dossiers](#-structure-des-dossiers)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration des API Keys](#-configuration-des-api-keys)
- [Lancement du projet](#-lancement-du-projet)
- [Utilisation du pipeline](#-utilisation-du-pipeline)
- [Troubleshooting](#-troubleshooting)
- [Sécurité](#-sécurité)
- [Contribuer](#-contribuer)

---

## 🎯 Présentation du projet

Ce projet est un **pipeline multi-agent intelligent** qui automatise entièrement l'analyse financière des rapports publiés par la **Commission du Marché Financier (CMF) de Tunisie**.

Le système combine plusieurs agents IA spécialisés pour :
1. **Scraper** automatiquement les rapports financiers PDF depuis le site CMF
2. **Extraire** le contenu textuel des PDF avec Docling (OCR inclus)
3. **Calculer** les KPI financiers selon les normes SCE tunisiennes
4. **Générer** des rapports d'analyse professionnels en français

Le tout est piloté via une **interface web React** connectée à une **API FastAPI**.

---

## 🏢 Contexte

Ce projet a été réalisé dans le cadre d'un **stage de fin d'études** chez **INETUM Tunisie** (anciennement GFI Informatique), entreprise de services numériques (ESN) présente en Tunisie et en Europe.

L'objectif du stage était de concevoir et implémenter un système d'intelligence artificielle appliqué à la finance de marché tunisienne, en exploitant les dernières avancées des frameworks d'agents autonomes (CrewAI, Agno).

---

## 🎯 Objectif et problème traité

### Le problème
L'analyse manuelle des rapports financiers des sociétés cotées à la **Bourse des Valeurs Mobilières de Tunis (BVMT)** est :
- ⏱️ **Chronophage** : des dizaines de PDF à lire et analyser chaque trimestre
- 🔢 **Fastidieuse** : calculs répétitifs de ratios (ROE, ROA, BFR, FRNG...)
- 📊 **Non standardisée** : chaque analyste interprète les données différemment
- ❌ **Sujette aux erreurs** humaines de calcul

### La solution
Un **pipeline automatisé** qui :
- Télécharge les rapports PDF directement depuis CMF.tn
- Extrait et structure les données financières
- Calcule automatiquement les KPI SCE tunisiens (Système Comptable des Entreprises)
- Génère un rapport d'analyse professionnel standardisé en Markdown
- Présente les résultats dans un tableau de bord interactif

---

## 🏗️ Architecture du système

```
┌────────────────────────────────────────────────────────────┐
│                    INTERFACE UTILISATEUR                    │
│                   React + Vite (Frontend)                   │
│          Dashboard KPI │ Visionneuse Rapports               │
└────────────────────────────┬───────────────────────────────┘
                             │ HTTP / WebSocket
                             ▼
┌────────────────────────────────────────────────────────────┐
│                     API GATEWAY                             │
│                  FastAPI (Backend)                           │
│     /scrape │ /process │ /report │ /kpis │ /upload         │
└──────┬───────────────┬───────────────────┬─────────────────┘
       │               │                   │
       ▼               ▼                   ▼
┌──────────┐   ┌──────────────┐   ┌─────────────────────┐
│  PHASE 1 │   │   PHASE 2    │   │       PHASE 3        │
│ SCRAPER  │   │  EXTRACTEUR  │   │    ANALYSE IA        │
│          │   │              │   │                      │
│ CrewAI   │   │   Docling    │   │  DISPATCHER          │
│ Agent +  │   │   PDF→MD     │   │  ┌───────────────┐  │
│ Gemini   │   │   + OCR      │   │  │ CrewAI Engine │  │
│ 2.5 Flash│   │              │   │  │ (docs < 20p.) │  │
│          │   │              │   │  ├───────────────┤  │
│ → PDFs   │   │ → Markdown   │   │  │  Agno Engine  │  │
│ → URLs   │   │   structuré  │   │  │ (docs > 20p.) │  │
└──────────┘   └──────────────┘   │  └───────────────┘  │
                                  │  → Rapport MD        │
                                  │  → KPIs JSON         │
                                  └─────────────────────┘
                                          │
                                          ▼
                                  ┌───────────────┐
                                  │  BASE DE      │
                                  │  DONNÉES      │
                                  │  SQLite       │
                                  └───────────────┘
```

### Flux de données complet

```
CMF.tn Website
     │
     │ (Scraping + Download)
     ▼
PDF Reports ──► Docling Extractor ──► Markdown
                                         │
                          ┌──────────────┘
                          ▼
              Dispatcher (sélection intelligente)
                 ├── Court (<20 pages) → CrewAI
                 └── Long (>20 pages) → Agno (FAISS RAG)
                          │
                          ▼
              Agent Calculateur (Gemini Pro)
              [Extrait les données brutes du bilan]
                          │
                          ▼
              Agent Rapporteur (Gemini Flash)
              [Génère le rapport en Markdown]
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Rapport MD              KPIs JSON
        (analyse narrative)    (données structurées)
```

---

## 🤖 Rôle de chaque agent

### Agent 1 — Scraper CMF (`src/src/scraper/agent.py`)
| Propriété | Valeur |
|-----------|--------|
| **Rôle** | Naviguer sur CMF.tn, collecter les liens PDF, télécharger les rapports |
| **Framework** | CrewAI |
| **LLM** | Gemini 2.5 Flash |
| **Sortie** | Fichiers PDF dans `backend/data/raw/` + `urls.json` |

Cet agent :
- Parcourt les pages de consultation des états financiers CMF
- Identifie les liens vers les PDF des rapports annuels
- Télécharge les PDF avec gestion de la progression (resume-capable)
- Filtre optionnellement par nom de société

### Agent 2 — Extracteur Docling (`src/src/extractor/extract.py`)
| Propriété | Valeur |
|-----------|--------|
| **Rôle** | Convertir les PDF en Markdown structuré |
| **Framework** | Docling (IBM) |
| **LLM** | Aucun (traitement local) |
| **Sortie** | Fichiers `.md` dans `backend/data/processed/` |

Cet agent :
- Utilise Docling pour extraire texte, tableaux et figures des PDF
- Supporte l'OCR pour les documents scannés (activé via `DO_OCR=true`)
- Préserve la structure des tableaux financiers (bilans, états de résultat)
- Mode safe pour contourner les erreurs mémoire sur gros documents

### Agent 3 — Calculateur KPI (CrewAI/Agno)
| Propriété | Valeur |
|-----------|--------|
| **Rôle** | Extraire les valeurs brutes du bilan et calculer les KPI SCE |
| **Framework** | CrewAI (court) ou Agno+FAISS (long) |
| **LLM** | Gemini Pro (extraction longue) |
| **Sortie** | JSON avec tous les KPI calculés |

KPI calculés selon les normes SCE tunisiennes :
- **Rentabilité** : Marge d'Exploitation, Marge Nette, ROE, ROA
- **Structure** : Autonomie Financière, Ratio d'Endettement, FRNG, BFR
- **Liquidité** : Liquidité Générale, Liquidité Immédiate, Trésorerie Nette

### Agent 4 — Rapporteur BVMT (CrewAI/Agno)
| Propriété | Valeur |
|-----------|--------|
| **Rôle** | Rédiger le rapport d'analyse financière professionnel |
| **Framework** | CrewAI ou Agno |
| **LLM** | Gemini 2.5 Flash (rédaction rapide) |
| **Sortie** | Rapport Markdown dans `backend/data/rapports/` |

### Dispatcher Intelligent (`src/src/agents/dispatcher.py`)
Le dispatcher choisit automatiquement le moteur d'analyse :
- **CrewAI** → pour documents < 20 pages (rapide, simple)
- **Agno + FAISS RAG** → pour documents > 20 pages (robuste, avec chunking)
- **Fallback automatique** → si CrewAI échoue (quota, erreur), bascule sur Agno

---

## 🛠️ Technologies utilisées

| Catégorie | Technologie | Usage |
|-----------|-------------|-------|
| **Agent Framework** | [CrewAI](https://github.com/crewAIInc/crewAI) ≥ 0.80 | Pipeline multi-agents séquentiels |
| **Agent Framework** | [Agno](https://github.com/agno-agi/agno) | Agents robustes avec RAG FAISS |
| **LLM** | Google Gemini (via API) | Gemini Pro (extraction) + Flash (rapport) |
| **PDF Extraction** | [Docling](https://github.com/DS4SD/docling) | Conversion PDF → Markdown structuré |
| **Vector DB** | FAISS (local) | Embeddings pour grands documents |
| **Backend** | FastAPI + Uvicorn | API REST + WebSocket temps réel |
| **Frontend** | React 18 + Vite | Dashboard interactif |
| **Base de données** | SQLite (SQLAlchemy) | Gestion des documents et statuts |
| **Scraping** | Requests + BeautifulSoup | Navigation CMF.tn |
| **Calculs financiers** | Pandas + NumPy | KPI SCE tunisiens |

---

## 📁 Structure des dossiers

```
INETUM-MultiAgent-Financial-Analysis/
│
├── .env.example              ← Modèle de configuration (à copier en .env)
├── .gitignore                ← Fichiers exclus du versioning
├── pyproject.toml            ← Métadonnées du projet Python
├── requirements.txt          ← Dépendances Python principales
├── requirements_agno.txt     ← Dépendances supplémentaires pour Agno
├── docker-compose.yml        ← Configuration Docker (optionnel)
│
├── backend/                  ← API FastAPI + logique métier
│   ├── main.py               ← Point d'entrée du backend (FastAPI app)
│   ├── config.py             ← Configuration des chemins et variables
│   ├── database.py           ← Modèles SQLAlchemy (Document)
│   └── data/                 ← Données générées (ignorées par git)
│       ├── raw/              ← PDFs téléchargés depuis CMF.tn
│       ├── processed/        ← Fichiers Markdown extraits
│       └── rapports/         ← Rapports d'analyse générés
│
├── src/src/                  ← Modules principaux des agents
│   ├── agents/               ← Agents d'analyse IA
│   │   ├── agents.py         ← Pipeline CrewAI (Calculateur + Rapporteur)
│   │   ├── agents_agno.py    ← Pipeline Agno avec FAISS RAG
│   │   ├── dispatcher.py     ← Sélecteur intelligent de moteur
│   │   ├── crewai_tools.py   ← Outils de calcul financier CrewAI
│   │   └── financial_calculator.py ← Calculateur KPI SCE tunisien
│   ├── extractor/            ← Extraction PDF → Markdown
│   │   ├── extract.py        ← Processeur batch Docling
│   │   └── memory_optimizer.py ← Gestion mémoire pour gros PDF
│   └── scraper/              ← Scraper CMF.tn
│       └── agent.py          ← Agent CrewAI de scraping
│
├── frontend/                 ← Interface React + Vite
│   ├── src/
│   │   ├── App.jsx           ← Application principale
│   │   ├── components/       ← Composants React (Dashboard, Reports...)
│   │   ├── config/api.js     ← Configuration des endpoints API
│   │   ├── contexts/         ← Contextes React (WebSocket, état)
│   │   └── hooks/            ← Hooks personnalisés
│   ├── package.json          ← Dépendances Node.js
│   └── vite.config.js        ← Configuration Vite
│
├── tests/                    ← Tests unitaires et d'intégration
├── docs/                     ← Documentation technique
└── logs/                     ← Fichiers de log (ignorés par git)
```

---

## 📦 Prérequis

Avant d'installer le projet, assurez-vous d'avoir :

| Outil | Version minimale | Vérification |
|-------|-----------------|--------------|
| **Python** | 3.10+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 8+ | `npm --version` |
| **Git** | 2.30+ | `git --version` |

### Installation de Python (si nécessaire)
```bash
# Windows : télécharger depuis https://python.org/downloads/
# Ubuntu/Debian :
sudo apt update && sudo apt install python3.10 python3.10-venv python3-pip

# macOS avec Homebrew :
brew install python@3.10
```

### Installation de Node.js (si nécessaire)
```bash
# Windows : télécharger depuis https://nodejs.org/ (LTS)
# Ubuntu/Debian :
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# macOS avec Homebrew :
brew install node
```

---

## 🚀 Installation

### Étape 1 — Cloner le repository

```bash
git clone https://github.com/syrinemaalel1-web/INETUM-MultiAgent-Financial-Analysis.git
cd INETUM-MultiAgent-Financial-Analysis
```

### Étape 2 — Créer l'environnement virtuel Python

```bash
# Créer l'environnement virtuel
python -m venv venv
```

### Étape 3 — Activer l'environnement virtuel

**Windows (PowerShell) :**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt) :**
```cmd
venv\Scripts\activate.bat
```

**Linux / macOS :**
```bash
source venv/bin/activate
```

> ✅ Vous devriez voir `(venv)` apparaître au début de votre invite de commande.

### Étape 4 — Installer les dépendances Python

```bash
# Dépendances principales
pip install -r requirements.txt

# Dépendances Agno (pour les grands documents)
pip install -r requirements_agno.txt
```

> ⏳ L'installation peut prendre 5 à 10 minutes (Docling + modèles ML inclus).

### Étape 5 — Installer les dépendances Frontend

```bash
cd frontend
npm install
cd ..
```

---

## 🔑 Configuration des API Keys

### Variables d'environnement nécessaires

Le projet utilise **2 clés API** :

---

#### 1. `GOOGLE_API_KEY` — Clé Google Gemini (**OBLIGATOIRE**)

**Rôle :** C'est la clé principale utilisée par **tous les agents IA** du pipeline :
- Agent Scraper (Gemini 2.5 Flash)
- Agent Calculateur KPI (Gemini Pro — Long Context)
- Agent Rapporteur BVMT (Gemini 2.5 Flash)

**Comment l'obtenir :**
1. Aller sur [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Se connecter avec un compte Google
3. Cliquer sur **"Create API Key"**
4. Copier la clé générée (commence par `AIzaSy...`)

> 💡 **Quota gratuit disponible** : Google offre un quota gratuit généreux pour Gemini Flash et Pro.

---

#### 2. `OPENAI_API_KEY` — Clé OpenAI (**OPTIONNELLE**)

**Rôle :** Utilisée uniquement si vous activez les outils d'embedding OpenAI dans CrewAI. Dans la configuration actuelle du projet, seule la clé Google est indispensable.

**Comment l'obtenir :**
1. Aller sur [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Créer un compte ou se connecter
3. Cliquer sur **"+ Create new secret key"**
4. Copier la clé (commence par `sk-...`)

---

### Créer le fichier `.env`

```bash
# Copier le fichier exemple
cp .env.example .env
```

**Éditer `.env` avec vos propres clés :**

```env
# ─── OBLIGATOIRE ─────────────────────────────────────────────
GOOGLE_API_KEY=AIzaSy...votre_vraie_cle_ici...

# ─── OPTIONNEL ───────────────────────────────────────────────
OPENAI_API_KEY=sk-...votre_cle_openai_si_necessaire...

# ─── CONFIGURATION ───────────────────────────────────────────
DO_OCR=false
SAFE_MODE=false
API_HOST=0.0.0.0
API_PORT=8000
```

> ⚠️ **IMPORTANT** : Ne partagez jamais votre fichier `.env`. Il est listé dans `.gitignore` et ne sera jamais uploadé sur GitHub.

---

## ▶️ Lancement du projet

### Lancer le Backend (FastAPI)

Ouvrez un terminal dans le dossier racine du projet :

```bash
# Activer l'environnement virtuel d'abord !
# Windows : venv\Scripts\Activate.ps1
# Linux/macOS : source venv/bin/activate

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le backend sera accessible à : **http://localhost:8000**
Documentation API interactive : **http://localhost:8000/docs**

### Lancer le Frontend (React)

Ouvrez un **second terminal** :

```bash
cd frontend
npm run dev
```

Le frontend sera accessible à : **http://localhost:5173**

---

## 📊 Utilisation du pipeline

### Via l'interface web (recommandé)

1. **Ouvrir** http://localhost:5173 dans votre navigateur
2. **Dashboard** : voir les statistiques des documents (PDFs, MD, rapports)

### Workflow complet en 3 étapes

#### Étape 1 — Scraper les rapports CMF

Via l'API :
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"page_start": 0, "page_end": 2}'
```

Ou filtrer par société :
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"page_start": 0, "page_end": 5, "societe_filter": "SFBT"}'
```

#### Étape 2 — Uploader un PDF manuellement (alternative)

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@rapport_annuel_2023.pdf"
```

#### Étape 3 — Lancer l'analyse IA

```bash
# Mode automatique (dispatcher choisit le moteur)
curl -X POST http://localhost:8000/process/rapport_annuel_2023.pdf \
  -H "Content-Type: application/json" \
  -d '{"engine_mode": "auto"}'

# Forcer CrewAI (documents courts)
curl -X POST http://localhost:8000/process/rapport_annuel_2023.pdf \
  -H "Content-Type: application/json" \
  -d '{"engine_mode": "manual", "selected_engine": "crewai"}'

# Forcer Agno (documents longs, avec FAISS RAG)
curl -X POST http://localhost:8000/process/rapport_annuel_2023.pdf \
  -H "Content-Type: application/json" \
  -d '{"engine_mode": "manual", "selected_engine": "agno"}'
```

#### Récupérer les résultats

```bash
# Rapport Markdown complet
curl http://localhost:8000/report/rapport_annuel_2023.pdf

# KPIs au format JSON
curl http://localhost:8000/kpis/rapport_annuel_2023.pdf

# Liste de tous les documents
curl http://localhost:8000/documents

# Statistiques globales
curl http://localhost:8000/stats
```

### Via Docker (optionnel)

```bash
docker-compose up --build
```

---

## ❗ Troubleshooting

### Problème : `GOOGLE_API_KEY non trouvée`

**Symptôme :** Message d'avertissement au démarrage du backend ou erreur d'analyse.

**Solution :**
```bash
# Vérifier que .env existe à la racine du projet
ls -la .env

# Vérifier son contenu (ne doit PAS montrer la vraie clé dans les logs)
head -1 .env

# S'assurer que la clé est correctement définie
grep GOOGLE_API_KEY .env
```

---

### Problème : `ImportError: No module named 'crewai'`

**Solution :**
```bash
# S'assurer que l'environnement virtuel est activé
pip install -r requirements.txt
```

---

### Problème : `ModuleNotFoundError: No module named 'agno'`

**Solution :**
```bash
pip install -r requirements_agno.txt
```

---

### Problème : Erreur de mémoire lors de l'extraction PDF

**Symptôme :** `MemoryError` ou crash du backend sur gros PDF.

**Solution :**
```env
# Dans votre .env, activer le mode safe
SAFE_MODE=true
```

---

### Problème : `CORS error` dans le frontend

**Symptôme :** Erreur dans la console du navigateur lors des appels API.

**Solution :** Vérifier que le backend tourne bien sur le port 8000 et que le frontend utilise la bonne URL dans `frontend/.env` :
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

### Problème : `429 Too Many Requests` (quota Gemini)

**Symptôme :** Erreur de quota sur l'API Google.

**Solution :**
- Le dispatcher bascule automatiquement vers le moteur de secours
- Attendre quelques minutes avant de relancer
- Envisager un plan payant sur [Google AI Studio](https://aistudio.google.com/)

---

### Problème : Le scraping ne trouve pas de PDF

**Symptôme :** Aucun fichier téléchargé après le scraping.

**Solution :**
```bash
# Vérifier que le site CMF.tn est accessible
curl -I "https://www.cmf.tn/?q=consultation-des-tats-financier-des-soci-t-s-faisant-ape"

# Vérifier les logs du backend
tail -f logs/backend.log
```

---

## 🔒 Sécurité

Ce projet suit les bonnes pratiques de sécurité suivantes :

| Mesure | Statut |
|--------|--------|
| `.env` dans `.gitignore` | ✅ |
| Vraies clés **jamais** dans le code | ✅ |
| `.env.example` avec placeholders uniquement | ✅ |
| Variables d'environnement via `python-dotenv` | ✅ |
| Aucune credential dans les logs | ✅ |

**Règles à respecter absolument :**
- 🚫 Ne jamais commiter le fichier `.env`
- 🚫 Ne jamais partager vos clés API dans des issues ou PR
- 🚫 Ne jamais hardcoder une clé directement dans le code source
- ✅ Toujours utiliser `.env.example` comme référence pour les autres développeurs
- ✅ Si une clé est accidentellement exposée, la révoquer immédiatement

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour les guidelines.

```bash
# Fork le projet, puis :
git checkout -b feature/ma-fonctionnalite
git commit -m "feat: ajout de ma fonctionnalité"
git push origin feature/ma-fonctionnalite
# Ouvrir une Pull Request
```

---

## 📄 Licence

Ce projet est distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 📬 Contact

Projet réalisé dans le cadre d'un stage chez **INETUM Tunisie**.

> 💡 Si vous rencontrez un problème non documenté, ouvrez une [issue](https://github.com/syrinemaalel1-web/INETUM-MultiAgent-Financial-Analysis/issues) sur GitHub.

---

<div align="center">

**Fait avec ❤️ chez INETUM Tunisie**

*Pipeline Multi-Agent · CrewAI · Agno · Gemini · FastAPI · React*

</div>
