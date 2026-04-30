# Architecture Hybride des Agents KPI

## Vue d'ensemble

Le système utilise une architecture hybride optimisée avec deux modèles Gemini différents pour maximiser l'efficacité et la précision.

## Configuration des Agents

### 🧠 Agent Calculateur - Gemini 3.1 Pro
- **Modèle**: `gemini/gemini-3.1-pro`
- **Rôle**: Extraction de données financières complexes
- **Contexte**: Documents financiers longs et complexes (jusqu'à plusieurs centaines de pages)
- **Avantages**:
  - Meilleure compréhension des documents multi-pages
  - Analyse précise des tableaux financiers complexes
  - Gestion robuste des formats de données variés
  - Extraction fiable des valeurs numériques

### ⚡ Agent Rapporteur - Gemini 2.5 Flash  
- **Modèle**: `gemini/gemini-2.5-flash`
- **Rôle**: Génération de rapports financiers professionnels
- **Contexte**: KPI structurés et validés (contexte limité)
- **Avantages**:
  - Génération rapide et efficace
  - Coût optimisé pour la rédaction
  - Qualité suffisante pour les rapports structurés
  - Vitesse d'exécution élevée

## Flux de Traitement

```
Document PDF → Docling → Markdown
                ↓
    Agent Calculateur (Gemini 3.1 Pro)
    - Extraction des données financières
    - Utilisation des outils MCP pour calculs précis
                ↓
    Agent Rapporteur (Gemini 2.5 Flash)  
    - Génération du rapport d'analyse
    - Structuration et recommandations
                ↓
    Rapport Final + KPI JSON
```

## Optimisations Techniques

### Paramètres de Performance
- **Max RPM**: 10 (ajusté pour Gemini 3.1 Pro)
- **Temperature**: 0.0 (précision maximale)
- **Cache**: Activé pour optimiser les performances
- **Memory**: Désactivé pour éviter les conflits

### Gestion des Coûts
- **Agent Calculateur**: Coût plus élevé mais utilisé uniquement pour l'extraction critique
- **Agent Rapporteur**: Coût optimisé pour la génération de contenu
- **ROI**: Amélioration de la précision justifie le surcoût

## Cas d'Usage Optimaux

### Gemini 3.1 Pro (Calculateur)
- ✅ Documents financiers > 10 pages
- ✅ États financiers consolidés
- ✅ Tableaux complexes avec mise en forme variée
- ✅ Rapports avec annexes multiples
- ✅ Documents CMF tunisiens complets

### Gemini 2.5 Flash (Rapporteur)
- ✅ Génération de rapports structurés
- ✅ Analyse de KPI pré-calculés
- ✅ Rédaction de recommandations
- ✅ Formatage et présentation

## Métriques de Performance Attendues

| Métrique | Amélioration Attendue |
|----------|----------------------|
| Précision d'extraction | +15-25% |
| Gestion documents longs | +40% |
| Vitesse de génération | Maintenue |
| Coût global | +20% (ROI positif) |

## Configuration Environnement

Assurez-vous que votre clé API Gemini supporte les deux modèles :
- `gemini-3.1-pro`
- `gemini-2.5-flash`

```bash
# Vérification dans le fichier env
GOOGLE_API_KEY=your_api_key_here
```

## Monitoring et Logs

Le système génère des logs détaillés pour chaque agent :
- Temps d'exécution par modèle
- Coût par requête
- Taux de succès d'extraction
- Qualité des rapports générés

Cette architecture hybride optimise le rapport qualité/coût en utilisant la puissance de Gemini 3.1 Pro là où elle apporte le plus de valeur.