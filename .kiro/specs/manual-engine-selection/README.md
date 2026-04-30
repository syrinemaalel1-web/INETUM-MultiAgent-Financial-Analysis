# Sélection Manuelle du Moteur d'Analyse - Documentation

## 🎯 Vue d'ensemble

Cette fonctionnalité permet aux utilisateurs de choisir manuellement entre les moteurs d'analyse **CrewAI** et **Agno** pour traiter leurs documents financiers CMF, tout en conservant l'option de mode automatique.

## ✨ Fonctionnalités Implémentées

### 1. Backend (Python/FastAPI)

#### Dispatcher Amélioré (`src/src/agents/dispatcher.py`)
- ✅ Modèles Pydantic pour les préférences utilisateur (`EnginePreference`)
- ✅ Informations détaillées sur chaque moteur (`ENGINE_INFO`)
- ✅ Logique de recommandation intelligente
- ✅ Respect des préférences manuelles avec fallback automatique
- ✅ Enrichissement des réponses avec métadonnées moteur

#### API Endpoints (`backend/main.py`)
- ✅ `POST /process/{filename}` - Accepte les préférences de moteur
- ✅ `GET /engines/info` - Retourne les informations sur les moteurs
- ✅ `POST /engines/recommend` - Génère une recommandation basée sur le document

### 2. Frontend (React)

#### Composants Créés
- ✅ `EngineSelector.jsx` - Sélecteur de moteur avec tooltips
- ✅ `EngineRecommendation.jsx` - Affichage des recommandations
- ✅ `useEnginePreference.js` - Hook pour la persistance localStorage

#### Intégrations
- ✅ Modal de sélection dans `DocumentList.jsx`
- ✅ Badges de moteur utilisé dans `ReportView.jsx`
- ✅ Persistance automatique des préférences

## 🚀 Utilisation

### Mode Automatique (Par défaut)
1. Cliquez sur "Lancer l'Analyse" pour un document
2. Le modal s'ouvre avec le mode "Automatique" sélectionné
3. Le système choisit automatiquement le meilleur moteur
4. Une recommandation est affichée pour information

### Mode Manuel
1. Cliquez sur "Lancer l'Analyse" pour un document
2. Sélectionnez le mode "Manuel" dans le modal
3. Choisissez entre CrewAI ⚡ ou Agno 🧠
4. Survolez les cartes pour voir les détails (avantages/limitations)
5. Cliquez sur "Lancer l'Analyse"

### Persistance
- Vos préférences sont automatiquement sauvegardées
- Elles sont restaurées à chaque visite
- Fonctionne via localStorage (fallback sur sessionStorage)

## 📊 Informations sur les Moteurs

### CrewAI ⚡
**Idéal pour :**
- Documents < 20 pages
- Analyse rapide
- Prototypage
- Documents standards

**Limitations :**
- Pas de fallback quota automatique
- Limite de contexte stricte
- Moins robuste sur gros documents

### Agno Framework 🧠
**Idéal pour :**
- Documents volumineux (> 20 pages)
- Fallback automatique sur quota
- Production critique
- Documents complexes (Tunisair, etc.)

**Limitations :**
- Setup plus complexe
- Légèrement plus lent
- Nécessite plus de configuration

## 🔧 Architecture Technique

### Flux de Données

```
Frontend (DocumentList)
    ↓
[Sélection Utilisateur]
    ↓
POST /process/{filename}
    {
      engine_mode: "manual",
      selected_engine: "agno"
    }
    ↓
Backend (main.py)
    ↓
Dispatcher (dispatcher.py)
    ↓
[Choix du Moteur]
    ↓
CrewAI ou Agno
    ↓
[Résultats + Métadonnées]
    ↓
Frontend (ReportView)
```

### Modèles de Données

```python
class EnginePreference(BaseModel):
    mode: Literal["auto", "manual"] = "auto"
    selected_engine: Optional[Literal["crewai", "agno"]] = None

class EngineRecommendation(BaseModel):
    engine: Literal["crewai", "agno"]
    reason: str
    confidence: float
    document_analysis: Dict[str, Any]
```

## 🧪 Tests

### Tests Manuels Recommandés

1. **Test Mode Automatique**
   - Lancer une analyse en mode auto
   - Vérifier que la recommandation est affichée
   - Confirmer que le bon moteur est utilisé

2. **Test Mode Manuel - CrewAI**
   - Sélectionner manuellement CrewAI
   - Lancer l'analyse
   - Vérifier le badge dans le rapport

3. **Test Mode Manuel - Agno**
   - Sélectionner manuellement Agno
   - Lancer l'analyse
   - Vérifier le badge dans le rapport

4. **Test Persistance**
   - Changer de préférence
   - Rafraîchir la page
   - Vérifier que la préférence est restaurée

5. **Test Recommandations**
   - Tester avec un petit document (< 10 pages)
   - Tester avec un gros document (> 30 pages)
   - Vérifier que les recommandations sont pertinentes

## 📝 Notes de Développement

### Compatibilité Backend
- Le paramètre `force_engine` (legacy) est toujours supporté
- Conversion automatique vers `EnginePreference`
- Rétrocompatibilité assurée

### Gestion d'Erreurs
- Préférence invalide → Mode automatique
- Moteur non disponible → Fallback automatique
- Erreur localStorage → Fallback sessionStorage

### Performance
- Les préférences sont chargées une seule fois au montage
- Pas d'appels API supplémentaires pour la sélection
- Recommandations calculées côté backend

## 🎨 Personnalisation

### Modifier les Informations Moteur
Éditez `ENGINE_INFO` dans `src/src/agents/dispatcher.py`

### Modifier les Styles
- `frontend/src/components/EngineSelector.css`
- `frontend/src/components/EngineRecommendation.css`

### Ajuster la Logique de Recommandation
Modifiez `_generate_recommendation()` dans `dispatcher.py`

## 🐛 Dépannage

### Le modal ne s'ouvre pas
- Vérifier que `EngineSelector` est bien importé
- Vérifier la console pour les erreurs React

### Les préférences ne sont pas sauvegardées
- Vérifier que localStorage est activé dans le navigateur
- Vérifier la console pour les erreurs de sauvegarde

### L'API ne reçoit pas les préférences
- Vérifier le payload dans Network tab
- Vérifier que `ProcessRequest` est bien défini dans `main.py`

## 📚 Ressources

- [Spec Requirements](.kiro/specs/manual-engine-selection/requirements.md)
- [Spec Design](.kiro/specs/manual-engine-selection/design.md)
- [Spec Tasks](.kiro/specs/manual-engine-selection/tasks.md)
- [Agno vs CrewAI Comparison](../../../AGNO_VS_CREWAI_COMPARISON.md)

## ✅ Statut d'Implémentation

- [x] Backend - Modèles de données
- [x] Backend - Logique dispatcher
- [x] Backend - API endpoints
- [x] Frontend - Composant sélecteur
- [x] Frontend - Composant recommandation
- [x] Frontend - Hook persistance
- [x] Frontend - Intégration DocumentList
- [x] Frontend - Badges ReportView
- [ ] Tests unitaires backend
- [ ] Tests unitaires frontend
- [ ] Tests d'intégration
- [ ] Documentation utilisateur

---

**Dernière mise à jour :** 30 avril 2026
**Version :** 1.0.0
