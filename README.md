# ATS Intelligent System (Supabase)

A clean, production-ready Applicant Tracking System with OCR, LLM structuring, and semantic search — built on **Supabase** only (no Docker, Mongo, MinIO, ChromaDB, RabbitMQ, Redis).

## Features

- **Supabase Postgres + pgvector** — structured CV data + embeddings
- **Supabase Storage** — original PDF/image files, signed URLs for secure access
- **Docling OCR** — extract text from PDF, DOCX, images
- **Groq LLM** — flexible CV structuring (uses your Groq API key)
- **sentence-transformers** — 384-dim embeddings (all-MiniLM-L6-v2)
- **Semantic search** — pgvector cosine similarity
- **Demo page** — load 4 example CVs and see the pipeline in action

## Quick Start

### 1. Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run `supabase/migrations/001_initial.sql`
3. Copy **Project URL**, **anon key**, and **service_role key** from Project Settings → API

### 2. Environment

**Backend** (`backend/.env`):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
GROQ_API_KEY=your-groq-api-key
```

**Frontend** (`frontend/.env`):

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Run

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- Backend: http://localhost:8000  
- API docs: http://localhost:8000/docs  
- Frontend: http://localhost:5173  

### 4. Demo

1. Generate sample PDFs: `python scripts/generate_resume_pdfs.py`
2. Open http://localhost:5173
3. Go to **Demo** → click **Load Sample Resumes** (processes 10 PDFs)
4. Go to **Matching** → click an example job offer to find suitable resumes

## Sample Data

- **10 resume PDFs** in `samples/resumes/` (generate with `python scripts/generate_resume_pdfs.py`)
- **8 example job offers** in `samples/job_offers.json` (Senior Dev, Data Scientist, DevOps, Frontend, Backend, UX, Security, Junior Dev)

## Project Structure

```
ats-intelligent-system-supabase/
├── samples/
│   ├── resumes/           # 10 sample PDFs (generated)
│   ├── resume_contents.py # Content for PDF generation
│   └── job_offers.json    # Example job offers
├── scripts/
│   └── generate_resume_pdfs.py
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/           # config, Supabase client
│   │   ├── models/
│   │   ├── routers/        # cv, matching, scoring, demo
│   │   ├── services/       # ocr, llm, embedding, storage
│   │   └── schemas/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/          # Dashboard, CVList, CVViewer, Matching, Demo
│   │   ├── lib/            # supabase.ts, api.ts
│   │   └── ...
│   └── package.json
├── docs/
│   └── UPDATED_DOCUMENTATION.md
├── supabase/
│   └── migrations/
│       └── 001_initial.sql
└── README.md
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `POST /api/cv/ingest` | Upload CV (multipart), run full pipeline |
| `GET /api/cv/{id}` | Get CV with signed URL, raw text, structured data, embedding |
| `GET /api/cv/search` | List CVs (optional `?q=` for semantic search) |
| `POST /api/matching/semantic` | Semantic match by job description |
| `POST /api/scoring/candidates` | Score candidates |
| `GET /api/demo/load` | Load demo CVs |

## LLM & Embeddings

- **LLM**: Groq (Llama) — uses `GROQ_API_KEY`
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` (384 dim)

## Deployment

- **Backend**: Railway, Render — set env vars, run `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Frontend**: Vercel — set `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

See [docs/UPDATED_DOCUMENTATION.md](docs/UPDATED_DOCUMENTATION.md) for full documentation (storage, security, data display).
