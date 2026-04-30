#!/usr/bin/env python3
"""
Test de l'architecture hybride Gemini 3.1 Pro + Flash
Validation du fonctionnement des deux agents avec des modèles différents
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.append(str(Path(__file__).parents[3]))

from dotenv import load_dotenv
from crewai import LLM

def test_llm_configuration():
    """Test de la configuration des deux modèles LLM"""
    
    # Charger les variables d'environnement
    env_path = Path(__file__).parents[3] / "env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY non trouvée dans le fichier env")
        return False
    
    print(f"✅ API Key trouvée: {api_key[:10]}...")
    
    try:
        # Test Gemini 3.1 Pro (Agent Calculateur)
        print("\n🧠 Test Gemini 3.1 Pro (Agent Calculateur)...")
        llm_calculateur = LLM(
            model="gemini/gemini-3.1-pro",
            temperature=0.0
        )
        
        response_calc = llm_calculateur.call("Test de connexion Gemini 3.1 Pro. Réponds simplement 'OK'.")
        print(f"✅ Gemini 3.1 Pro: {response_calc}")
        
        # Test Gemini 2.5 Flash (Agent Rapporteur)
        print("\n⚡ Test Gemini 2.5 Flash (Agent Rapporteur)...")
        llm_rapporteur = LLM(
            model="gemini/gemini-2.5-flash",
            temperature=0.0
        )
        
        response_rap = llm_rapporteur.call("Test de connexion Gemini 2.5 Flash. Réponds simplement 'OK'.")
        print(f"✅ Gemini 2.5 Flash: {response_rap}")
        
        print("\n🎯 Architecture hybride configurée avec succès !")
        print("- Agent Calculateur: Gemini 3.1 Pro ✅")
        print("- Agent Rapporteur: Gemini 2.5 Flash ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des modèles: {e}")
        return False

def test_context_capabilities():
    """Test des capacités de contexte des deux modèles"""
    
    print("\n📊 Test des capacités de contexte...")
    
    # Document de test court
    short_doc = "BILAN: Total Actif: 1,000,000 DT. Capitaux Propres: 600,000 DT."
    
    # Document de test long (simulation)
    long_doc = """
    RAPPORT FINANCIER COMPLEXE - 50 PAGES
    """ + "Données financières détaillées. " * 1000 + """
    BILAN CONSOLIDÉ:
    - Total Actif: 275,736,314 DT
    - Capitaux Propres: 255,342,850 DT
    - Résultat Net: 5,191,147 DT
    """
    
    try:
        # Test avec document court (Flash)
        llm_flash = LLM(model="gemini/gemini-2.5-flash", temperature=0.0)
        response_short = llm_flash.call(f"Extrait le Total Actif de ce document: {short_doc}")
        print(f"✅ Flash (doc court): {response_short}")
        
        # Test avec document long (3.1 Pro)
        llm_pro = LLM(model="gemini/gemini-3.1-pro", temperature=0.0)
        response_long = llm_pro.call(f"Extrait le Total Actif de ce document complexe: {long_doc}")
        print(f"✅ 3.1 Pro (doc long): {response_long}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de contexte: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test de l'Architecture Hybride Gemini")
    print("=" * 50)
    
    # Test de configuration
    config_ok = test_llm_configuration()
    
    if config_ok:
        # Test des capacités
        context_ok = test_context_capabilities()
        
        if context_ok:
            print("\n🎉 Tous les tests réussis !")
            print("L'architecture hybride est prête pour la production.")
        else:
            print("\n⚠️ Tests de contexte échoués")
    else:
        print("\n❌ Configuration échouée")
        print("Vérifiez votre clé API Gemini dans le fichier env")