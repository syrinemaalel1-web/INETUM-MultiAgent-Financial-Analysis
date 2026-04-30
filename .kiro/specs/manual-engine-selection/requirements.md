# Requirements Document - Sélection Manuelle du Moteur d'Analyse

## Introduction

Cette fonctionnalité permet à l'utilisateur de choisir manuellement entre les moteurs d'analyse CrewAI et Agno pour traiter les documents financiers CMF, au lieu de laisser le système décider automatiquement.

## Glossary

- **Moteur d'Analyse**: Système d'IA utilisé pour analyser les documents (CrewAI ou Agno)
- **Interface Utilisateur**: Interface web permettant la sélection du moteur
- **Backend API**: Service qui traite les requêtes d'analyse avec le moteur choisi
- **Dispatcher**: Composant qui route les requêtes vers le bon moteur

## Requirements

### Requirement 1

**User Story:** En tant qu'utilisateur, je veux pouvoir choisir le moteur d'analyse (CrewAI ou Agno) avant de lancer l'analyse d'un document, afin d'avoir le contrôle sur la méthode de traitement utilisée.

#### Acceptance Criteria

1. WHEN l'utilisateur accède à l'interface d'analyse THEN le système SHALL afficher une option de sélection du moteur avec CrewAI et Agno comme choix
2. WHEN l'utilisateur sélectionne un moteur d'analyse THEN le système SHALL mémoriser ce choix pour la session en cours
3. WHEN l'utilisateur lance une analyse THEN le système SHALL utiliser le moteur sélectionné et non le choix automatique
4. WHEN aucun moteur n'est sélectionné THEN le système SHALL utiliser le mode automatique par défaut
5. WHEN l'analyse est terminée THEN le système SHALL indiquer quel moteur a été utilisé dans les résultats

### Requirement 2

**User Story:** En tant qu'utilisateur, je veux voir les avantages et inconvénients de chaque moteur, afin de faire un choix éclairé selon mes besoins.

#### Acceptance Criteria

1. WHEN l'utilisateur survole ou clique sur l'option CrewAI THEN le système SHALL afficher les caractéristiques "Rapide, Simple, Documents < 20 pages"
2. WHEN l'utilisateur survole ou clique sur l'option Agno THEN le système SHALL afficher les caractéristiques "Robuste, Gros documents, Fallback intelligent"
3. WHEN l'utilisateur hésite entre les choix THEN le système SHALL proposer une recommandation basée sur la taille du document
4. WHEN le document fait plus de 50k caractères THEN le système SHALL recommander Agno avec un indicateur visuel
5. WHEN le document fait moins de 20k caractères THEN le système SHALL recommander CrewAI avec un indicateur visuel

### Requirement 3

**User Story:** En tant qu'utilisateur, je veux pouvoir revenir au mode automatique, afin de laisser le système choisir le meilleur moteur selon le contexte.

#### Acceptance Criteria

1. WHEN l'utilisateur active le mode automatique THEN le système SHALL utiliser la logique de dispatch intelligente existante
2. WHEN le mode automatique est activé THEN le système SHALL afficher quel moteur a été choisi automatiquement et pourquoi
3. WHEN une erreur survient avec le moteur choisi automatiquement THEN le système SHALL basculer vers le fallback comme prévu
4. WHEN l'utilisateur change de mode THEN le système SHALL sauvegarder la préférence dans le localStorage
5. WHEN l'utilisateur revient sur l'application THEN le système SHALL restaurer le dernier mode sélectionné