"""
Matching router - semantic matching for job offers.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.core.supabase_client import get_supabase
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/api/matching", tags=["Matching"])
logger = logging.getLogger(__name__)


@router.post("/semantic")
async def semantic_matching(
    job_description: str,
    required_skills: Optional[List[str]] = None,
    top_n: int = 10,
):
    """
    Semantic matching: find CVs most similar to job description.
    Uses pgvector cosine similarity.
    """
    query_text = job_description
    if required_skills:
        query_text += " " + " ".join(required_skills or [])

    query_embedding = await generate_embedding(query_text)

    supabase = get_supabase()
    r = supabase.rpc(
        "match_cv_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.3,
            "match_count": top_n,
        },
    ).execute()

    if not hasattr(r, "data") or not r.data:
        return {"query": job_description, "results": [], "total": 0}

    ids = [row["id"] for row in r.data]
    rows = supabase.table("cv_documents").select("*").in_("id", ids).execute()

    # Preserve similarity order
    id_to_sim = {str(row["id"]): row["similarity"] for row in r.data}
    cv_list = rows.data or []
    cv_list.sort(key=lambda x: id_to_sim.get(str(x["id"]), 0), reverse=True)

    results = []
    for cv in cv_list:
        cv_id = str(cv["id"])
        results.append({
            "cv": cv,
            "similarity_score": id_to_sim.get(cv_id, 0),
        })

    return {"query": job_description, "results": results, "total": len(results)}
