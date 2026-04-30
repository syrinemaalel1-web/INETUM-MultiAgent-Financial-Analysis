"""
dispatcher.py — Dispatcher Intelligent CrewAI vs Agno
Choix automatique du moteur d'analyse selon le contexte

LOGIQUE DE DISPATCH :
- Documents < 20 pages + Quota OK → CrewAI (rapide et simple)
- Documents > 20 pages OU Quota limité → Agno (robuste et intelligent)
- Erreurs CrewAI → Fallback automatique vers Agno
- Préférence utilisateur → Respecte le choix manuel
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Literal
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AnalysisEngine(Enum):
    """Moteurs d'analyse disponibles"""
    CREWAI = "crewai"
    AGNO = "agno"

class DispatchReason(Enum):
    """Raisons du choix du moteur"""
    DOCUMENT_SIZE = "document_size"
    QUOTA_LIMIT = "quota_limit"
    CREWAI_ERROR = "crewai_error"
    USER_PREFERENCE = "user_preference"
    DEFAULT = "default"

# ════════════════════════════════════════════════════════
# MODÈLES DE DONNÉES POUR PRÉFÉRENCES UTILISATEUR
# ════════════════════════════════════════════════════════

class EnginePreference(BaseModel):
    """Modèle pour les préférences utilisateur de moteur d'analyse"""
    mode: Literal["auto", "manual"] = Field(
        default="auto",
        description="Mode de sélection: 'auto' pour automatique, 'manual' pour choix utilisateur"
    )
    selected_engine: Optional[Literal["crewai", "agno"]] = Field(
        default=None,
        description="Moteur sélectionné manuellement (requis si mode='manual')"
    )

class EngineRecommendation(BaseModel):
    """Recommandation de moteur basée sur l'analyse du document"""
    engine: Literal["crewai", "agno"] = Field(description="Moteur recommandé")
    reason: str = Field(description="Raison de la recommandation")
    confidence: float = Field(description="Niveau de confiance (0-1)", ge=0, le=1)
    document_analysis: Dict[str, Any] = Field(description="Analyse du document")

# Informations détaillées sur chaque moteur
ENGINE_INFO = {
    "crewai": {
        "name": "CrewAI",
        "icon": "⚡",
        "description": "Rapide et simple",
        "best_for": [
            "Documents < 20 pages",
            "Analyse rapide",
            "Prototypage",
            "Documents standards"
        ],
        "limitations": [
            "Pas de fallback quota automatique",
            "Limite de contexte stricte",
            "Moins robuste sur gros documents"
        ],
        "performance": {
            "speed": "Très rapide",
            "reliability": "Bonne (documents standards)",
            "cost": "Optimal"
        }
    },
    "agno": {
        "name": "Agno Framework",
        "icon": "🧠",
        "description": "Robuste et intelligent",
        "best_for": [
            "Documents volumineux (> 20 pages)",
            "Fallback automatique sur quota",
            "Production critique",
            "Documents complexes (Tunisair, etc.)"
        ],
        "limitations": [
            "Setup plus complexe",
            "Légèrement plus lent",
            "Nécessite plus de configuration"
        ],
        "performance": {
            "speed": "Rapide",
            "reliability": "Excellente (tous documents)",
            "cost": "Optimisé avec fallback"
        }
    }
}

class AnalysisDispatcher:
    """Dispatcher intelligent pour choisir entre CrewAI et Agno"""
    
    def __init__(self):
        self.quota_errors_count = 0
        self.max_quota_errors = 3  # Après 3 erreurs quota, basculer vers Agno
        
        # Seuils de configuration
        self.large_document_threshold = 50000  # 50k caractères
        self.max_pages_crewai = 20
        
        # Statistiques
        self.stats = {
            "crewai_success": 0,
            "crewai_failures": 0,
            "agno_success": 0,
            "agno_failures": 0,
            "total_dispatches": 0
        }
    
    def analyze_document_complexity(self, rapport_md: str, md_file_path: Path = None) -> Dict[str, Any]:
        """Analyse la complexité du document pour le dispatch"""
        
        # Métriques de base
        char_count = len(rapport_md)
        line_count = rapport_md.count('\n')
        table_count = rapport_md.count('|')  # Approximation des tableaux
        
        # Estimation du nombre de pages (approximative)
        estimated_pages = max(1, char_count // 2500)  # ~2500 chars par page
        
        # Détection de mots-clés complexes
        complex_keywords = [
            'BILAN CONSOLIDÉ', 'ÉTATS FINANCIERS', 'ANNEXES',
            'NOTES AUX ÉTATS', 'RAPPORT ANNUEL', 'TUNISAIR',
            'GROUPE', 'FILIALES', 'PARTICIPATIONS'
        ]
        
        complexity_score = sum(1 for keyword in complex_keywords if keyword in rapport_md.upper())
        
        # Classification de complexité
        if char_count > 100000 or estimated_pages > 30 or complexity_score > 3:
            complexity = "high"
        elif char_count > 50000 or estimated_pages > 15 or complexity_score > 1:
            complexity = "medium"
        else:
            complexity = "low"
        
        return {
            "char_count": char_count,
            "estimated_pages": estimated_pages,
            "table_count": table_count,
            "complexity_score": complexity_score,
            "complexity": complexity,
            "is_large": char_count > self.large_document_threshold
        }
    
    def check_quota_status(self) -> Tuple[bool, str]:
        """Vérifie le statut du quota Gemini"""
        
        # Si trop d'erreurs quota récentes, considérer comme limité
        if self.quota_errors_count >= self.max_quota_errors:
            return False, f"Quota errors: {self.quota_errors_count}/{self.max_quota_errors}"
        
        # TODO: Implémenter une vérification réelle du quota via API
        # Pour l'instant, on assume que le quota est OK
        return True, "Quota available"
    
    def choose_engine(
        self, 
        rapport_md: str, 
        md_file_path: Path = None,
        force_engine: Optional[AnalysisEngine] = None,
        user_preference: Optional[EnginePreference] = None
    ) -> Tuple[AnalysisEngine, DispatchReason, Dict[str, Any]]:
        """
        Choisit le moteur d'analyse optimal
        
        Args:
            rapport_md: Contenu du document
            md_file_path: Chemin du fichier
            force_engine: Force un moteur (legacy, utilisez user_preference)
            user_preference: Préférence utilisateur (mode auto/manual)
        
        Returns:
            Tuple[AnalysisEngine, DispatchReason, Dict[metadata]]
        """
        
        self.stats["total_dispatches"] += 1
        
        # Priorité 1: Préférence utilisateur en mode manuel
        if user_preference and user_preference.mode == "manual" and user_preference.selected_engine:
            try:
                engine = AnalysisEngine(user_preference.selected_engine)
                logger.info(f"👤 Préférence utilisateur : {engine.value}")
                
                # Générer quand même une recommandation pour information
                recommendation = self._generate_recommendation(rapport_md, md_file_path)
                
                metadata = {
                    "user_preference": user_preference.dict(),
                    "recommendation": recommendation.dict()
                }
                
                if engine.value != recommendation.engine:
                    logger.info(f"ℹ️ Note: Le système aurait recommandé {recommendation.engine}")
                    logger.info(f"   Raison: {recommendation.reason}")
                
                return engine, DispatchReason.USER_PREFERENCE, metadata
                
            except ValueError:
                logger.warning(f"⚠️ Moteur invalide '{user_preference.selected_engine}', utilisation automatique")
        
        # Priorité 2: Force un moteur spécifique (legacy)
        if force_engine:
            return force_engine, DispatchReason.USER_PREFERENCE, {}
        
        # Priorité 3: Mode automatique (comportement par défaut)
        return self._choose_engine_automatic(rapport_md, md_file_path)
    
    def _generate_recommendation(
        self, 
        rapport_md: str, 
        md_file_path: Path = None
    ) -> EngineRecommendation:
        """
        Génère une recommandation de moteur basée sur l'analyse du document
        """
        # Analyse du document
        doc_analysis = self.analyze_document_complexity(rapport_md, md_file_path)
        
        # Vérification du quota
        quota_ok, quota_status = self.check_quota_status()
        
        # Logique de recommandation
        if doc_analysis["complexity"] == "high" or doc_analysis["estimated_pages"] > 25:
            return EngineRecommendation(
                engine="agno",
                reason=f"Document complexe ({doc_analysis['estimated_pages']} pages estimées)",
                confidence=0.9,
                document_analysis=doc_analysis
            )
        
        if not quota_ok:
            return EngineRecommendation(
                engine="agno",
                reason=f"Quota Gemini limité ({quota_status})",
                confidence=0.95,
                document_analysis=doc_analysis
            )
        
        if doc_analysis["complexity"] in ["low", "medium"] and quota_ok:
            return EngineRecommendation(
                engine="crewai",
                reason=f"Document standard ({doc_analysis['estimated_pages']} pages, quota OK)",
                confidence=0.85,
                document_analysis=doc_analysis
            )
        
        # Par défaut, recommander Agno pour la sécurité
        return EngineRecommendation(
            engine="agno",
            reason="Recommandation par défaut pour robustesse",
            confidence=0.7,
            document_analysis=doc_analysis
        )
    
    def _choose_engine_automatic(
        self, 
        rapport_md: str, 
        md_file_path: Path = None
    ) -> Tuple[AnalysisEngine, DispatchReason, Dict[str, Any]]:
        """
        Choix automatique du moteur (logique originale)
        """
        # Analyse du document
        doc_analysis = self.analyze_document_complexity(rapport_md, md_file_path)
        
        # Vérification du quota
        quota_ok, quota_status = self.check_quota_status()
        
        # Logique de décision
        metadata = {
            "document_analysis": doc_analysis,
            "quota_status": quota_status,
            "quota_errors_count": self.quota_errors_count
        }
        
        # Cas 1: Document très volumineux → Agno obligatoire
        if doc_analysis["complexity"] == "high" or doc_analysis["estimated_pages"] > 25:
            logger.info(f"📊 Document complexe détecté → Agno")
            logger.info(f"   - Pages estimées: {doc_analysis['estimated_pages']}")
            logger.info(f"   - Complexité: {doc_analysis['complexity']}")
            return AnalysisEngine.AGNO, DispatchReason.DOCUMENT_SIZE, metadata
        
        # Cas 2: Quota limité → Agno (fallback intelligent)
        if not quota_ok:
            logger.info(f"⚠️ Quota Gemini limité → Agno")
            logger.info(f"   - Statut: {quota_status}")
            return AnalysisEngine.AGNO, DispatchReason.QUOTA_LIMIT, metadata
        
        # Cas 3: Document moyen + quota OK → CrewAI (optimal)
        if doc_analysis["complexity"] in ["low", "medium"] and quota_ok:
            logger.info(f"✅ Document standard → CrewAI")
            logger.info(f"   - Pages estimées: {doc_analysis['estimated_pages']}")
            logger.info(f"   - Complexité: {doc_analysis['complexity']}")
            return AnalysisEngine.CREWAI, DispatchReason.DEFAULT, metadata
        
        # Cas par défaut → Agno (sécurité)
        logger.info(f"🔄 Cas par défaut → Agno")
        return AnalysisEngine.AGNO, DispatchReason.DEFAULT, metadata
    
    def execute_analysis(
        self, 
        rapport_md: str, 
        output_path: Path = None, 
        md_file_path: Path = None,
        company_name: str = "Entreprise Tunisienne",
        user_preference: Optional[EnginePreference] = None
    ) -> Dict[str, Any]:
        """
        Exécute l'analyse avec le moteur optimal et gestion des fallbacks
        
        Args:
            rapport_md: Contenu du document
            output_path: Chemin de sortie
            md_file_path: Chemin source
            company_name: Nom de l'entreprise
            user_preference: Préférence utilisateur pour le moteur
        """
        
        # Choix du moteur initial
        engine, reason, metadata = self.choose_engine(
            rapport_md, 
            md_file_path,
            user_preference=user_preference
        )
        
        logger.info(f"🚀 Dispatch: {engine.value} (raison: {reason.value})")
        
        # Ajouter la recommandation si en mode manuel
        recommendation = None
        if user_preference and user_preference.mode == "manual":
            recommendation = self._generate_recommendation(rapport_md, md_file_path)
        
        try:
            if engine == AnalysisEngine.CREWAI:
                result = self._execute_crewai(rapport_md, output_path, md_file_path, company_name)
                
                # Vérifier si c'est une erreur de quota
                if not result.get("success", False):
                    error_msg = result.get("message", "").lower()
                    if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
                        logger.warning("⚠️ Erreur quota CrewAI détectée → Fallback vers Agno")
                        self.quota_errors_count += 1
                        return self._execute_agno_fallback(rapport_md, output_path, md_file_path, company_name)
                
                if result.get("success", False):
                    self.stats["crewai_success"] += 1
                else:
                    self.stats["crewai_failures"] += 1
                
                # Enrichir avec recommandation si disponible
                if recommendation:
                    result["recommendation"] = recommendation.dict()
                
                return result
                
            else:  # AGNO
                result = self._execute_agno(rapport_md, output_path, md_file_path, company_name)
                
                if result.get("success", False):
                    self.stats["agno_success"] += 1
                else:
                    self.stats["agno_failures"] += 1
                
                # Enrichir avec recommandation si disponible
                if recommendation:
                    result["recommendation"] = recommendation.dict()
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur dans {engine.value}: {e}")
            
            # Fallback automatique si CrewAI échoue
            if engine == AnalysisEngine.CREWAI:
                logger.info("🔄 Fallback automatique CrewAI → Agno")
                return self._execute_agno_fallback(rapport_md, output_path, md_file_path, company_name)
            
            return {
                "success": False,
                "message": f"Erreur {engine.value}: {str(e)}",
                "engine_used": engine.value,
                "recommendation": recommendation.dict() if recommendation else None
            }
    
    def _execute_crewai(self, rapport_md: str, output_path: Path, md_file_path: Path, company_name: str) -> Dict[str, Any]:
        """Exécute l'analyse avec CrewAI"""
        try:
            from .agents import analyser_rapport
            
            logger.info("🔧 Exécution CrewAI...")
            rapport_final = analyser_rapport(rapport_md, output_path, md_file_path)
            
            return {
                "success": True,
                "message": "Analyse CrewAI terminée avec succès",
                "engine_used": "crewai",
                "engine_reason": "Moteur rapide et simple pour documents standards",
                "rapport": rapport_final
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur CrewAI: {e}")
            return {
                "success": False,
                "message": f"Erreur CrewAI: {str(e)}",
                "engine_used": "crewai",
                "engine_reason": "Tentative avec CrewAI"
            }
    
    def _execute_agno(self, rapport_md: str, output_path: Path, md_file_path: Path, company_name: str) -> Dict[str, Any]:
        """Exécute l'analyse avec Agno"""
        try:
            from .agents_agno import analyser_rapport_agno
            
            logger.info("🧠 Exécution Agno...")
            result = analyser_rapport_agno(rapport_md, output_path, md_file_path, company_name)
            
            result["engine_used"] = "agno"
            result["engine_reason"] = "Moteur robuste avec fallback intelligent pour documents complexes"
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur Agno: {e}")
            return {
                "success": False,
                "message": f"Erreur Agno: {str(e)}",
                "engine_used": "agno",
                "engine_reason": "Tentative avec Agno"
            }
    
    def _execute_agno_fallback(self, rapport_md: str, output_path: Path, md_file_path: Path, company_name: str) -> Dict[str, Any]:
        """Fallback vers Agno avec marquage spécial"""
        result = self._execute_agno(rapport_md, output_path, md_file_path, company_name)
        result["engine_used"] = "agno_fallback"
        result["fallback_reason"] = "crewai_quota_error"
        result["engine_reason"] = "Fallback automatique vers Agno suite à erreur CrewAI"
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation"""
        total_success = self.stats["crewai_success"] + self.stats["agno_success"]
        total_failures = self.stats["crewai_failures"] + self.stats["agno_failures"]
        total_attempts = total_success + total_failures
        
        return {
            **self.stats,
            "success_rate": (total_success / max(1, total_attempts)) * 100,
            "quota_errors": self.quota_errors_count,
            "preferred_engine": "agno" if self.quota_errors_count >= self.max_quota_errors else "auto"
        }
    
    def reset_quota_errors(self):
        """Remet à zéro le compteur d'erreurs quota (après résolution)"""
        self.quota_errors_count = 0
        logger.info("✅ Compteur d'erreurs quota remis à zéro")

# Instance globale du dispatcher
dispatcher = AnalysisDispatcher()

# Fonction d'interface pour le backend
def analyze_financial_document(
    rapport_md: str,
    output_path: Path = None,
    md_file_path: Path = None,
    company_name: str = "Entreprise Tunisienne",
    force_engine: str = None,
    user_preference: Optional[EnginePreference] = None
) -> Dict[str, Any]:
    """
    Interface principale pour l'analyse de documents financiers
    
    Args:
        rapport_md: Contenu Markdown du document
        output_path: Chemin de sortie
        md_file_path: Chemin source
        company_name: Nom de l'entreprise
        force_engine: "crewai" ou "agno" pour forcer un moteur (legacy)
        user_preference: Préférence utilisateur (mode auto/manual)
    
    Returns:
        Dict avec les résultats de l'analyse
    """
    
    # Convertir force_engine en user_preference si fourni (legacy support)
    if force_engine and not user_preference:
        try:
            user_preference = EnginePreference(
                mode="manual",
                selected_engine=force_engine.lower()
            )
        except ValueError:
            logger.warning(f"⚠️ Moteur inconnu '{force_engine}', utilisation automatique")
            user_preference = EnginePreference(mode="auto")
    
    return dispatcher.execute_analysis(
        rapport_md=rapport_md,
        output_path=output_path,
        md_file_path=md_file_path,
        company_name=company_name,
        user_preference=user_preference
    )

def get_engine_info() -> Dict[str, Any]:
    """
    Retourne les informations sur les moteurs disponibles
    
    Returns:
        Dict contenant les informations détaillées sur chaque moteur
    """
    return ENGINE_INFO

def get_engine_recommendation(
    rapport_md: str,
    md_file_path: Path = None
) -> EngineRecommendation:
    """
    Génère une recommandation de moteur pour un document donné
    
    Args:
        rapport_md: Contenu du document
        md_file_path: Chemin du fichier
    
    Returns:
        EngineRecommendation avec le moteur suggéré et la raison
    """
    return dispatcher._generate_recommendation(rapport_md, md_file_path)