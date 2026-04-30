import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Data Directories — aligned with scraper (agent.py uses relative 'data/raw' from backend/)
DATA_DIR = BACKEND_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "rapports"

# Ensure directories exist
for d in [RAW_DIR, PROCESSED_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Source Directories
SRC_DIR = BASE_DIR / "src" / "src"
EXTRACTOR_DIR = SRC_DIR / "extractor"
TEMPLATES_DIR = EXTRACTOR_DIR / "templates"

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Extraction Configuration
TIMEOUT_SECONDS = 600  # 10 minutes pour les documents complexes
DO_OCR = os.getenv("DO_OCR", "false").lower() == "true"
SAFE_MODE = os.getenv("SAFE_MODE", "false").lower() == "true" # Désactive les tableaux si True
OCR_RETRY_THRESHOLD = 500  # Characters threshold to trigger OCR retry
