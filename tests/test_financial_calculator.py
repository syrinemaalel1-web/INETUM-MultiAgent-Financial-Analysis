"""
Tests unitaires pour le calculateur financier
"""

import unittest
from decimal import Decimal
import sys
from pathlib import Path

# Ajouter le chemin src pour les imports
sys.path.append(str(Path(__file__).parents[1] / "src" / "src"))

from agents.financial_calculator import FinancialCalculator

class TestFinancialCalculator(unittest.TestCase):
    
    def setUp(self):
        self.calculator = FinancialCalculator()
    
    def test_detect_monetary_unit(self):
        """Test de détection des unités monétaires"""
        # Test MDT
        unit, factor = self.calculator.detect_monetary_unit("Valeurs en MDT")
        self.assertEqual(unit, "MDT")
        self.assertEqual(factor, 1000)
        
        # Test DT
        unit, factor = self.calculator.detect_monetary_unit("Montant en DT")
        self.assertEqual(unit, "DT")
        self.assertEqual(factor, 1)
        
        # Test KDTE
        unit, factor = self.calculator.detect_monetary_unit("Exprimé en KDTE")
        self.assertEqual(unit, "KDTE")
        self.assertEqual(factor, 1000)
    
    def test_extract_number(self):
        """Test d'extraction de nombres"""
        # Format français
        result = self.calculator.extract_number("1 234,56")
        self.assertEqual(result, Decimal("1234.56"))
        
        # Format anglais
        result = self.calculator.extract_number("1,234.56")
        self.assertEqual(result, Decimal("1234.56"))
        
        # Nombre négatif avec parenthèses
        result = self.calculator.extract_number("(1,234.56)")
        self.assertEqual(result, Decimal("-1234.56"))
        
        # Nombre entier
        result = self.calculator.extract_number("1234")
        self.assertEqual(result, Decimal("1234"))
    
    def test_calculate_percentage(self):
        """Test de calcul de pourcentages"""
        result = self.calculator.calculate_percentage(Decimal("25"), Decimal("100"))
        self.assertEqual(result, Decimal("25.00"))
        
        # Division par zéro
        result = self.calculator.calculate_percentage(Decimal("25"), Decimal("0"))
        self.assertIsNone(result)
    
    def test_calculate_kpi_rentabilite(self):
        """Test de calcul des KPI de rentabilité"""
        data = {
            "chiffre_affaires": Decimal("1000000"),
            "resultat_exploitation": Decimal("150000"),
            "resultat_net": Decimal("100000"),
            "capitaux_propres": Decimal("500000"),
            "total_actif": Decimal("800000")
        }
        
        kpis = self.calculator.calculate_kpi_rentabilite(data)
        
        # Marge d'exploitation = 150000/1000000 * 100 = 15%
        self.assertEqual(kpis["marge_exploitation"], Decimal("15.00"))
        
        # ROE = 100000/500000 * 100 = 20%
        self.assertEqual(kpis["roe"], Decimal("20.00"))
        
        # ROA = 100000/800000 * 100 = 12.5%
        self.assertEqual(kpis["roa"], Decimal("12.50"))
    
    def test_calculate_kpi_structure(self):
        """Test de calcul des KPI de structure"""
        data = {
            "capitaux_propres": Decimal("500000"),
            "total_actif": Decimal("800000"),
            "dettes_non_courantes": Decimal("200000"),
            "actif_non_courant": Decimal("600000"),
            "actifs_courants": Decimal("200000"),
            "passifs_courants": Decimal("100000")
        }
        
        kpis = self.calculator.calculate_kpi_structure(data)
        
        # Autonomie financière = 500000/800000 * 100 = 62.5%
        self.assertEqual(kpis["autonomie_financiere"], Decimal("62.50"))
        
        # FRNG = (500000 + 200000) - 600000 = 100000
        self.assertEqual(kpis["frng"], Decimal("100000.00"))
        
        # BFR = 200000 - 100000 = 100000
        self.assertEqual(kpis["bfr"], Decimal("100000.00"))
    
    def test_validate_kpi(self):
        """Test de validation des KPI"""
        # Autonomie financière bonne (> 30%)
        validation = self.calculator.validate_kpi("autonomie_financiere", Decimal("45.0"))
        self.assertEqual(validation["status"], "ok")
        
        # Autonomie financière faible (< 30%)
        validation = self.calculator.validate_kpi("autonomie_financiere", Decimal("25.0"))
        self.assertEqual(validation["status"], "warning")
        
        # Liquidité critique (< 1.0)
        validation = self.calculator.validate_kpi("liquidite_generale", Decimal("0.8"))
        self.assertEqual(validation["status"], "critical")

if __name__ == "__main__":
    unittest.main()