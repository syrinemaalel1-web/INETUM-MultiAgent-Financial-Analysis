# CMF Tunisie - Frontend React

Cette interface permet de piloter le pipeline d'analyse financière.

## Prérequis
- Node.js (v18+)
- npm ou yarn

## Installation Rapide
1. Naviguez dans ce dossier : `cd frontend`
2. Installez les dépendances : `npm install`
3. Lancez le serveur de développement : `npm run dev`

## Structure
- `src/App.jsx` : Gestion de la navigation et de l'état global.
- `src/components/Dashboard.jsx` : Statistiques et progression.
- `src/components/DocumentList.jsx` : Liste des PDFs et actions.
- `src/components/ScraperControl.jsx` : Pilotage du scraper.
- `src/components/ReportView.jsx` : Affichage des rapports Markdown.

## Note
L'interface communique avec le backend FastAPI sur `http://localhost:8000`. Assurez-vous que le backend est lancé avant d'utiliser l'interface.
