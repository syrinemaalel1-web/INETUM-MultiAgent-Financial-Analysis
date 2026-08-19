# 🚀 Guide de Démarrage Complet — CMF Analysis Platform

## Prérequis à installer (une seule fois)

| Outil | Version minimale | Lien |
|-------|-----------------|------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| Git | any | https://git-scm.com/ |

Vérifier les installations :
```powershell
python --version     # doit afficher 3.10+
node --version       # doit afficher v18+
npm --version        # doit afficher 9+
git --version
```

---

## 📁 Étape 1 — Cloner le projet

```powershell
git clone https://github.com/Ghassenboussalem/Investi.git
cd Investi
git checkout feature/cmf-analysis-platform
```

---

## 🔑 Étape 2 — Configurer les clés API

Copier le fichier d'exemple et renseigner vos clés :

```powershell
copy env.example .env
```

Ouvrir `.env` et remplir :

```env
GOOGLE_API_KEY=AIzaSy...        # Clé Google Gemini (obligatoire)
OPENAI_API_KEY=sk-...           # Clé OpenAI (optionnelle)
DO_OCR=false
SAFE_MODE=false
API_HOST=0.0.0.0
API_PORT=8000
```

> **Obtenir GOOGLE_API_KEY** : https://aistudio.google.com/app/apikey  
> Activer "Generative Language API" dans Google Cloud Console.

---

## 🐍 Étape 3 — Installer les dépendances Python

### Option A — Avec venv (recommandé)
```powershell
# Créer l'environnement virtuel
python -m venv venv

# Activer (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Si erreur de politique d'exécution :
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Installer toutes les dépendances
```powershell
# Dépendances principales (FastAPI, scraper, extractor)
pip install -r requirements.txt

# Dépendances Agno + RAG FAISS (agents IA)
pip install -r requirements_agno.txt

# Dépendances CrewAI (moteur alternatif)
pip install -r requirements_agents.txt
```

> ⏱️ L'installation prend ~5-10 minutes selon votre connexion.  
> 📦 Les modèles BGE-M3 (~570 MB) seront téléchargés automatiquement au premier lancement.

---

## 🗂️ Étape 4 — Créer les dossiers de données

```powershell
# Depuis la racine du projet
mkdir backend\data\raw
mkdir backend\data\processed
mkdir backend\data\rapports
```

---

## ⚙️ Étape 5 — Lancer le Backend (API FastAPI)

**Ouvrir un premier terminal PowerShell :**

```powershell
# Se placer dans le dossier backend
cd backend

# Lancer le serveur
python main.py
```

✅ Le backend est prêt quand vous voyez :
```
INFO: Tous les modules sont importés avec succès.
INFO: Started server process
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

> **Si erreur port 8000 déjà utilisé :**
> ```powershell
> # Trouver et tuer le processus
> netstat -ano | findstr :8000
> taskkill /PID <PID_AFFICHÉ> /F
> # Puis relancer python main.py
> ```

---

## 🌐 Étape 6 — Lancer le Frontend (React + Vite)

**Ouvrir un deuxième terminal PowerShell :**

```powershell
# Se placer dans le dossier frontend
cd frontend

# Installer les dépendances Node (première fois uniquement)
npm install

# Lancer le serveur de développement
npm run dev
```

✅ Le frontend est prêt quand vous voyez :
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

## 🌍 Accès à l'application

| Service | URL |
|---------|-----|
| **Frontend** (interface) | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **Documentation API** | http://localhost:8000/docs |
| **Santé API** | http://localhost:8000/health |

---

## 📊 Utilisation du pipeline complet

### 1. Scraper les PDFs CMF
Dans l'interface → cliquer **"Lancer le Scraping"**  
Ou via l'API :
```powershell
curl http://localhost:8000/scrape
```

### 2. Analyser un document
Dans l'interface → sélectionner un PDF → cliquer **"Analyser"**  
Choisir le moteur : **Agno** (recommandé) ou CrewAI

### 3. Voir les résultats
- **KPI Dashboard** : 11 indicateurs SCE Tunisie avec graphiques
- **Rapport** : Analyse narrative complète exportable en PDF

---

## 🔄 Commandes de démarrage rapide (sessions suivantes)

```powershell
# Terminal 1 — Backend
cd Investi\backend
.\venv\Scripts\Activate.ps1   # si venv à la racine
python main.py

# Terminal 2 — Frontend
cd Investi\frontend
npm run dev
```

---

## 🐛 Dépannage fréquent

### `ModuleNotFoundError: No module named 'agno'`
```powershell
pip install -r requirements_agno.txt
```

### `Agent.__init__() got an unexpected keyword argument`
```powershell
pip install --upgrade agno
```

### `[Errno 10048] error while attempting to bind on address 0.0.0.0:8000`
```powershell
# PowerShell — trouver et tuer le processus sur le port 8000
$p = netstat -ano | findstr ":8000 " | Select-String "LISTENING"
$pid = ($p -split '\s+')[-1]
taskkill /PID $pid /F
```

### `GOOGLE_API_KEY not found`
Vérifier que `.env` existe à la racine et contient la clé :
```powershell
Get-Content .env
```

### Modèle BGE-M3 lent au premier lancement
Normal — téléchargement unique de ~570 MB. Les lancements suivants utilisent le cache local.

### Frontend `npm install` échoue
```powershell
npm cache clean --force
Remove-Item -Recurse -Force node_modules
npm install
```

---

## 📁 Structure du projet

```
Investi/
├── backend/              # API FastAPI
│   ├── main.py          # Point d'entrée serveur
│   ├── config.py        # Configuration chemins
│   └── data/
│       ├── raw/         # PDFs téléchargés
│       ├── processed/   # Markdown extraits
│       └── rapports/    # Rapports générés
├── frontend/             # Interface React
│   ├── src/components/
│   │   ├── KPIDashboard.jsx   # 11 KPI + graphiques
│   │   └── ReportView.jsx     # Rapport stylisé + PDF
│   └── package.json
├── src/src/
│   ├── agents/
│   │   ├── agents_agno.py     # Moteur Agno + RAG FAISS
│   │   └── agents.py          # Moteur CrewAI
│   ├── extractor/extract.py   # Docling PDF → Markdown
│   └── scraper/agent.py       # Scraper CMF
├── .env                  # Vos clés API (ne pas committer)
├── requirements.txt      # Dépendances principales
├── requirements_agno.txt # Dépendances Agno + RAG
└── requirements_agents.txt  # Dépendances CrewAI
```