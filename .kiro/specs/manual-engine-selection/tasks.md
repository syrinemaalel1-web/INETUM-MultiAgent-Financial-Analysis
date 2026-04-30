# Implementation Plan - Sélection Manuelle du Moteur d'Analyse

- [x] 1. Modifier le Backend pour Supporter les Préférences Utilisateur


  - Ajouter le modèle EnginePreference dans dispatcher.py
  - Modifier analyze_financial_document pour accepter engine_preference
  - Étendre AnalysisDispatcher.execute_analysis pour respecter les préférences manuelles
  - _Requirements: 1.3, 3.1_



- [ ] 1.1 Créer les modèles de données pour les préférences
  - Définir EnginePreference avec mode et selected_engine
  - Ajouter ENGINE_INFO avec descriptions et caractéristiques
  - Créer les types de réponse enrichis avec engine_used et engine_reason


  - _Requirements: 1.1, 2.1, 2.2_

- [ ] 1.2 Modifier la logique du dispatcher
  - Ajouter check_user_preference() dans AnalysisDispatcher

  - Modifier choose_engine() pour respecter les préférences manuelles
  - Conserver la logique automatique quand mode="auto"
  - _Requirements: 1.3, 3.1_

- [ ] 1.3 Enrichir les réponses API
  - Ajouter engine_used, engine_reason dans les réponses
  - Inclure les recommandations quand mode="auto"
  - Ajouter les métadonnées de performance (temps, fallback utilisé)
  - _Requirements: 1.5, 3.2_



- [ ]* 1.4 Écrire les tests pour le backend
  - Tester la logique de préférence utilisateur
  - Tester la préservation du mode automatique
  - Tester les cas d'erreur et fallbacks
  - _Requirements: 1.3, 3.1_



- [ ] 2. Modifier l'API Backend pour Accepter les Préférences
  - Modifier l'endpoint /analyze dans main.py
  - Ajouter le paramètre engine_preference dans les requêtes


  - Mettre à jour la documentation API
  - _Requirements: 1.3_

- [ ] 2.1 Mettre à jour l'endpoint d'analyse
  - Modifier la signature de /analyze pour accepter engine_preference
  - Parser et valider les préférences utilisateur
  - Passer les préférences au dispatcher
  - _Requirements: 1.3_



- [ ] 2.2 Ajouter un endpoint d'information sur les moteurs
  - Créer /engines/info pour retourner ENGINE_INFO
  - Ajouter /engines/recommend pour les recommandations
  - Inclure les statistiques d'utilisation si disponibles
  - _Requirements: 2.1, 2.2_



- [ ]* 2.3 Tester l'API modifiée
  - Tester les requêtes avec préférences manuelles
  - Tester les requêtes en mode automatique


  - Tester la gestion d'erreurs
  - _Requirements: 1.3, 3.1_

- [ ] 3. Créer le Composant de Sélection d'Engine Frontend
  - Créer EngineSelector.jsx avec radio buttons pour CrewAI/Agno/Auto
  - Ajouter les tooltips informatifs pour chaque option


  - Implémenter la sauvegarde des préférences dans localStorage
  - _Requirements: 1.1, 1.2, 3.4_

- [ ] 3.1 Développer l'interface de sélection
  - Créer le composant EngineSelector avec trois options
  - Ajouter les icônes et descriptions pour chaque moteur
  - Implémenter les tooltips avec avantages/inconvénients



  - _Requirements: 1.1, 2.1, 2.2_

- [ ] 3.2 Ajouter la logique de recommandation
  - Créer EngineRecommendation.jsx pour suggérer le meilleur moteur
  - Analyser la taille du document pour la recommandation


  - Afficher des indicateurs visuels (badges, couleurs)
  - _Requirements: 2.3, 2.4, 2.5_

- [x] 3.3 Implémenter la persistance des préférences


  - Sauvegarder les préférences dans localStorage
  - Restaurer les préférences au chargement de l'application
  - Gérer les cas d'erreur de sauvegarde/restauration
  - _Requirements: 3.4, 3.5_


- [ ]* 3.4 Écrire les tests pour les composants
  - Tester la sélection et sauvegarde des préférences
  - Tester l'affichage des recommandations
  - Tester la persistance localStorage
  - _Requirements: 1.2, 3.4_

- [ ] 4. Intégrer la Sélection dans l'Interface d'Upload
  - Modifier FileUpload.jsx pour inclure EngineSelector
  - Passer les préférences dans les requêtes d'analyse
  - Afficher le moteur utilisé dans les résultats
  - _Requirements: 1.1, 1.5_

- [ ] 4.1 Modifier le composant d'upload
  - Intégrer EngineSelector dans FileUpload.jsx
  - Modifier handleFileUpload pour inclure engine_preference
  - Adapter l'interface utilisateur pour la nouvelle fonctionnalité
  - _Requirements: 1.1, 1.3_

- [ ] 4.2 Mettre à jour l'affichage des résultats
  - Modifier ReportView.jsx pour afficher le moteur utilisé
  - Ajouter des badges indiquant "Analysé avec CrewAI" ou "Analysé avec Agno"
  - Inclure les informations de fallback si applicable
  - _Requirements: 1.5, 3.2_

- [ ] 4.3 Améliorer l'expérience utilisateur
  - Ajouter des animations de transition entre les modes
  - Implémenter des notifications pour les changements de préférence
  - Optimiser l'interface mobile pour la sélection
  - _Requirements: 1.2, 3.4_

- [ ]* 4.4 Tester l'intégration complète
  - Tester le workflow complet avec sélection manuelle
  - Tester le passage entre modes auto/manuel
  - Tester l'affichage des résultats avec informations moteur
  - _Requirements: 1.3, 1.5, 3.1_

- [ ] 5. Checkpoint - Vérifier le Fonctionnement Complet
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Ajouter la Documentation Utilisateur
  - Créer une section d'aide expliquant les différences entre moteurs
  - Ajouter des conseils pour choisir le bon moteur
  - Documenter les cas d'usage recommandés
  - _Requirements: 2.1, 2.2_

- [ ] 6.1 Créer la documentation intégrée
  - Ajouter un modal d'aide accessible depuis EngineSelector
  - Inclure des exemples concrets d'utilisation
  - Expliquer les avantages et limitations de chaque moteur
  - _Requirements: 2.1, 2.2_

- [ ] 6.2 Ajouter des guides contextuels
  - Créer des tooltips détaillés pour chaque option
  - Ajouter des liens vers la documentation complète
  - Inclure des FAQ sur le choix du moteur
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 6.3 Tester la documentation
  - Vérifier la clarté des explications
  - Tester l'accessibilité des aides contextuelles
  - Valider les exemples et recommandations
  - _Requirements: 2.1, 2.2_

- [ ] 7. Final Checkpoint - Tests Complets et Validation
  - Ensure all tests pass, ask the user if questions arise.