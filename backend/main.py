import os
import sys
import asyncio
from pathlib import Path
from typing import List, Optional
import json
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from config import RAW_DIR, PROCESSED_DIR, REPORTS_DIR, TEMPLATES_DIR, BASE_DIR, DO_OCR, SAFE_MODE
from database import init_db, get_db, Document
from sqlalchemy.orm import Session
from fastapi import Depends

# Charger les variables d'environnement
load_dotenv(dotenv_path=BASE_DIR / "env")

# Initialisation de la base de données
init_db()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "backend.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Ajout du chemin src pour les imports
sys.path.append(str(BASE_DIR / "src" / "src"))

# Imports des modules existants
try:
    from scraper.agent import run_scraping_phase, download_all_pdfs, load_urls_file, load_progress
    from extractor.extract import PDFBatchProcessor
    from agents.agents import analyser_rapport
    from agents.dispatcher import (
        analyze_financial_document, 
        get_engine_info, 
        get_engine_recommendation,
        EnginePreference
    )
    
    # Vérification explicite que PDFBatchProcessor est bien importé
    if PDFBatchProcessor is None:
        raise ImportError("PDFBatchProcessor is None after import")
    logger.info("Tous les modules (Scraper, Extractor, Agents) sont importés avec succès.")
except ImportError as e:
    logger.error(f"Erreur d'importation : {e}")
    # Fallback pour le développement
    run_scraping_phase = None
    download_all_pdfs = None
    PDFBatchProcessor = None
    analyser_rapport = None
    analyze_financial_document = None
    get_engine_info = None
    get_engine_recommendation = None
    EnginePreference = None

app = FastAPI(title="CMF Tunisie Analysis API")

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Envoie un message à tous les clients connectés."""
        for connection in self.active_connections:
            try:
                # Utiliser send_json qui est l'API standard FastAPI/Starlette
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Erreur d'envoi WebSocket : {e}")
                # La déconnexion sera gérée par le bloc try/except de l'endpoint

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Maintenir la connexion ouverte
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ScrapeRequest(BaseModel):
    page_start: int = 0
    page_end: int = 2
    societe_filter: Optional[str] = None

class AnalysisResult(BaseModel):
    filename: str
    status: str
    report_path: Optional[str] = None

class ProcessRequest(BaseModel):
    """Requête de traitement avec préférences de moteur"""
    engine_mode: str = "auto"  # "auto" ou "manual"
    selected_engine: Optional[str] = None  # "crewai" ou "agno" si mode="manual"

# État global simple (à remplacer par une DB pour la prod)
processing_status = {
    "is_scraping": False,
    "last_scrape_result": None,
    "active_tasks": []
}

@app.get("/")
async def root():
    return {"message": "CMF Tunisie Analysis API is running"}

@app.get("/stats")
async def get_stats():
    raw_files = list(RAW_DIR.glob("*.pdf")) if RAW_DIR.exists() else []
    processed_files = list(PROCESSED_DIR.glob("*.md")) if PROCESSED_DIR.exists() else []
    report_files = list(REPORTS_DIR.glob("*.md")) if REPORTS_DIR.exists() else []
    
    return {
        "raw_pdfs": len(raw_files),
        "processed_mds": len(processed_files),
        "reports_generated": len(report_files),
        "is_scraping": processing_status["is_scraping"]
    }

@app.post("/scrape")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    if processing_status["is_scraping"]:
        raise HTTPException(status_code=400, detail="Scraping already in progress")
    
    def run_pipeline():
        processing_status["is_scraping"] = True
        asyncio.run(manager.broadcast({"type": "scrape_status", "status": "started"}))
        try:
            run_scraping_phase(request.page_start, request.page_end)
            download_all_pdfs(societe_filter=request.societe_filter)
            processing_status["last_scrape_result"] = "Success"
            asyncio.run(manager.broadcast({"type": "scrape_status", "status": "success"}))
        except Exception as e:
            processing_status["last_scrape_result"] = f"Error: {str(e)}"
            asyncio.run(manager.broadcast({"type": "scrape_status", "status": "error", "message": str(e)}))
        finally:
            processing_status["is_scraping"] = False

    background_tasks.add_task(run_pipeline)
    return {"message": "Scraping started in background"}

@app.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    # Sync filesystem with DB
    if RAW_DIR.exists():
        for f in RAW_DIR.glob("*.pdf"):
            doc = db.query(Document).filter(Document.filename == f.name).first()
            md_file = PROCESSED_DIR / f.name.replace(".pdf", ".md")
            report_file = REPORTS_DIR / f.name.replace(".pdf", "_rapport.md")
            
            if not doc:
                doc = Document(
                    filename=f.name,
                    size=f.stat().st_size,
                    last_modified=f.stat().st_mtime,
                    has_md=md_file.exists(),
                    has_report=report_file.exists(),
                    status="completed" if report_file.exists() else "pending"
                )
                db.add(doc)
            else:
                doc.has_md = md_file.exists()
                doc.has_report = report_file.exists()
                if doc.has_report and doc.status == "pending":
                    doc.status = "completed"
        db.commit()

    docs = db.query(Document).order_by(Document.last_modified.desc()).all()
    return docs

@app.post("/process/{filename}")
async def process_document(
    filename: str, 
    background_tasks: BackgroundTasks, 
    request: Optional[ProcessRequest] = None,
    db: Session = Depends(get_db)
):
    pdf_path = RAW_DIR / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    doc = db.query(Document).filter(Document.filename == filename).first()
    if doc:
        doc.status = "processing"
        db.commit()
    
    # Préparer les préférences utilisateur
    user_preference = None
    if request and EnginePreference:
        try:
            user_preference = EnginePreference(
                mode=request.engine_mode,
                selected_engine=request.selected_engine
            )
            logger.info(f"Préférence utilisateur: mode={request.engine_mode}, engine={request.selected_engine}")
        except Exception as e:
            logger.warning(f"Erreur parsing préférence: {e}, utilisation mode auto")
            user_preference = EnginePreference(mode="auto")

    def run_analysis():
        from database import SessionLocal
        db_session = SessionLocal()
        try:
            logger.info(f"Starting analysis for {filename}")
            doc = db_session.query(Document).filter(Document.filename == filename).first()
            
            # Notifier le début
            asyncio.run(manager.broadcast({"type": "status", "filename": filename, "status": "processing"}))
            
            # 1. Extraction Docling
            if PDFBatchProcessor is None:
                logger.error("PDFBatchProcessor not available")
                if doc: doc.status = "failed"; doc.error_message = "Processor unavailable"
                db_session.commit()
                return

            processor = PDFBatchProcessor(TEMPLATES_DIR)
            md_path = PROCESSED_DIR / filename.replace(".pdf", ".md")
            processor.execute_single(pdf_path, PROCESSED_DIR, do_ocr=DO_OCR, safe_mode=SAFE_MODE)
            
            # 2. Analyse IA avec dispatcher
            if md_path.exists():
                if doc: doc.has_md = True; db_session.commit()
                asyncio.run(manager.broadcast({"type": "status", "filename": filename, "status": "extracted"}))
                
                logger.info(f"MD extracted, starting IA analysis for {filename}")
                rapport_md = md_path.read_text(encoding="utf-8")
                report_out = REPORTS_DIR / filename.replace(".pdf", "_rapport.md")
                
                # Utiliser le dispatcher si disponible, sinon fallback sur analyser_rapport
                if analyze_financial_document:
                    result = analyze_financial_document(
                        rapport_md=rapport_md,
                        output_path=report_out,
                        md_file_path=md_path,
                        company_name=filename.replace(".pdf", ""),
                        user_preference=user_preference
                    )
                    
                    if result.get("success"):
                        if doc: 
                            doc.status = "completed"
                            doc.has_report = True
                            # Sauvegarder le moteur utilisé
                            doc.error_message = f"Engine: {result.get('engine_used', 'unknown')}"
                        logger.info(f"Analysis completed for {filename} with {result.get('engine_used')}")
                        asyncio.run(manager.broadcast({
                            "type": "status", 
                            "filename": filename, 
                            "status": "completed",
                            "engine_used": result.get("engine_used"),
                            "engine_reason": result.get("engine_reason")
                        }))
                    else:
                        logger.error(f"Analysis failed: {result.get('message')}")
                        if doc: doc.status = "failed"; doc.error_message = result.get("message")
                        asyncio.run(manager.broadcast({
                            "type": "status", 
                            "filename": filename, 
                            "status": "failed", 
                            "error": result.get("message")
                        }))
                        
                elif analyser_rapport:
                    # Fallback sur l'ancienne méthode
                    analyser_rapport(rapport_md, report_out, md_file_path=md_path)
                    if doc: 
                        doc.status = "completed"
                        doc.has_report = True
                    logger.info(f"Analysis completed for {filename}")
                    asyncio.run(manager.broadcast({"type": "status", "filename": filename, "status": "completed"}))
                else:
                    logger.error("analyser_rapport not available")
                    if doc: doc.status = "failed"; doc.error_message = "AI agent unavailable"
            else:
                logger.error(f"MD file not found after extraction for {filename}")
                if doc: doc.status = "failed"; doc.error_message = "Extraction failed"
            
            db_session.commit()
        except Exception as e:
            logger.exception(f"Error processing {filename}: {e}")
            doc = db_session.query(Document).filter(Document.filename == filename).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                db_session.commit()
            asyncio.run(manager.broadcast({"type": "status", "filename": filename, "status": "failed", "error": str(e)}))
        finally:
            db_session.close()

    background_tasks.add_task(run_analysis)
    return {"message": f"Processing started for {filename}", "engine_preference": request.dict() if request else {"mode": "auto"}}

@app.get("/report/{filename}")
async def get_report(filename: str):
    report_name = filename.replace(".pdf", "_rapport.md")
    report_path = REPORTS_DIR / report_name
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return {"content": report_path.read_text(encoding="utf-8")}

@app.get("/kpis/{filename}")
async def get_kpis(filename: str):
    kpi_name = filename.replace(".pdf", "_kpis.json")
    kpi_path = REPORTS_DIR / kpi_name
    if not kpi_path.exists():
        # Essayer sans extension si déjà fourni
        kpi_path = REPORTS_DIR / filename.replace(".md", "_kpis.json")
        if not kpi_path.exists():
            raise HTTPException(status_code=404, detail="KPIs not found")
    
    import json
    with open(kpi_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DIR / file.filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {"filename": file.filename, "status": "Uploaded"}

@app.get("/engines/info")
async def engines_info():
    """Retourne les informations détaillées sur les moteurs d'analyse disponibles"""
    if get_engine_info:
        return get_engine_info()
    else:
        return {
            "crewai": {
                "name": "CrewAI",
                "icon": "⚡",
                "description": "Rapide et simple",
                "best_for": ["Documents < 20 pages", "Analyse rapide"],
                "limitations": ["Pas de fallback quota automatique"]
            },
            "agno": {
                "name": "Agno Framework",
                "icon": "🧠",
                "description": "Robuste et intelligent",
                "best_for": ["Documents volumineux", "Fallback automatique"],
                "limitations": ["Setup plus complexe"]
            }
        }

@app.post("/engines/recommend")
async def recommend_engine(file: UploadFile = File(...)):
    """Génère une recommandation de moteur basée sur l'analyse du document"""
    try:
        # Lire le contenu du fichier
        content = await file.read()
        
        # Si c'est un PDF, on estime la taille
        if file.filename.endswith(".pdf"):
            # Estimation basique : 1 page ≈ 50KB
            estimated_pages = len(content) // 50000
            complexity = "high" if estimated_pages > 25 else "medium" if estimated_pages > 10 else "low"
            
            return {
                "engine": "agno" if estimated_pages > 20 else "crewai",
                "reason": f"Document estimé à {estimated_pages} pages",
                "confidence": 0.8,
                "document_analysis": {
                    "estimated_pages": estimated_pages,
                    "complexity": complexity,
                    "file_size": len(content)
                }
            }
        
        # Si c'est un MD, utiliser le dispatcher
        if file.filename.endswith(".md") and get_engine_recommendation:
            text_content = content.decode("utf-8")
            recommendation = get_engine_recommendation(text_content)
            return recommendation.dict()
        
        # Par défaut
        return {
            "engine": "auto",
            "reason": "Type de fichier non reconnu, utilisation du mode automatique",
            "confidence": 0.5
        }
        
    except Exception as e:
        logger.error(f"Erreur recommandation: {e}")
        return {
            "engine": "auto",
            "reason": f"Erreur d'analyse: {str(e)}",
            "confidence": 0.0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
