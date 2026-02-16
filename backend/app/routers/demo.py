"""
Demo router - load sample PDFs, job offers.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.core.supabase_client import get_supabase
from app.services.ocr_service import extract_text
from app.services.llm_structuring import structure_cv_flexible
from app.services.embedding_service import generate_embedding
from app.services.storage_service import upload_file

router = APIRouter(prefix="/api/demo", tags=["Demo"])
logger = logging.getLogger(__name__)

DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"

# Project root (backend/app/routers/demo.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES_RESUMES_DIR = PROJECT_ROOT / "samples" / "resumes"
JOB_OFFERS_PATH = PROJECT_ROOT / "samples" / "job_offers.json"

# Fallback: 4 text-only CVs if PDFs not found (original demo)
DEMO_CV_TEXTS = [
    """John Doe
Senior Software Engineer
Email: john.doe@email.com | Phone: +1 555-123-4567 | Location: San Francisco, CA

PROFESSIONAL SUMMARY
5+ years of experience in full-stack development. Expertise in React, Node.js, and Python.

EXPERIENCE
Senior Software Engineer | TechCorp Inc. | 2020 - Present
- Developed microservices using Python and FastAPI
- Led migration to Kubernetes

SKILLS
Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS""",
    """Marie Dupont - Ingénieure Logiciel
marie.dupont@mail.fr | Paris, France

EXPÉRIENCE
2021-2024 Ingénieure Senior | EntrepriseSoft - Java Spring
2018-2021 Développeuse | TechStart - PHP, MySQL

COMPÉTENCES
Java, Spring, Python, SQL, Git, Agile""",
    """Sarah Chen, PhD - Data Scientist
sarah.chen@data.co | New York, NY

Machine learning and statistical modeling. 6 years NLP and computer vision.
Lead Data Scientist at DataCorp. Python, TensorFlow, PyTorch.""",
    """Michael Johnson - DevOps Engineer
michael.j@tech.io | Austin, TX

8 years infrastructure, CI/CD, cloud. AWS certified.
Kubernetes, Terraform, Docker, Jenkins.""",
]


def _build_structured(llm_result: dict) -> dict:
    data = llm_result.get("data", {}) or {}
    exp, edu, skills = [], [], []
    for s in data.get("sections", []):
        t = s.get("section_type", "")
        c = s.get("content", {}) or {}
        if t == "experience":
            exp.extend(c.get("experiences", []))
        elif t in ("formation", "education"):
            edu.extend(c.get("education", []))
        elif t in ("compétences", "skills"):
            skills.extend(c.get("skills", []))
    return {
        "candidate_info": data.get("candidate_info", {}) or {},
        "sections": data.get("sections", []) or [],
        "experiences": exp,
        "education": edu,
        "skills": skills,
        "career_summary": data.get("career_summary", {}) or {},
    }


def _quality(structured: dict) -> float:
    s = 0.0
    ci = structured.get("candidate_info", {}) or {}
    if ci.get("full_name"):
        s += 0.3
    if ci.get("email"):
        s += 0.2
    if structured.get("experiences"):
        s += 0.3
    if structured.get("skills"):
        s += 0.2
    return min(s, 1.0)


def _get_sample_pdf_paths() -> List[Path]:
    """Get list of sample PDF paths. Returns empty if dir missing."""
    if not SAMPLES_RESUMES_DIR.exists():
        return []
    return sorted(SAMPLES_RESUMES_DIR.glob("*.pdf"))


async def _process_one_cv(
    file_content: bytes,
    filename: str,
    supabase,
    source: str = "sample",
) -> Dict[str, Any]:
    """Run full pipeline on one CV. Returns cv_id and step_log."""
    from app.routers.cv import _build_structured_data, _calculate_quality_score

    cv_id = str(uuid.uuid4())
    step_log = {"filename": filename, "cv_id": cv_id, "steps": []}

    # 1. Upload to storage
    try:
        storage_path = await upload_file(
            file_content=file_content,
            filename=filename,
            user_id=DEMO_USER_ID,
            cv_id=cv_id,
        )
        step_log["steps"].append({"name": "Storage", "status": "completed"})
    except Exception as e:
        logger.warning(f"Storage upload failed for {filename}: {e}")
        storage_path = f"{DEMO_USER_ID}/{cv_id}/{filename}"
        step_log["steps"].append({"name": "Storage", "status": "skipped", "note": str(e)})

    # 2. OCR
    ocr_result = await extract_text(
        file_content=file_content,
        filename=filename,
        content_type="application/pdf",
    )
    raw_text = ocr_result.get("raw_text", "") or ""
    step_log["steps"].append({"name": "OCR", "status": "completed"})

    # 3. LLM
    llm_result = await structure_cv_flexible(raw_text, ocr_result)
    structured_data = _build_structured_data(llm_result)
    step_log["steps"].append({
        "name": "LLM",
        "status": "completed" if llm_result.get("success") else "partial",
    })

    # 4. Embedding
    embedding = await generate_embedding(raw_text)
    step_log["steps"].append({"name": "Embedding", "status": "completed", "dim": len(embedding)})

    # 5. Quality
    quality_score = _calculate_quality_score(structured_data)

    # 6. Save to DB
    row = {
        "id": cv_id,
        "user_id": DEMO_USER_ID,
        "original_file_path": storage_path,
        "raw_text": raw_text,
        "structured_data": structured_data,
        "embedding": embedding,
        "quality_score": quality_score,
        "status": "active",
        "source_type": source,
        "original_filename": filename,
        "mime_type": "application/pdf",
        "file_size_bytes": len(file_content),
        "gdpr_consent": True,
    }
    supabase.table("cv_documents").insert(row).execute()

    return {"cv_id": cv_id, "step_log": step_log}


@router.get("/load")
async def load_demo_data(use_pdfs: bool = True):
    """
    Load sample data.
    - use_pdfs=true: Process 10 sample PDFs from samples/resumes/ (full pipeline)
    - use_pdfs=false: Process 4 text CVs (original demo, no PDFs)
    """
    supabase = get_supabase()
    steps: List[Dict[str, Any]] = []
    cv_ids: List[str] = []

    if use_pdfs:
        pdf_paths = _get_sample_pdf_paths()
        if not pdf_paths:
            logger.warning("No sample PDFs found, falling back to text demos")
            use_pdfs = False

    if use_pdfs:
        pdf_paths = _get_sample_pdf_paths()
        for i, path in enumerate(pdf_paths):
            try:
                file_content = path.read_bytes()
                result = await _process_one_cv(
                    file_content=file_content,
                    filename=path.name,
                    supabase=supabase,
                    source="sample",
                )
                cv_ids.append(result["cv_id"])
                steps.append(result["step_log"])
            except Exception as e:
                logger.error(f"Failed to process {path.name}: {e}")
                steps.append({
                    "filename": path.name,
                    "error": str(e),
                    "steps": [{"name": "error", "status": "failed"}],
                })
    else:
        # Text-only fallback (original 4 CVs)
        for i, raw_text in enumerate(DEMO_CV_TEXTS):
            cv_id = str(uuid.uuid4())
            step_log = {"cv_index": i + 1, "cv_id": cv_id, "steps": []}

            ocr_result = {"raw_text": raw_text, "success": True}
            llm_result = await structure_cv_flexible(raw_text, ocr_result)
            structured = _build_structured(llm_result)
            quality = _quality(structured)
            embedding = await generate_embedding(raw_text)

            filename = f"demo_cv_{i + 1}.pdf"
            storage_path = f"{DEMO_USER_ID}/{cv_id}/{filename}"

            row = {
                "id": cv_id,
                "user_id": DEMO_USER_ID,
                "original_file_path": storage_path,
                "raw_text": raw_text,
                "structured_data": structured,
                "embedding": embedding,
                "quality_score": quality,
                "status": "active",
                "source_type": "demo",
                "original_filename": filename,
                "mime_type": "application/pdf",
                "file_size_bytes": len(raw_text.encode()),
                "gdpr_consent": True,
            }
            supabase.table("cv_documents").insert(row).execute()
            cv_ids.append(cv_id)
            step_log["steps"] = [
                {"name": "OCR", "status": "completed"},
                {"name": "LLM", "status": "completed"},
                {"name": "Embedding", "status": "completed", "dim": len(embedding)},
            ]
            steps.append(step_log)

    return {
        "message": f"Loaded {len(cv_ids)} CVs",
        "cv_ids": cv_ids,
        "steps": steps,
        "total": len(cv_ids),
    }


@router.get("/job-offers")
async def get_job_offers():
    """Return example job offers for matching."""
    if not JOB_OFFERS_PATH.exists():
        return {"job_offers": []}
    try:
        data = json.loads(JOB_OFFERS_PATH.read_text(encoding="utf-8"))
        return {"job_offers": data}
    except Exception as e:
        logger.error(f"Failed to load job offers: {e}")
        return {"job_offers": []}


@router.get("/status")
async def demo_status():
    """Return count of demo/sample CVs in DB."""
    supabase = get_supabase()
    r = (
        supabase.table("cv_documents")
        .select("id", count="exact")
        .in_("source_type", ["demo", "sample"])
        .execute()
    )
    count = getattr(r, "count", None) or len(r.data or [])
    return {"demo_count": count, "total": count}
