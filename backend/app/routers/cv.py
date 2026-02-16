"""
CV router - ingest, get, search, delete.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.supabase_client import get_supabase
from app.services.ocr_service import extract_text
from app.services.llm_structuring import structure_cv_flexible
from app.services.embedding_service import generate_embedding
from app.services.storage_service import upload_file, create_signed_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cv", tags=["CV"])


def _get_user_id() -> str:
    """Default user for demo - replace with JWT auth in production."""
    return "00000000-0000-0000-0000-000000000000"


def _build_structured_data(llm_result: dict) -> dict:
    """Convert LLM result to structured_data for storage."""
    data = llm_result.get("data", {}) or {}
    candidate_info = data.get("candidate_info", {}) or {}
    sections = data.get("sections", []) or []
    career = data.get("career_summary", {}) or {}

    experiences = []
    education = []
    skills = []

    for s in sections:
        if s.get("section_type") == "experience":
            experiences.extend(s.get("content", {}).get("experiences", []))
        elif s.get("section_type") in ("formation", "education"):
            education.extend(s.get("content", {}).get("education", []))
        elif s.get("section_type") in ("compétences", "skills"):
            skills.extend(s.get("content", {}).get("skills", []))

    return {
        "candidate_info": candidate_info,
        "sections": sections,
        "experiences": experiences,
        "education": education,
        "skills": skills,
        "career_summary": career,
    }


def _calculate_quality_score(structured: dict) -> float:
    """Simple quality score."""
    score = 0.0
    ci = structured.get("candidate_info", {}) or {}
    if ci.get("full_name"):
        score += 0.3
    if ci.get("email"):
        score += 0.2
    if structured.get("experiences"):
        score += 0.3
    if structured.get("skills"):
        score += 0.2
    return min(score, 1.0)


@router.post("/ingest")
async def ingest_cv(
    file: UploadFile = File(...),
    source: str = Form("upload"),
    gdpr_consent: bool = Form(False),
):
    """
    Ingest a CV: upload to storage, OCR, LLM structuring, embedding, save to DB.
    Full pipeline runs synchronously.
    """
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ct = file.content_type or "application/octet-stream"
    if ct not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported type: {ct}")

    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large (max {settings.MAX_FILE_SIZE_MB} MB)")

    user_id = _get_user_id()
    cv_id = str(uuid.uuid4())

    # 1. Upload to Supabase Storage
    storage_path = await upload_file(
        file_content=file_content,
        filename=file.filename,
        user_id=user_id,
        cv_id=cv_id,
    )

    # 2. OCR
    ocr_result = await extract_text(
        file_content=file_content,
        filename=file.filename,
        content_type=ct,
    )
    raw_text = ocr_result.get("raw_text", "") or ""

    # 3. LLM structuring
    llm_result = await structure_cv_flexible(raw_text, ocr_result)
    structured_data = _build_structured_data(llm_result)

    # 4. Embedding
    embedding = await generate_embedding(raw_text)

    # 5. Quality score
    quality_score = _calculate_quality_score(structured_data)

    # 6. Save to Supabase
    supabase = get_supabase()
    row = {
        "id": cv_id,
        "user_id": user_id,
        "original_file_path": storage_path,
        "raw_text": raw_text,
        "structured_data": structured_data,
        "embedding": embedding,
        "quality_score": quality_score,
        "status": "active",
        "source_type": source,
        "original_filename": file.filename,
        "mime_type": ct,
        "file_size_bytes": len(file_content),
        "gdpr_consent": gdpr_consent,
    }
    supabase.table("cv_documents").insert(row).execute()

    return JSONResponse(
        status_code=201,
        content={
            "cv_id": cv_id,
            "status": "active",
            "message": "CV ingested successfully",
        },
    )


@router.get("/search")
async def search_cvs(
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    """
    Search CVs - text query uses pgvector semantic search.
    Without q, returns paginated list.
    """
    supabase = get_supabase()
    user_id = _get_user_id()

    if q and q.strip():
        # Semantic search: get embedding for query, then vector search
        query_embedding = await generate_embedding(q.strip())
        r = supabase.rpc(
            "match_cv_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": limit,
            },
        ).execute()
        # Fallback if RPC not exists: simple filter
        if hasattr(r, "data") and r.data:
            ids = [x["id"] for x in r.data]
        else:
            ids = []
        if not ids:
            return {"results": [], "total": 0, "page": page, "limit": limit}

        r2 = supabase.table("cv_documents").select("*").in_("id", ids).eq("user_id", user_id).execute()
        return {
            "results": r2.data or [],
            "total": len(r2.data or []),
            "page": page,
            "limit": limit,
        }

    # List all
    start = (page - 1) * limit
    r = (
        supabase.table("cv_documents")
        .select("*", count="exact")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(start, start + limit - 1)
        .execute()
    )
    count = r.count if hasattr(r, "count") and r.count is not None else len(r.data or [])
    return {
        "results": r.data or [],
        "total": count,
        "page": page,
        "limit": limit,
    }


@router.get("/{cv_id}")
async def get_cv(cv_id: str):
    """
    Get CV by ID. Returns signed URL for original, raw_text, structured_data, embedding preview.
    """
    supabase = get_supabase()
    r = supabase.table("cv_documents").select("*").eq("id", cv_id).execute()

    if not r.data or len(r.data) == 0:
        raise HTTPException(404, "CV not found")

    row = r.data[0]
    signed_url = create_signed_url(
        row["original_file_path"],
        expires_in=settings.SIGNED_URL_EXPIRY,
    )

    return {
        "id": row["id"],
        "raw_text": row.get("raw_text", ""),
        "structured_data": row.get("structured_data", {}),
        "original_file_path": row["original_file_path"],
        "signed_url": signed_url,
        "status": row.get("status", "unknown"),
        "quality_score": row.get("quality_score", 0),
        "embedding_preview": {
            "dimension": len(row["embedding"]) if row.get("embedding") else 0,
            "first_5": (row["embedding"] or [])[:5],
        },
        "original_filename": row.get("original_filename"),
        "created_at": row.get("created_at"),
    }


@router.delete("/{cv_id}")
async def delete_cv(cv_id: str):
    """Delete CV and its storage file."""
    supabase = get_supabase()
    user_id = _get_user_id()

    r = supabase.table("cv_documents").select("original_file_path").eq("id", cv_id).eq("user_id", user_id).execute()
    if not r.data or len(r.data) == 0:
        raise HTTPException(404, "CV not found")

    path = r.data[0].get("original_file_path")
    if path:
        try:
            supabase.storage.from_("cv-originals").remove([path])
        except Exception as e:
            logger.warning(f"Storage delete failed: {e}")

    supabase.table("cv_documents").delete().eq("id", cv_id).eq("user_id", user_id).execute()
    return {"cv_id": cv_id, "status": "deleted"}
