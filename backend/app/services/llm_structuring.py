"""
LLM structuring service - uses Groq API for flexible CV transformation.
"""

import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def structure_cv_flexible(raw_text: str, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structure CV via Groq LLM - flexible JSON output.
    """
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set - using fallback parsing")
        return _fallback_parsing(raw_text)

    prompt = _build_prompt(raw_text)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.GROQ_API_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a CV analysis expert. Respond ONLY with valid JSON, no extra text.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            structured = _extract_json(content)
            return {
                "success": True,
                "data": structured,
                "model": settings.LLM_MODEL,
                "confidence": _calculate_confidence(structured),
            }
    except Exception as e:
        logger.error(f"Groq LLM error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "data": _fallback_parsing(raw_text)["data"],
        }


def _build_prompt(raw_text: str) -> str:
    """Build the structuring prompt."""
    return f"""You are a CV analysis expert. Extract and structure ALL information from this CV in a flexible way.

RULES:
1. DO NOT invent information - only what is in the text
2. Adapt to the real structure - no forced standard
3. Keep all information, even unusual
4. If a section does not exist, do not create it empty
5. Detect the real CV structure

CV TEXT:

{raw_text[:8000]}

TASK:
Extract and structure this CV as JSON:

1. **candidate_info**: full_name, email, phone, location, linkedin_url, summary
2. **sections**: All sections in order - each with section_type, section_title, content (flexible), order, confidence
   Types: experience, formation, compétences, projets, langues, certifications, etc.
3. **career_summary**: years_of_experience, seniority_level, primary_expertise

Respond ONLY with valid JSON, no markdown, no extra text.

FORMAT:
{{
  "candidate_info": {{ "full_name": "...", "email": "...", "phone": "...", "location": "...", "summary": "..." }},
  "sections": [
    {{
      "section_type": "experience",
      "section_title": "Experience",
      "order": 1,
      "content": {{
        "experiences": [
          {{ "job_title": "...", "company": "...", "start_date": "...", "end_date": "...", "description": "..." }}
        ]
      }},
      "confidence": 0.95
    }}
  ],
  "career_summary": {{ "years_of_experience": 5, "seniority_level": "senior", "primary_expertise": ["..."] }}
}}"""


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


def _calculate_confidence(data: Dict) -> float:
    """Compute confidence score."""
    scores = []
    if data.get("candidate_info", {}).get("full_name"):
        scores.append(1.0)
    else:
        scores.append(0.3)
    sections = len(data.get("sections", []))
    scores.append(min(sections / 5.0, 1.0))
    return sum(scores) / len(scores) if scores else 0.5


def _fallback_parsing(raw_text: str) -> Dict[str, Any]:
    """Basic parsing when LLM is unavailable."""
    return {
        "success": False,
        "data": {
            "candidate_info": {},
            "sections": [],
            "career_summary": {},
        },
        "error": "LLM not available",
    }
