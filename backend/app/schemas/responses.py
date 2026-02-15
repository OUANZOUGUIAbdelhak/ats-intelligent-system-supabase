"""
Response schemas for API endpoints.
"""

from typing import Any, Dict, List, Optional


def cv_document_response(
    id: str,
    raw_text: str,
    structured_data: Dict[str, Any],
    original_file_path: str,
    signed_url: Optional[str],
    status: str,
    quality_score: float,
    embedding: Optional[List[float]] = None,
    **extra,
) -> Dict[str, Any]:
    """Build standardized CV response with signed URL for original file."""
    result = {
        "id": id,
        "raw_text": raw_text,
        "structured_data": structured_data,
        "original_file_path": original_file_path,
        "signed_url": signed_url,
        "status": status,
        "quality_score": quality_score,
        "embedding_preview": {
            "dimension": len(embedding) if embedding else 0,
            "first_5": embedding[:5] if embedding and len(embedding) >= 5 else (embedding or []),
        },
        **extra,
    }
    return result
