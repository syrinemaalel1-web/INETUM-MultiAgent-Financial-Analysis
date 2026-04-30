#!/usr/bin/env python3
"""Test de syntaxe pour extract.py"""

import sys
import py_compile

try:
    py_compile.compile('src/src/extractor/extract.py', doraise=True)
    print("✅ Syntaxe correcte !")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"❌ Erreur de syntaxe :")
    print(e)
    sys.exit(1)
