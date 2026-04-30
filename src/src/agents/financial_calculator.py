"""
financial_calculator.py — Calculateur financier précis pour les KPI SCE Tunisie
Outils de calcul fiables pour éviter les hallucinations numériques de l'IA
"""

import re
from typing import Dict, Optional, Tuple, List
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)

class FinancialCalculator:
    """Calculateur financier précis pour les KPI selon les normes SCE tunisiennes"""
    
    # Seuils de référence SCE Tunisie
    SEUILS_SCE = {
        "autonomie_financiere_min": 30.0,  # %
        "liquidite_generale_min": 1.0,     # ratio
        "liquidite_immediate_min": 0.2,    # ratio
        "endettement_max": 1.0,            # ratio
        "roe_bon": 15.0,                   # %
        "marge_exploitation_min": 5.0      # %
    }
    
    # Unités monétaires tunisiennes
    UNITES_MONETAIRES = {
        "DT": 1,
        "DINARS": 1,
        "MDT": 1000,
        "MILLIERS": 1000,
        "KDTE": 1000,
        "MILLIONS": 1000000
    }
    
    def __init__(self):
        self.precision = Decimal('0.01')  # 2 décimales
        
    def detect_monetary_unit(self, text: str) -> Tuple[str, int]:
        """
        Détecte l'unité monétaire dans le texte
        Returns: (unité_détectée, facteur_conversion)
        """
        text_upper = text.upper()
        
        # Recherche des patterns d'unités
        patterns = [
            (r'\bMILLIONS?\s+DE?\s+DINARS?\b', "MILLIONS", 1000000),
            (r'\bMILLIONS?\s+DT\b', "MILLIONS", 1000000),
            (r'\bMDT\b', "MDT", 1000),
            (r'\bKDTE\b', "KDTE", 1000),
            (r'\bMILLIERS?\s+DE?\s+DINARS?\b', "MILLIERS", 1000),
            (r'\bDINARS?\s+TUNISIENS?\b', "DINARS", 1),
            (r'\bDT\b', "DT", 1)
        ]
        
        for pattern, unit, factor in patterns:
            if re.search(pattern, text_upper):
                logger.info(f"Unité détectée: {unit} (facteur: {factor})")
                return unit, factor
                
        logger.warning("Unité monétaire non détectée, utilisation de DT par défaut")
        return "DT", 1
    
    def extract_number(self, text: str) -> Optional[Decimal]:
        """
        Extrait un nombre depuis un texte, gère les formats tunisiens
        Formats supportés: 1,234.56 | 1 234,56 | 1234.56 | (1,234.56)
        """
        if not text or text.strip() == "":
            return None
            
        # Nettoyer le texte
        clean_text = re.sub(r'[^\d\s,.\-()]+', '', text.strip())
        
        # Gérer les parenthèses (nombres négatifs)
        is_negative = bool(re.search(r'\([^)]*\d[^)]*\)', clean_text))
        clean_text = re.sub(r'[()]', '', clean_text)
        
        # Patterns de nombres
        patterns = [
            r'(\d{1,3}(?:\s\d{3})*),(\d{2})',  # Format français: 1 234,56
            r'(\d{1,3}(?:,\d{3})*).(\d{2})',   # Format anglais: 1,234.56
            r'(\d+),(\d{2})',                  # Simple avec virgule: 1234,56
            r'(\d+).(\d{2})',                  # Simple avec point: 1234.56
            r'(\d+)'                           # Entier simple: 1234
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_text)
            if match:
                if len(match.groups()) == 2:
                    # Nombre avec décimales
                    integer_part = re.sub(r'[\s,]', '', match.group(1))
                    decimal_part = match.group(2)
                    number_str = f"{integer_part}.{decimal_part}"
                else:
                    # Nombre entier
                    number_str = re.sub(r'[\s,]', '', match.group(1))
                
                try:
                    number = Decimal(number_str)
                    return -number if is_negative else number
                except:
                    continue
                    
        logger.warning(f"Impossible d'extraire un nombre de: {text}")
        return None
    
    def convert_to_dt(self, value: Decimal, unit_factor: int) -> Decimal:
        """Convertit une valeur vers les Dinars Tunisiens"""
        return value * Decimal(str(unit_factor))
    
    def calculate_percentage(self, numerator: Decimal, denominator: Decimal) -> Optional[Decimal]:
        """Calcule un pourcentage avec gestion des divisions par zéro"""
        if denominator == 0:
            logger.warning("Division par zéro dans le calcul de pourcentage")
            return None
        return (numerator / denominator * 100).quantize(self.precision, rounding=ROUND_HALF_UP)
    
    def calculate_ratio(self, numerator: Decimal, denominator: Decimal) -> Optional[Decimal]:
        """Calcule un ratio avec gestion des divisions par zéro"""
        if denominator == 0:
            logger.warning("Division par zéro dans le calcul de ratio")
            return None
        return (numerator / denominator).quantize(self.precision, rounding=ROUND_HALF_UP)
    
    def calculate_kpi_rentabilite(self, data: Dict[str, Decimal]) -> Dict[str, Optional[Decimal]]:
        """Calcule les KPI de rentabilité"""
        results = {}
        
        # KPI_R1: Marge d'Exploitation (%)
        if data.get('chiffre_affaires') and data.get('resultat_exploitation'):
            results['marge_exploitation'] = self.calculate_percentage(
                data['resultat_exploitation'], data['chiffre_affaires']
            )
        else:
            results['marge_exploitation'] = None
            
        # KPI_R2: Marge Nette (%)
        if data.get('chiffre_affaires') and data.get('resultat_net'):
            results['marge_nette'] = self.calculate_percentage(
                data['resultat_net'], data['chiffre_affaires']
            )
        else:
            results['marge_nette'] = None
            
        # KPI_R3: ROE (%)
        if data.get('resultat_net') and data.get('capitaux_propres'):
            results['roe'] = self.calculate_percentage(
                data['resultat_net'], data['capitaux_propres']
            )
        else:
            results['roe'] = None
            
        # KPI_R4: ROA (%)
        if data.get('resultat_net') and data.get('total_actif'):
            results['roa'] = self.calculate_percentage(
                data['resultat_net'], data['total_actif']
            )
        else:
            results['roa'] = None
            
        return results
    
    def calculate_kpi_structure(self, data: Dict[str, Decimal]) -> Dict[str, Optional[Decimal]]:
        """Calcule les KPI de structure financière"""
        results = {}
        
        # KPI_S1: Autonomie Financière (%)
        if data.get('capitaux_propres') and data.get('total_actif'):
            results['autonomie_financiere'] = self.calculate_percentage(
                data['capitaux_propres'], data['total_actif']
            )
        else:
            results['autonomie_financiere'] = None
            
        # KPI_S2: Ratio d'Endettement
        if data.get('capitaux_propres'):
            total_dettes = Decimal('0')
            for key in ['dettes_non_courantes', 'passifs_courants', 'tresorerie_passif']:
                if data.get(key):
                    total_dettes += data[key]
            
            if total_dettes > 0:
                results['ratio_endettement'] = self.calculate_ratio(
                    total_dettes, data['capitaux_propres']
                )
            else:
                results['ratio_endettement'] = None
        else:
            results['ratio_endettement'] = None
            
        # KPI_S4: FRNG (Fonds de Roulement Net Global)
        if (data.get('capitaux_propres') and data.get('dettes_non_courantes') 
            and data.get('actif_non_courant')):
            capitaux_permanents = data['capitaux_propres'] + data['dettes_non_courantes']
            results['frng'] = (capitaux_permanents - data['actif_non_courant']).quantize(self.precision)
        else:
            results['frng'] = None
            
        # KPI_S5: BFR (Besoin en Fonds de Roulement)
        if data.get('actifs_courants') and data.get('passifs_courants'):
            results['bfr'] = (data['actifs_courants'] - data['passifs_courants']).quantize(self.precision)
        else:
            results['bfr'] = None
            
        # KPI_S6: Trésorerie Nette
        if results.get('frng') is not None and results.get('bfr') is not None:
            results['tresorerie_nette'] = (results['frng'] - results['bfr']).quantize(self.precision)
        elif data.get('tresorerie_actif') and data.get('tresorerie_passif'):
            # Méthode alternative
            results['tresorerie_nette'] = (data['tresorerie_actif'] - data['tresorerie_passif']).quantize(self.precision)
        else:
            results['tresorerie_nette'] = None
            
        return results
    
    def calculate_kpi_liquidite(self, data: Dict[str, Decimal]) -> Dict[str, Optional[Decimal]]:
        """Calcule les KPI de liquidité"""
        results = {}
        
        # Calculer le total des dettes courantes
        dettes_courantes = Decimal('0')
        for key in ['passifs_courants', 'tresorerie_passif']:
            if data.get(key):
                dettes_courantes += data[key]
        
        # KPI_L1: Liquidité Générale
        if dettes_courantes > 0:
            actifs_liquides = Decimal('0')
            for key in ['actifs_courants', 'tresorerie_actif']:
                if data.get(key):
                    actifs_liquides += data[key]
            
            if actifs_liquides > 0:
                results['liquidite_generale'] = self.calculate_ratio(
                    actifs_liquides, dettes_courantes
                )
            else:
                results['liquidite_generale'] = None
        else:
            results['liquidite_generale'] = None
            
        # KPI_L2: Liquidité Immédiate
        if dettes_courantes > 0 and data.get('tresorerie_actif'):
            results['liquidite_immediate'] = self.calculate_ratio(
                data['tresorerie_actif'], dettes_courantes
            )
        else:
            results['liquidite_immediate'] = None
            
        return results
    
    def validate_kpi(self, kpi_name: str, value: Optional[Decimal]) -> Dict[str, any]:
        """Valide un KPI par rapport aux seuils SCE tunisiens"""
        if value is None:
            return {"status": "missing", "message": "Donnée manquante"}
            
        validation = {"value": float(value), "status": "ok", "message": "Conforme"}
        
        # Validation selon les seuils
        if kpi_name == "autonomie_financiere":
            if value < self.SEUILS_SCE["autonomie_financiere_min"]:
                validation.update({"status": "warning", "message": f"Inférieur au seuil recommandé ({self.SEUILS_SCE['autonomie_financiere_min']}%)"})
                
        elif kpi_name == "liquidite_generale":
            if value < self.SEUILS_SCE["liquidite_generale_min"]:
                validation.update({"status": "critical", "message": f"Risque de liquidité (< {self.SEUILS_SCE['liquidite_generale_min']})"})
                
        elif kpi_name == "ratio_endettement":
            if value > self.SEUILS_SCE["endettement_max"]:
                validation.update({"status": "warning", "message": f"Endettement élevé (> {self.SEUILS_SCE['endettement_max']})"})
                
        elif kpi_name == "roe":
            if value > self.SEUILS_SCE["roe_bon"]:
                validation.update({"status": "excellent", "message": f"Excellente rentabilité (> {self.SEUILS_SCE['roe_bon']}%)"})
                
        return validation
    
    def generate_calculation_report(self, extracted_data: Dict, calculated_kpis: Dict) -> str:
        """Génère un rapport détaillé des calculs effectués"""
        report = ["# Rapport de Calculs KPI - Détails Techniques\n"]
        
        # Données extraites
        report.append("## Données Extraites du Document\n")
        for key, value in extracted_data.items():
            if value is not None:
                report.append(f"- **{key.replace('_', ' ').title()}**: {value:,.2f} DT")
        
        # Calculs détaillés
        report.append("\n## Calculs Détaillés\n")
        
        # Rentabilité
        if calculated_kpis.get('marge_exploitation'):
            report.append(f"**Marge d'Exploitation** = (Résultat d'Exploitation / CA) × 100")
            report.append(f"= ({extracted_data.get('resultat_exploitation', 0):,.2f} / {extracted_data.get('chiffre_affaires', 1):,.2f}) × 100 = {calculated_kpis['marge_exploitation']:.2f}%\n")
        
        # Structure
        if calculated_kpis.get('frng'):
            report.append(f"**FRNG** = Capitaux Permanents - Actif Non Courant")
            cp = extracted_data.get('capitaux_propres', 0)
            dnc = extracted_data.get('dettes_non_courantes', 0)
            anc = extracted_data.get('actif_non_courant', 0)
            report.append(f"= ({cp:,.2f} + {dnc:,.2f}) - {anc:,.2f} = {calculated_kpis['frng']:,.2f} DT\n")
        
        return "\n".join(report)


# Fonction utilitaire pour l'intégration avec CrewAI
def create_financial_calculator_tool():
    """Crée un outil calculateur pour CrewAI"""
    calculator = FinancialCalculator()
    
    def calculate_kpis(extracted_values: str) -> str:
        """
        Outil de calcul KPI pour CrewAI
        Input: JSON string avec les valeurs extraites
        Output: JSON string avec les KPI calculés
        """
        import json
        
        try:
            # Parser les données d'entrée
            data_dict = json.loads(extracted_values)
            
            # Convertir en Decimal pour la précision
            decimal_data = {}
            for key, value in data_dict.items():
                if isinstance(value, (int, float, str)):
                    decimal_value = calculator.extract_number(str(value))
                    if decimal_value is not None:
                        decimal_data[key] = decimal_value
            
            # Calculer tous les KPI
            kpi_results = {}
            kpi_results.update(calculator.calculate_kpi_rentabilite(decimal_data))
            kpi_results.update(calculator.calculate_kpi_structure(decimal_data))
            kpi_results.update(calculator.calculate_kpi_liquidite(decimal_data))
            
            # Convertir en format JSON sérialisable
            json_results = {}
            for key, value in kpi_results.items():
                if value is not None:
                    json_results[key] = float(value)
                else:
                    json_results[key] = None
            
            return json.dumps(json_results, indent=2)
            
        except Exception as e:
            logger.error(f"Erreur dans le calcul KPI: {e}")
            return json.dumps({"error": str(e)})
    
    return calculate_kpis