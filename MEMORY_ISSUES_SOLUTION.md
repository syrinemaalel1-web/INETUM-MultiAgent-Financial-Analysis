# Solution aux Problèmes de Mémoire (std::bad_alloc)

## 🔴 Problème Identifié

Vous rencontrez l'erreur `std::bad_alloc` (manque de mémoire) lors du traitement de documents volumineux comme **Tunisair (67 pages)** avec Docling.

```
[ERROR] Stage preprocess failed for run 1, pages [22]: std::bad_alloc
RuntimeError: [enforce fail at alloc_cpu.cpp:117] data. DefaultCPUAllocator: 
not enough memory: you tried to allocate 6553600 bytes.
```

## ✅ Solutions Implémentées

### 1. Optimiseur Mémoire Automatique

J'ai créé un système qui :
- ✅ Détecte automatiquement les erreurs de mémoire
- ✅ Crée un fichier Markdown de fallback avec recommandations
- ✅ Suggère d'utiliser Agno Framework pour les gros documents

**Fichier créé** : `src/src/extractor/memory_optimizer.py`

### 2. Limites de Pages Réduites

**Fichier modifié** : `env`

```bash
# Optimisations mémoire pour Docling
DOCLING_MAX_PAGES=15          # Réduit de 20 à 15 pages
DOCLING_BATCH_SIZE=1          # Traitement page par page
DOCLING_LOW_MEMORY=true       # Mode économie mémoire
DOCLING_SKIP_PAGES=true       # Nouveau: Skip pages problématiques
```

### 3. Gestion Intelligente des Erreurs

**Fichier modifié** : `src/src/extractor/extract.py`

L'extracteur détecte maintenant les erreurs mémoire et :
1. Crée un fichier Markdown informatif
2. Recommande d'utiliser Agno Framework
3. Fournit des statistiques sur le document

## 🚀 Comment Utiliser

### Option 1 : Utiliser Agno Framework (RECOMMANDÉ)

C'est exactement pour ça que nous avons créé le système de sélection de moteur !

1. **Lancez l'analyse** du document Tunisair
2. **Sélectionnez "Manuel"** dans le modal
3. **Choisissez "Agno 🧠"**
4. **Lancez l'analyse**

Agno va :
- ✅ Découper le document en chunks intelligents
- ✅ Traiter chaque section séparément
- ✅ Gérer automatiquement les fallbacks
- ✅ Réussir là où CrewAI échoue

### Option 2 : Augmenter la Mémoire Disponible

**Avant de lancer l'extraction** :
1. Fermez toutes les applications non nécessaires
2. Fermez les navigateurs avec beaucoup d'onglets
3. Redémarrez votre ordinateur si nécessaire

### Option 3 : Traiter par Sections

Si vous voulez quand même utiliser Docling :

1. **Divisez le PDF** en plusieurs fichiers plus petits (< 15 pages chacun)
2. **Traitez chaque section** séparément
3. **Combinez les résultats** manuellement

## 📊 Stratégies par Taille de Document

| Taille Document | Pages | Stratégie Recommandée |
|-----------------|-------|----------------------|
| Petit | < 10 pages | CrewAI ⚡ (rapide) |
| Moyen | 10-20 pages | CrewAI ⚡ ou Agno 🧠 |
| Grand | 20-40 pages | **Agno 🧠** (chunking) |
| Très Grand | > 40 pages | **Agno 🧠** (obligatoire) |

## 🔧 Configuration Avancée

### Réduire Encore Plus la Limite

Si vous avez toujours des problèmes, éditez `env` :

```bash
DOCLING_MAX_PAGES=10  # Encore plus conservateur
```

### Désactiver l'OCR

L'OCR consomme beaucoup de mémoire :

```bash
DO_OCR=false
```

### Mode Safe

Active des protections supplémentaires :

```bash
SAFE_MODE=true
```

## 🎯 Workflow Recommandé pour Tunisair

```
1. Upload du PDF Tunisair (67 pages)
   ↓
2. Docling tente l'extraction
   ↓
3. Erreur mémoire détectée
   ↓
4. Fichier Markdown de fallback créé
   ↓
5. Vous lancez l'analyse avec Agno 🧠
   ↓
6. Agno découpe en chunks de 10 pages
   ↓
7. Traitement réussi ! ✅
```

## 📝 Exemple de Fichier Fallback

Quand une erreur mémoire survient, vous obtenez :

```markdown
# Extraction Partielle - TUNISAIR_2022

## ⚠️ Avertissement
Ce document n'a pas pu être extrait complètement en raison de contraintes mémoire.

### Informations sur l'erreur
- **Type**: Erreur mémoire (std::bad_alloc)
- **Fichier**: TUNISAIR_2022.pdf
- **Taille**: 8.5 MB
- **Pages estimées**: 67

### Recommandation
Utiliser Agno Framework avec chunking intelligent

### Solutions possibles
1. **Utiliser Agno Framework** (recommandé)
2. **Augmenter la mémoire disponible**
3. **Traiter manuellement**
```

## 🐛 Dépannage

### L'erreur persiste même avec Agno

1. Vérifiez que vous avez bien installé les dépendances Agno :
   ```bash
   pip install -r requirements_agno.txt
   ```

2. Vérifiez les logs pour voir si Agno est bien utilisé

### Le système ne détecte pas l'erreur mémoire

Les logs devraient montrer :
```
❌ ERREUR MÉMOIRE détectée pour TUNISAIR_2022.pdf
   Taille: 8.50 MB
   Pages estimées: 67
```

Si vous ne voyez pas ça, l'erreur n'est peut-être pas de type mémoire.

## 📚 Ressources

- [Agno vs CrewAI Comparison](AGNO_VS_CREWAI_COMPARISON.md)
- [Hybrid Architecture Benefits](HYBRID_ARCHITECTURE_BENEFITS.md)
- [Manual Engine Selection Spec](.kiro/specs/manual-engine-selection/README.md)

## ✅ Checklist de Résolution

- [x] Optimiseur mémoire créé
- [x] Limites de pages réduites (15 pages)
- [x] Gestion d'erreurs améliorée
- [x] Fichiers fallback automatiques
- [x] Recommandations Agno intégrées
- [x] Documentation complète

---

**La solution est maintenant en place !** 

Pour le document Tunisair, **utilisez simplement Agno 🧠** via l'interface de sélection de moteur que nous venons de créer.

**Dernière mise à jour** : 30 avril 2026
