"""
OCR service using Docling.
Extracts text from PDF, DOCX, and images.
"""

import io
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

DOCLING_AVAILABLE = False
converter = None

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Docling not available, using fallback: {e}")


def _get_converter():
    """Lazy-load Docling converter."""
    global converter
    if converter is None and DOCLING_AVAILABLE:
        try:
            converter = DocumentConverter()
        except Exception as e:
            logger.error(f"Failed to init Docling: {e}")
    return converter


async def extract_text(
    file_content: bytes,
    filename: str,
    content_type: str,
) -> Dict[str, Any]:
    """
    Extract text from document using Docling (or fallback).
    """
    conv = _get_converter()
    if conv:
        return await _extract_with_docling(file_content, filename)
    return await _extract_fallback(file_content, content_type)


async def _extract_with_docling(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Extract using Docling."""
    conv = _get_converter()
    if not conv:
        return await _extract_fallback(file_content, "application/pdf")
    try:
        file_obj = io.BytesIO(file_content)
        result = conv.convert(source=file_obj, max_num_pages=100)

        raw_text = ""
        metadata = {"pages": 0, "tables": 0, "status": "unknown"}

        if hasattr(result, "legacy_document") and result.legacy_document:
            doc = result.legacy_document
            raw_text = doc.render_as_markdown() if hasattr(doc, "render_as_markdown") else ""
            metadata = {
                "pages": len(doc.pages) if hasattr(doc, "pages") else 0,
                "tables": len(doc.output.tables) if hasattr(doc, "output") and hasattr(doc.output, "tables") else 0,
                "status": str(result.status) if hasattr(result, "status") else "unknown",
            }
        else:
            raw_text = str(result) if result else ""

        return {
            "success": True,
            "raw_text": raw_text,
            "metadata": metadata,
            "confidence": 0.95,
            "method": "docling",
        }
    except Exception as e:
        logger.error(f"Docling extraction failed: {e}", exc_info=True)
        return await _extract_fallback(file_content, "application/pdf")


async def _extract_fallback(file_content: bytes, content_type: str) -> Dict[str, Any]:
    """Fallback extraction (PyPDF2 for PDF, etc.)."""
    if content_type == "application/pdf":
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            return {
                "success": True,
                "raw_text": text,
                "metadata": {},
                "confidence": 0.7,
                "method": "pypdf2_fallback",
            }
        except Exception as e:
            logger.error(f"PDF fallback failed: {e}")

    if content_type.startswith("image/"):
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(img)
            return {
                "success": True,
                "raw_text": text,
                "metadata": {},
                "confidence": 0.6,
                "method": "tesseract_fallback",
            }
        except Exception as e:
            logger.error(f"Image fallback failed: {e}")

    return {
        "success": False,
        "raw_text": "",
        "error": "No extraction method available",
        "confidence": 0.0,
        "method": "none",
    }
