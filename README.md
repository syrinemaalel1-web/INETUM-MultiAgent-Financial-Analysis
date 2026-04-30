# CMF Tunisie — KPIs Agent Platform

An end-to-end AI platform for automated extraction, processing, and financial analysis of CMF (Commission du Marché Financier) Tunisia reports. The system scrapes PDF financial statements, extracts structured data, computes SCE KPIs, and generates professional analysis reports — all through a real-time React dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Pipeline Stages](#pipeline-stages)
- [AI Engine System](#ai-engine-system)
- [RAG System (FAISS + BGE-M3)](#rag-system-faiss--bge-m3)
- [Financial KPIs](#financial-kpis)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Frontend Features](#frontend-features)
- [WebSocket Protocol](#websocket-protocol)
- [Memory & Large Document Handling](#memory--large-document-handling)
- [Engine Selection](#engine-selection)

---

## Overview

The platform automates the full financial analysis workflow for Tunisian listed companies:

```
CMF Website → PDF Scraper → Docling Extractor → AI Agents → KPI Report → React Dashboard
```

It handles documents ranging from small 5-page SICAV reports to large 67+ page Tunisair consolidated statements, with automatic memory management and intelligent engine selection.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  DocumentList │ EngineSelector │ ReportView │ WebSocketMonitor  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP + WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend (main.py)                     │
│  /documents │ /process/{file} │ /report │ /engines/info │ /ws   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Analysis Dispatcher                           │
│         Auto mode │ Manual CrewAI │ Manual Agno                 │
└──────────┬────────────────────────────────┬────────────────────┘
           │                                │
┌──────────▼──────────┐          ┌──────────▼──────────────────┐
│   CrewAI Engine     │          │      Agno Engine             │
│  agents.py          │          │  agents_agno.py              │
│  Gemini 2.5 Pro     │          │  Gemini 2.5 Pro + Flash      │
│  + Flash fallback   │          │  + RAG FAISS + BGE-M3        │
│  + MCP Calculator   │          │  + MCP Calculator            │
└─────────────────────┘          └──────────────────────────────┘
           │                                │
┌──────────▼────────────────────────────────▼────────────────────┐
│                    PDF Extractor (extract.py)                   │
│   Docling + PyPDF2 chunking (15 pages/chunk) + MemoryOptimizer  │
└─────────────────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                    CMF Scraper (agent.py)                       │
│              Selenium + BeautifulSoup + Rate limiting           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Stages

### Stage 1 — Scraping (`src/src/scraper/agent.py`)
- Scrapes the CMF Tunisia website for listed company financial reports
- Downloads PDF files to `data/data/raw/`
- Supports pagination, company filtering, and incremental downloads
- Rate-limited to avoid server overload

### Stage 2 — PDF Extraction (`src/src/extractor/extract.py`)
- Uses **Docling** for intelligent PDF-to-Markdown conversion
- Extracts sections, tables, and full text with semantic labeling
- **Automatic chunking** for documents > 15 pages (splits into 15-page chunks via PyPDF2, processes each, merges results)
- **Memory fallback chain**: Full extraction → No OCR → No tables → Minimal mode
- Outputs structured Markdown to `data/data/processed/`
- Jinja2 templates for consistent Markdown formatting

### Stage 3 — AI Analysis (CrewAI or Agno)
- Two specialized agents work sequentially:
  1. **Agent Calculateur** — extracts raw financial figures, computes 12 SCE KPIs
  2. **Agent Rapporteur** — generates professional analysis report in French
- Uses **MCP Financial Calculator** for precise Decimal arithmetic (no hallucinated numbers)
- Outputs reports to `data/data/rapports/`

---

## AI Engine System

### Dispatcher (`src/src/agents/dispatcher.py`)

The dispatcher automatically selects the best engine or respects user preference:

| Condition | Engine Selected | Reason |
|-----------|----------------|--------|
| Document < 20 pages + quota OK | CrewAI | Fast, simple |
| Document > 25 pages | Agno | Handles large docs |
| Quota errors ≥ 3 | Agno | Automatic fallback |
| User selects manually | User choice | Respected always |
| CrewAI quota error | Agno fallback | Auto-recovery |

### CrewAI Engine (`src/src/agents/agents.py`)
- **Agent Calculateur**: Gemini 2.5 Pro (heavy context extraction)
- **Agent Rapporteur**: Gemini 2.5 Flash (report generation)
- Sequential crew workflow
- Rate limiting: 15 RPM
- MCP tools for financial calculations

### Agno Engine (`src/src/agents/agents_agno.py`)
- **Agent Calculateur**: Gemini 2.5 Pro with fallback config
- **Agent Rapporteur**: Gemini 2.5 Flash with fallback config
- Fallback chain: Pro → Flash → Flash 1.5 on quota/error
- Exponential backoff retry (5 attempts for calculateur, 3 for rapporteur)
- **RAG FAISS** for large documents (see below)
- Structured output via Pydantic models (`FinancialKPIs`, `FinancialReport`)

---

## RAG System (FAISS + BGE-M3)

For documents exceeding 50,000 characters, the Agno engine activates a local RAG pipeline to avoid context window limits without losing any data.

### How it works

```
Large Document (e.g. Tunisair 266k chars)
         │
         ▼
  Split into chunks (3000 chars, 300 overlap)
  ~100 chunks for a 266k doc
         │
         ▼
  BGE-M3 local embeddings (1024d, 100+ languages)
  No API calls, no quota usage
         │
         ▼
  FAISS IndexFlatIP (cosine similarity)
         │
         ▼
  8 financial queries run against index:
  - "bilan actif passif total actif capitaux propres"
  - "résultat net résultat exploitation chiffre affaires"
  - "dettes long terme dettes courantes passif"
  - ... (8 queries total)
         │
         ▼
  Top-5 chunks per query retrieved → merged (deduped)
  ~40-60 relevant chunks sent to LLM
  Zero data loss — everything is indexed
```

### BGE-M3 Model
- **Model**: `BAAI/bge-m3`
- **Size**: ~570MB (downloaded once, cached locally)
- **Dimensions**: 1024
- **Languages**: 100+ including French and Arabic
- **Context**: Up to 8192 tokens per chunk
- **Fallback**: `gemini-embedding-exp-03-07` if sentence-transformers unavailable

### Why BGE-M3 over alternatives
| Model | Size | Languages | Dims | Best for |
|-------|------|-----------|------|----------|
| all-MiniLM-L6-v2 | 90MB | English | 384 | English only |
| paraphrase-multilingual-MiniLM-L12-v2 | 120MB | 50 | 384 | Light multilingual |
| **BAAI/bge-m3** | **570MB** | **100+** | **1024** | **Our choice — FR/AR financial docs** |
| multilingual-e5-large | 560MB | 100+ | 1024 | Similar quality |

---

## Financial KPIs

The system computes 12 SCE (Système Comptable des Entreprises) Tunisian KPIs:

### Rentabilité
| KPI | Formula |
|-----|---------|
| Marge d'Exploitation (KPI_R1) | (Résultat Exploitation / CA) × 100 |
| Marge Nette (KPI_R2) | (Résultat Net / CA) × 100 |
| ROE (KPI_R3) | (Résultat Net / Capitaux Propres) × 100 |
| ROA (KPI_R4) | (Résultat Net / Total Actif) × 100 |

### Structure Financière
| KPI | Formula |
|-----|---------|
| Autonomie Financière (KPI_S1) | (Capitaux Propres / Total Actif) × 100 |
| Ratio d'Endettement (KPI_S2) | Total Dettes / Capitaux Propres |
| FRNG (KPI_S4) | (Capitaux Propres + Dettes LT) - Actif Non Courant |
| BFR (KPI_S5) | Actifs Courants - Passifs Courants |
| Trésorerie Nette (KPI_S6) | FRNG - BFR |

### Liquidité
| KPI | Formula |
|-----|---------|
| Liquidité Générale (KPI_L1) | (Actifs Courants + Trésorerie) / Dettes Courantes |
| Liquidité Immédiate (KPI_L2) | Trésorerie / Dettes Courantes |

### SCE Tunisian Thresholds
- Autonomie financière saine: > 30%
- Liquidité générale correcte: > 1.0
- Endettement acceptable: < 1.0

---

## Project Structure

```
kpisagent/
├── backend/
│   ├── main.py              # FastAPI server — all endpoints + WebSocket
│   ├── config.py            # Paths, env vars, timeouts
│   └── database.py          # SQLAlchemy models (Document table)
│
├── src/src/
│   ├── agents/
│   │   ├── agents.py        # CrewAI engine (Gemini Pro + Flash)
│   │   ├── agents_agno.py   # Agno engine + RAG FAISS + BGE-M3
│   │   ├── dispatcher.py    # Engine selection logic
│   │   ├── financial_calculator.py  # MCP Decimal calculator
│   │   └── crewai_tools.py  # CrewAI tool wrappers
│   │
│   ├── extractor/
│   │   ├── extract.py       # Docling PDF→Markdown + chunking
│   │   ├── memory_optimizer.py  # std::bad_alloc handler
│   │   └── templates/
│   │       └── report.md.j2 # Jinja2 Markdown template
│   │
│   └── scraper/
│       └── agent.py         # CMF website scraper
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentList.jsx      # Document list + engine selector modal
│   │   │   ├── EngineSelector.jsx    # Auto/CrewAI/Agno selector UI
│   │   │   ├── EngineRecommendation.jsx  # Recommendation display
│   │   │   ├── ReportView.jsx        # Report viewer with engine badge
│   │   │   ├── ErrorDisplay.jsx      # Structured error UI
│   │   │   ├── ErrorBoundary.jsx     # React error boundary
│   │   │   ├── WebSocketMonitor.jsx  # Connection status indicator
│   │   │   └── NotificationToast.jsx # Toast notifications
│   │   ├── contexts/
│   │   │   └── WebSocketContext.jsx  # WS context + auto-reconnect
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js       # WS hook with exponential backoff
│   │   │   └── useEnginePreference.js # localStorage engine preference
│   │   ├── utils/
│   │   │   └── errorHandler.js       # Error classification utilities
│   │   └── config/
│   │       └── api.js                # Centralized API URLs from env vars
│   └── package.json
│
├── data/data/
│   ├── raw/                 # Downloaded PDFs from CMF
│   ├── processed/           # Extracted Markdown files
│   └── rapports/            # Generated analysis reports + KPI JSONs
│
├── env                      # Environment variables (not committed)
├── requirements.txt         # Core Python dependencies
├── requirements_agents.txt  # CrewAI + Gemini dependencies
└── requirements_agno.txt    # Agno + FAISS + BGE-M3 dependencies
```

---

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- ~2GB disk space (for BGE-M3 model cache on first run)

### 1. Clone
```bash
git clone https://github.com/slimgithub04/kpisagent.git
cd kpisagent
```

### 2. Python dependencies
```bash
# Core backend
pip install -r requirements.txt

# AI agents (CrewAI + Gemini)
pip install -r requirements_agents.txt

# Agno + FAISS + BGE-M3
pip install -r requirements_agno.txt
```

### 3. Frontend
```bash
cd frontend
npm install
```

---

## Configuration

### Backend — `env` file (root directory)
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# PDF Extraction
DO_OCR=false              # Keep false to save memory (auto-enables if text too short)
SAFE_MODE=false           # Set true to disable table extraction on low-RAM machines
DOCLING_MAX_PAGES=15      # Max pages per chunk
DOCLING_BATCH_SIZE=1      # Process one chunk at a time
DOCLING_LOW_MEMORY=true   # Aggressive memory optimization

# Server
API_HOST=0.0.0.0
API_PORT=8000
TIMEOUT_SECONDS=600
```

### Frontend — `frontend/.env`
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

For production:
```bash
VITE_API_URL=https://your-backend-domain.com
VITE_WS_URL=wss://your-backend-domain.com
```

---

## Running the Application

### Backend
```bash
# From project root (backend/ directory is the working dir)
python backend/main.py
```
API available at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm run dev
```
UI available at `http://localhost:5173`

> Note: On first Agno analysis of a large document, BGE-M3 (~570MB) will download and cache. Subsequent runs load from cache in ~3-5s.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/stats` | Processing statistics |
| GET | `/documents` | List all documents with status |
| POST | `/scrape` | Start CMF website scraping |
| POST | `/process/{filename}` | Process a PDF (with engine preference) |
| GET | `/report/{filename}` | Get generated analysis report |
| GET | `/kpis/{filename}` | Get extracted KPIs as JSON |
| POST | `/upload` | Upload a PDF file |
| GET | `/engines/info` | Get engine details and capabilities |
| POST | `/engines/recommend` | Get engine recommendation for a file |
| WS | `/ws` | WebSocket for real-time updates |

### Process endpoint body
```json
{
  "engine_mode": "auto",        // "auto" or "manual"
  "selected_engine": "agno"     // "crewai" or "agno" (only if mode="manual")
}
```

---

## Frontend Features

### Engine Selector
- Three modes: **Auto** (system decides), **CrewAI** (fast), **Agno** (robust)
- Tooltips explaining each engine's strengths
- Preference persisted in `localStorage`
- Recommendation badge shown when user overrides system suggestion

### Document List
- Real-time status updates via WebSocket
- Engine badge on completed documents (shows which engine was used)
- Upload button for manual PDF upload
- Scrape button to trigger CMF website scraping

### Report Viewer
- Full Markdown rendering of generated reports
- KPI table display
- Engine used indicator
- Download option

### Error Handling
- Distinguishes "no data" from "server unreachable"
- Retry buttons on failed operations
- Toast notifications for connection events
- React ErrorBoundary for unexpected crashes

---

## WebSocket Protocol

### Server → Client messages

```json
// Processing status update
{"type": "status", "filename": "doc.pdf", "status": "processing|extracted|completed|failed", "engine_used": "agno", "engine_reason": "..."}

// Scraping status
{"type": "scrape_status", "status": "started|success|error", "message": "..."}
```

### Connection behavior
- Auto-reconnect with exponential backoff (max 10 attempts)
- Visual indicator in sidebar (green/yellow/red)
- Toast notification on disconnect/reconnect

---

## Memory & Large Document Handling

### The problem
Large PDFs (Tunisair 67 pages, ~266k chars extracted) caused `std::bad_alloc` errors in Docling's C++ layout engine.

### Solution: PDF Chunking
Documents > 15 pages are automatically split into 15-page chunks using PyPDF2:
```
67-page Tunisair PDF → 5 chunks × 15 pages → processed sequentially → merged
```

### Memory fallback chain (per chunk)
```
Full extraction (OCR + tables)
    ↓ (if std::bad_alloc)
No OCR (text-only extraction)
    ↓ (if still fails)
No tables (minimal extraction)
    ↓ (if still fails)
Fallback Markdown with error info
```

### Environment tuning
```bash
DO_OCR=false              # Biggest memory saver
DOCLING_MAX_PAGES=15      # Chunk size
DOCLING_BATCH_SIZE=1      # One chunk at a time
DOCLING_LOW_MEMORY=true   # Disable page/table images
```

---

## Engine Selection

### When to use CrewAI
- Documents under 20 pages
- Quick analysis needed
- Standard financial reports (SICAV, small companies)

### When to use Agno
- Large documents (Tunisair, consolidated groups, 30+ pages)
- When Gemini quota is limited (auto-fallback to Flash)
- Production-critical analysis requiring retry logic
- Documents mixing French and Arabic content (BGE-M3 handles both)

### Auto mode behavior
The dispatcher analyzes document complexity (character count, estimated pages, keyword density) and selects the optimal engine automatically. CrewAI quota errors trigger automatic fallback to Agno.
