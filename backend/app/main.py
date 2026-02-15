"""
ATS Intelligent System - FastAPI Backend
Supabase-native: Postgres (pgvector), Storage, RLS.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import cv, matching, scoring, demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ATS Intelligent System",
    description="Applicant Tracking System with OCR, LLM structuring, semantic search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router)
app.include_router(matching.router)
app.include_router(scoring.router)
app.include_router(demo.router)


@app.get("/")
def root():
    return {
        "service": "ATS Intelligent System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ats-backend"}


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
    )
