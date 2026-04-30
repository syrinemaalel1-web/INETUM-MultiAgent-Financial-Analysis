# Design Document - Sélection Manuelle du Moteur d'Analyse

## Overview

Cette fonctionnalité ajoute une interface utilisateur permettant de choisir manuellement entre CrewAI et Agno, tout en conservant l'option de mode automatique. Le système sera modifié pour respecter le choix utilisateur tout en gardant les capacités de fallback.

## Architecture

### Frontend Components
- **EngineSelector**: Composant de sélection du moteur avec tooltips informatifs
- **EngineRecommendation**: Composant qui suggère le meilleur moteur selon le document
- **AnalysisStatus**: Composant qui affiche quel moteur est utilisé pendant l'analyse

### Backend Modifications
- **API Endpoint**: Modification pour accepter le paramètre `engine_preference`
- **Dispatcher Enhancement**: Extension pour respecter les préférences utilisateur
- **Response Enhancement**: Ajout d'informations sur le moteur utilisé

## Components and Interfaces

### Frontend Interface

```typescript
interface EnginePreference {
  mode: 'auto' | 'manual';
  selectedEngine?: 'crewai' | 'agno';
  recommendation?: {
    engine: 'crewai' | 'agno';
    reason: string;
    confidence: number;
  };
}

interface AnalysisRequest {
  file: File;
  enginePreference: EnginePreference;
}

interface AnalysisResponse {
  success: boolean;
  engineUsed: 'crewai' | 'agno' | 'agno_fallback';
  engineReason: string;
  results: any;
}
```

### Backend Interface

```python
class EnginePreference(BaseModel):
    mode: Literal["auto", "manual"] = "auto"
    selected_engine: Optional[Literal["crewai", "agno"]] = None

class AnalysisRequest(BaseModel):
    company_name: str
    engine_preference: EnginePreference = EnginePreference()

class AnalysisResponse(BaseModel):
    success: bool
    engine_used: str
    engine_reason: str
    recommendation: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
```

## Data Models

### Engine Information
```python
ENGINE_INFO = {
    "crewai": {
        "name": "CrewAI",
        "description": "Rapide et simple",
        "best_for": ["Documents < 20 pages", "Analyse rapide", "Prototypage"],
        "limitations": ["Pas de fallback quota", "Limite de contexte"],
        "icon": "⚡"
    },
    "agno": {
        "name": "Agno Framework", 
        "description": "Robuste et intelligent",
        "best_for": ["Gros documents", "Fallback automatique", "Production"],
        "limitations": ["Plus complexe", "Setup initial"],
        "icon": "🧠"
    }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Engine Selection Respect
*For any* user engine selection (manual mode), the system should use exactly the selected engine and not override it with automatic logic
**Validates: Requirements 1.3**

### Property 2: Automatic Mode Preservation  
*For any* automatic mode selection, the system should behave exactly as the original dispatcher logic without user preference interference
**Validates: Requirements 3.1**

### Property 3: Preference Persistence
*For any* user preference change, the system should persist the preference and restore it on subsequent visits
**Validates: Requirements 3.4, 3.5**

### Property 4: Recommendation Accuracy
*For any* document analysis, when providing recommendations, the system should suggest the engine that the automatic logic would choose
**Validates: Requirements 2.4, 2.5**

## Error Handling

### Frontend Error Handling
- Invalid engine selection → Reset to auto mode
- Network errors during analysis → Show engine-specific error messages
- Preference save failures → Fallback to session storage

### Backend Error Handling  
- Invalid engine preference → Use automatic mode
- Selected engine unavailable → Log warning and use automatic fallback
- Preference parsing errors → Default to automatic mode

## Testing Strategy

### Unit Tests
- Test engine preference parsing and validation
- Test preference persistence in localStorage
- Test recommendation logic accuracy
- Test API parameter handling

### Property-Based Tests
- **Property 1**: Engine selection respect - Generate random preferences and verify correct engine usage
- **Property 2**: Automatic mode preservation - Verify automatic logic unchanged when no preference set
- **Property 3**: Preference persistence - Test preference save/restore across sessions
- **Property 4**: Recommendation accuracy - Verify recommendations match automatic dispatcher logic

### Integration Tests
- Test full workflow with manual engine selection
- Test fallback behavior when manual selection fails
- Test UI state management across engine switches
- Test API integration with engine preferences