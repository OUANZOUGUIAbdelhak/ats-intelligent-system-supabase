"""
Pydantic models for CV documents.
Flexible structure - adapts to real CV content.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CVSection(BaseModel):
    """Flexible CV section - adapts to content."""
    section_type: str
    section_title: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    order: int = 0
    confidence: float = Field(default=0.0, ge=0, le=1)


class CVDocumentFull(BaseModel):
    """Full CV document - flexible structure for Postgres jsonb."""

    # Core identifiers
    id: Optional[str] = None
    version: int = 1

    # Source metadata
    source: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "upload",
            "original_filename": None,
            "upload_timestamp": None,
            "file_size_bytes": None,
            "mime_type": None,
            "storage_path": None,
        }
    )

    # Raw text (OCR output - preserve everything)
    raw_text: str = ""
    raw_ocr_output: Dict[str, Any] = Field(default_factory=dict)

    # Candidate info
    candidate_info: Dict[str, Any] = Field(
        default_factory=lambda: {
            "full_name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin_url": None,
            "summary": None,
        }
    )

    # Sections (flexible)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    experiences: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    languages: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)

    # Processing metadata
    processing: Dict[str, Any] = Field(
        default_factory=lambda: {
            "ocr_language": None,
            "ocr_confidence": None,
            "processed_at": None,
            "llm_structured": False,
            "llm_model": None,
            "status": "pending",
        }
    )

    quality_score: float = Field(default=0.0, ge=0, le=1)
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None

    status: str = "processing"
    gdpr_consent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
