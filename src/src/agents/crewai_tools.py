"""
crewai_tools.py — Outils CrewAI personnalisés pour l'analyse financière CMF Tunisie
Intégration du calculateur financier avec CrewAI pour des calculs précis
"""

from crewai.tools import tool
from typing import Dict, Any
import json
import logging
from decimal import Decimal
from .financial_calculator import FinancialCalculator

logger = logging.getLogger(__name__)

# Instance globale du calculateur
calculator = FinancialCalculator()

@tool("financial_calculator")
def financial_calculator_tool(extracted_data: str) -> str:
    """
    Outil de calcul financier précis pour les KPI SCE tunisiens.
    
    Args:
        extracted_data (str): JSON string contenant les valeurs extraites du document
        Format attendu: {
            "chiffre_affaires": "1234567.89",
            "resultat_exploitation": "123456.78",
            "resultat_net": "98765.43",
            "capitaux_propres": "2345678.90",
            "total_actif": "5432109.87",
            "actif_non_courant": "3456789.01",
            "actifs_courants": "1975320.86",
            "dettes_non_courantes": "1234567.89",
            "passifs_courants": "987654.32",
            "tresorerie_actif": "543210.98",
            "tresorerie_passif": "123456.78"
        }
    
    Returns:
        str: JSON string avec les KPI calculés et leur validation
    """
    try:
        # Parser les données d'entrée
        data_dict = json.loads(extracted_data)
        logger.info(f"Calcul KPI pour {len(data_dict)} valeurs extraites")
        
        # Convertir les valeurs en Decimal pour la précision
        decimal_data = {}
        conversion_log = []
        
        for key, value in data_dict.items():
            if value and str(value).strip():
                decimal_value = calculator.extract_number(str(value))
                if decimal_value is not None:
                    decimal_data[key] = decimal_value
                    conversion_log.append(f"{key}: {value} → {decimal_value}")
                else:
                    conversion_log.append(f"{key}: {value} → ERREUR_CONVERSION")
            else:
                conversion_log.append(f"{key}: VIDE")
        
        # Calculer tous les KPI
        kpi_results = {}
        
        # KPI de Rentabilité
        rentabilite = calculator.calculate_kpi_rentabilite(decimal_data)
        kpi_results.update(rentabilite)
        
        # KPI de Structure Financière
        structure = calculator.calculate_kpi_structure(decimal_data)
        kpi_results.update(structure)
        
        # KPI de Liquidité
        liquidite = calculator.calculate_kpi_liquidite(decimal_data)
        kpi_results.update(liquidite)
        
        # Validation des KPI
        validations = {}
        for kpi_name, kpi_value in kpi_results.items():
            validations[kpi_name] = calculator.validate_kpi(kpi_name, kpi_value)
        
        # Préparer le résultat final
        result = {
            "unit": "DT",
            "kpis": {},
            "validations": validations,
            "missing_data": [],
            "calculation_log": conversion_log,
            "summary": {
                "total_kpis": len(kpi_results),
                "calculated_kpis": len([k for k, v in kpi_results.items() if v is not None]),
                "missing_kpis": len([k for k, v in kpi_results.items() if v is None])
            }
        }
        
        # Convertir les KPI en format JSON sérialisable
        for key, value in kpi_results.items():
            if value is not None:
                result["kpis"][key] = float(value)
            else:
                result["kpis"][key] = None
                result["missing_data"].append(key)
        
        logger.info(f"Calcul terminé: {result['summary']['calculated_kpis']}/{result['summary']['total_kpis']} KPI calculés")
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        error_msg = f"Erreur de parsing JSON: {e}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg, "type": "json_error"})
        
    except Exception as e:
        error_msg = f"Erreur dans le calcul KPI: {e}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg, "type": "calculation_error"})

@tool("unit_converter")
def unit_converter_tool(value_with_unit: str) -> str:
    """
    Convertit une valeur avec son unité vers les Dinars Tunisiens (DT).
    
    Args:
        value_with_unit (str): Valeur avec unité, ex: "1,234 MDT" ou "567.89 KDTE"
    
    Returns:
        str: JSON avec la valeur convertie en DT
    """
    try:
        # Détecter l'unité
        unit, factor = calculator.detect_monetary_unit(value_with_unit)
        
        # Extraire la valeur numérique
        numeric_value = calculator.extract_number(value_with_unit)
        
        if numeric_value is None:
            return json.dumps({
                "error": "Impossible d'extraire la valeur numérique",
                "input": value_with_unit
            })
        
        # Convertir en DT
        dt_value = calculator.convert_to_dt(numeric_value, factor)
        
        result = {
            "original_value": float(numeric_value),
            "original_unit": unit,
            "conversion_factor": factor,
            "dt_value": float(dt_value),
            "formatted": f"{dt_value:,.2f} DT"
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Erreur de conversion: {e}",
            "input": value_with_unit
        })

@tool("kpi_validator")
def kpi_validator_tool(kpi_data: str) -> str:
    """
    Valide les KPI calculés selon les seuils SCE tunisiens.
    
    Args:
        kpi_data (str): JSON string avec les KPI à valider
    
    Returns:
        str: JSON avec les validations et recommandations
    """
    try:
        kpis = json.loads(kpi_data)
        validations = {}
        recommendations = []
        alerts = []
        
        for kpi_name, kpi_value in kpis.items():
            if kpi_value is not None:
                validation = calculator.validate_kpi(kpi_name, Decimal(str(kpi_value)))
                validations[kpi_name] = validation
                
                # Générer des recommandations
                if validation["status"] == "critical":
                    alerts.append(f"🚨 {kpi_name}: {validation['message']}")
                elif validation["status"] == "warning":
                    recommendations.append(f"⚠️ {kpi_name}: {validation['message']}")
                elif validation["status"] == "excellent":
                    recommendations.append(f"✅ {kpi_name}: {validation['message']}")
        
        result = {
            "validations": validations,
            "recommendations": recommendations,
            "alerts": alerts,
            "overall_health": "good" if len(alerts) == 0 else "warning" if len(alerts) < 3 else "critical"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Erreur de validation: {e}",
            "input": kpi_data
        })

@tool("financial_ratio_calculator")
def financial_ratio_calculator_tool(numerator: str, denominator: str, ratio_type: str = "percentage") -> str:
    """
    Calcule un ratio financier précis.
    
    Args:
        numerator (str): Numérateur
        denominator (str): Dénominateur  
        ratio_type (str): "percentage" ou "ratio"
    
    Returns:
        str: JSON avec le résultat du calcul
    """
    try:
        num_value = calculator.extract_number(numerator)
        den_value = calculator.extract_number(denominator)
        
        if num_value is None or den_value is None:
            return json.dumps({
                "error": "Valeurs numériques invalides",
                "numerator": numerator,
                "denominator": denominator
            })
        
        if ratio_type == "percentage":
            result_value = calculator.calculate_percentage(num_value, den_value)
            unit = "%"
        else:
            result_value = calculator.calculate_ratio(num_value, den_value)
            unit = "ratio"
        
        if result_value is None:
            return json.dumps({
                "error": "Division par zéro",
                "numerator": float(num_value),
                "denominator": float(den_value)
            })
        
        result = {
            "numerator": float(num_value),
            "denominator": float(den_value),
            "result": float(result_value),
            "unit": unit,
            "calculation": f"({float(num_value)} / {float(den_value)})" + (" × 100" if ratio_type == "percentage" else ""),
            "formatted": f"{result_value:.2f} {unit}"
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "error": f"Erreur de calcul: {e}",
            "numerator": numerator,
            "denominator": denominator
        })

# Liste des outils disponibles pour CrewAI
FINANCIAL_TOOLS = [
    financial_calculator_tool,
    unit_converter_tool,
    kpi_validator_tool,
    financial_ratio_calculator_tool
]