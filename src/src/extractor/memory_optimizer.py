"""
memory_optimizer.py — Optimisations mémoire pour Docling
Gestion des documents volumineux avec chunking et fallback
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """Optimise l'utilisation mémoire pour le traitement de gros documents"""
    
    def __init__(self):
        # Limites de configuration
        self.max_pages_full = int(os.getenv("DOCLING_MAX_PAGES", "15"))
        self.batch_size = int(os.getenv("DOCLING_BATCH_SIZE", "1"))
        self.low_memory = os.getenv("DOCLING_LOW_MEMORY", "true").lower() == "true"
        
        logger.info(f"MemoryOptimizer initialisé:")
        logger.info(f"  - Max pages (mode complet): {self.max_pages_full}")
        logger.info(f"  - Batch size: {self.batch_size}")
        logger.info(f"  - Low memory mode: {self.low_memory}")
    
    def should_use_chunking(self, pdf_path: Path) -> bool:
        """Détermine si un document nécessite le chunking"""
        try:
            # Estimation basique : 1 page ≈ 50KB
            file_size = pdf_path.stat().st_size
            estimated_pages = file_size // 50000
            
            if estimated_pages > self.max_pages_full:
                logger.warning(f"Document {pdf_path.name} estimé à {estimated_pages} pages")
                logger.warning(f"Limite: {self.max_pages_full} pages → Chunking recommandé")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur estimation taille: {e}")
            return False
    
    def get_processing_strategy(self, pdf_path: Path) -> Dict[str, Any]:
        """Retourne la stratégie de traitement optimale"""
        
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        estimated_pages = pdf_path.stat().st_size // 50000
        
        if estimated_pages <= 10:
            return {
                "strategy": "full",
                "max_pages": None,
                "description": "Traitement complet (petit document)"
            }
        elif estimated_pages <= self.max_pages_full:
            return {
                "strategy": "full_optimized",
                "max_pages": self.max_pages_full,
                "description": f"Traitement complet optimisé (limite {self.max_pages_full} pages)"
            }
        elif estimated_pages <= 30:
            return {
                "strategy": "chunked",
                "max_pages": self.max_pages_full,
                "chunk_size": 10,
                "description": f"Traitement par chunks de 10 pages"
            }
        else:
            return {
                "strategy": "first_pages_only",
                "max_pages": self.max_pages_full,
                "description": f"Extraction des {self.max_pages_full} premières pages uniquement (document très volumineux)"
            }
    
    def handle_memory_error(self, pdf_path: Path, error: Exception) -> Dict[str, Any]:
        """Gère les erreurs de mémoire et propose une solution"""
        
        error_str = str(error).lower()
        
        if "bad_alloc" in error_str or "not enough memory" in error_str:
            logger.error(f"❌ Erreur mémoire détectée pour {pdf_path.name}")
            logger.error(f"   Erreur: {error}")
            
            strategy = self.get_processing_strategy(pdf_path)
            
            return {
                "error_type": "memory",
                "original_error": str(error),
                "recommendation": strategy,
                "message": f"Document trop volumineux. Recommandation: {strategy['description']}"
            }
        
        return {
            "error_type": "other",
            "original_error": str(error),
            "message": str(error)
        }
    
    def create_fallback_markdown(self, pdf_path: Path, error_info: Dict[str, Any]) -> str:
        """Crée un fichier Markdown de fallback avec informations d'erreur"""
        
        strategy = error_info.get("recommendation", {})
        
        markdown = f"""# Extraction Partielle - {pdf_path.stem}

## ⚠️ Avertissement

Ce document n'a pas pu être extrait complètement en raison de contraintes mémoire.

### Informations sur l'erreur
- **Type**: Erreur mémoire (std::bad_alloc)
- **Fichier**: {pdf_path.name}
- **Taille**: {pdf_path.stat().st_size / (1024 * 1024):.2f} MB
- **Pages estimées**: {pdf_path.stat().st_size // 50000}

### Recommandation
{strategy.get('description', 'Utiliser un système avec plus de mémoire ou traiter par chunks')}

### Solutions possibles

1. **Utiliser Agno Framework** (recommandé)
   - Chunking intelligent des documents
   - Traitement par sections
   - Fallback automatique

2. **Augmenter la mémoire disponible**
   - Fermer les applications non nécessaires
   - Augmenter la RAM du système

3. **Traiter manuellement**
   - Extraire les pages importantes uniquement
   - Diviser le PDF en plusieurs fichiers

### Données extraites
Aucune donnée n'a pu être extraite automatiquement.

---
*Extraction générée le {Path(__file__).stat().st_mtime}*
*Système: Memory Optimizer - CMF Tunisie*
"""
        
        return markdown

# Instance globale
memory_optimizer = MemoryOptimizer()
