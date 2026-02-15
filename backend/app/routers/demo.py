"""
Demo router - load demo data with example CVs.
"""

import base64
import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter

from app.core.supabase_client import get_supabase
from app.services.llm_structuring import structure_cv_flexible
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/api/demo", tags=["Demo"])
logger = logging.getLogger(__name__)

DEMO_USER_ID = "00000000-0000-0000-0000-000000000000"

# Example CV texts - diverse: clean, scanned-style, messy, multilingual
DEMO_CV_TEXTS = [
    # 1. Clean structured CV
    """John Doe
Senior Software Engineer
Email: john.doe@email.com | Phone: +1 555-123-4567 | Location: San Francisco, CA
LinkedIn: linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
5+ years of experience in full-stack development. Expertise in React, Node.js, and Python.
Led teams of 5+ developers. Strong problem-solving and communication skills.

EXPERIENCE
Senior Software Engineer | TechCorp Inc. | 2020 - Present
- Developed microservices using Python and FastAPI
- Led migration to Kubernetes
- Mentored 3 junior developers

Software Developer | StartUpXYZ | 2018 - 2020
- Built React frontend applications
- Implemented CI/CD with Jenkins

EDUCATION
B.S. Computer Science | MIT | 2018

SKILLS
Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS""",
    # 2. Scanned / image-style (slightly noisy)
    """Marie Dupont
   INGENIEURE LOGICIEL
   marie.dupont@mail.fr  |  Paris, France

   EXPERIENCE
   2021-2024  Ingenieure Senior  |  EntrepriseSoft
   Developpement applications Java Spring
   Gestion equipe de 4 personnes

   2018-2021  Developpeuse  |  TechStart
   Backend PHP et MySQL

   FORMATION
   Master Informatique  |  Universite Paris-Saclay  |  2018

   COMPETENCES
   Java, Spring, Python, SQL, Git, Agile""",
    # 3. Messy layout
    """Alex Smith — alex.smith@mail.com — NYC
    FULL STACK DEV
    skills: react node python sql
    work:
    - 2022-now: Dev at BigCo (react, api)
    - 2020-2022: Junior at SmallCo
    edu: CS degree 2020""",
    # 4. Multilingual (FR/EN mix)
    """Carlos García
    Desarrollador Full Stack | Full Stack Developer
    carlos@email.com | Madrid, Spain | Español, English (fluent)

    RÉSUMÉ | SUMMARY
    4 ans d'expérience en développement web. Experience with React, Vue, and Django.
    Passionné par l'architecture cloud. Passionate about cloud architecture.

    EXPÉRIENCE | EXPERIENCE
    Full Stack Developer | IberiaTech | 2021 - Present
    - Desarrollo de APIs REST con Django | REST API development with Django
    - Frontend con Vue.js y React

    EDUCATION | FORMACIÓN
    Ingeniería Informática | Universidad Complutense | 2020

    COMPETENCIAS | SKILLS
    Python, JavaScript, Vue, React, Django, PostgreSQL, AWS""",
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


@router.get("/load")
async def load_demo_data():
    """
    Load 4 demo CVs - processes each through OCR (simulated), LLM, embedding.
    Returns list of created CV IDs and pipeline steps.
    """
    supabase = get_supabase()
    steps: List[Dict[str, Any]] = []
    cv_ids: List[str] = []

    for i, raw_text in enumerate(DEMO_CV_TEXTS):
        cv_id = str(uuid.uuid4())
        step_log = {"cv_index": i + 1, "cv_id": cv_id, "steps": []}

        # Simulate OCR (we use text directly)
        step_log["steps"].append({"name": "OCR", "status": "completed", "note": "Text input"})
        ocr_result = {"raw_text": raw_text, "success": True, "confidence": 0.95}

        # LLM structuring
        llm_result = await structure_cv_flexible(raw_text, ocr_result)
        step_log["steps"].append({
            "name": "LLM",
            "status": "completed" if llm_result.get("success") else "partial",
            "note": llm_result.get("model", "groq"),
        })

        structured = _build_structured(llm_result)
        quality = _quality(structured)

        # Embedding
        embedding = await generate_embedding(raw_text)
        step_log["steps"].append({"name": "Embedding", "status": "completed", "dim": len(embedding)})

        # Demo: store path only (no actual file upload - signed URL will be null)
        # Real ingest flow uploads to storage.
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
        steps.append(step_log)

    return {
        "message": "Demo data loaded",
        "cv_ids": cv_ids,
        "steps": steps,
        "total": len(cv_ids),
    }


@router.get("/status")
async def demo_status():
    """Return count of demo CVs in DB."""
    supabase = get_supabase()
    r = supabase.table("cv_documents").select("id", count="exact").eq("source_type", "demo").execute()
    count = getattr(r, "count", None) or len(r.data or [])
    return {"demo_count": count, "total": count}
