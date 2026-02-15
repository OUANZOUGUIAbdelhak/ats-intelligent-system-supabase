"""
Scoring router - multi-criteria candidate scoring.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/api/scoring", tags=["Scoring"])
logger = logging.getLogger(__name__)


@router.post("/candidates")
async def score_candidates(
    cv_ids: List[str],
    job_id: Optional[str] = None,
    criteria: Optional[dict] = None,
):
    """
    Score candidates by multi-criteria (skills match, experience, etc.).
    """
    if not cv_ids:
        return {"results": [], "total": 0}

    weights = criteria or {
        "skills": 0.4,
        "experience": 0.3,
        "education": 0.2,
        "quality": 0.1,
    }

    supabase = get_supabase()
    rows = supabase.table("cv_documents").select("*").in_("id", cv_ids).execute()
    cvs = rows.data or []

    results = []
    for cv in cvs:
        structured = cv.get("structured_data", {}) or {}
        skills_score = min(len(structured.get("skills", [])) / 10.0, 1.0) * weights["skills"]
        exp_score = min(len(structured.get("experiences", [])) / 5.0, 1.0) * weights["experience"]
        edu_score = min(len(structured.get("education", [])) / 3.0, 1.0) * weights["education"]
        quality_score = (cv.get("quality_score") or 0) * weights["quality"]

        total = skills_score + exp_score + edu_score + quality_score
        results.append({
            "cv_id": str(cv["id"]),
            "cv": cv,
            "score": round(min(total, 1.0), 2),
            "breakdown": {
                "skills": round(skills_score, 2),
                "experience": round(exp_score, 2),
                "education": round(edu_score, 2),
                "quality": round(quality_score, 2),
            },
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results, "total": len(results)}
