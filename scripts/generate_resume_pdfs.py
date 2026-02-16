#!/usr/bin/env python3
"""Generate 10 sample resume PDFs for testing."""

import os
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
except ImportError:
    print("Install reportlab: pip install reportlab")
    raise

# Import resume contents
import sys
sys.path.insert(0, str(ROOT))
from samples.resume_contents import SAMPLE_RESUMES

OUTPUT_DIR = ROOT / "samples" / "resumes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_pdf(filename: str, content: str) -> Path:
    """Generate a PDF from resume text."""
    path = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
    )
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        spaceAfter=6,
    )
    story = []
    lines = content.strip().split("\n")
    for i, line in enumerate(lines):
        if not line.strip():
            story.append(Spacer(1, 6))
            continue
        # First line as title
        style = title_style if i == 0 else body_style
        story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;"), style))
    doc.build(story)
    return path


def main():
    print(f"Generating {len(SAMPLE_RESUMES)} resumes to {OUTPUT_DIR}")
    for r in SAMPLE_RESUMES:
        p = generate_pdf(r["filename"], r["content"])
        print(f"  Created: {p.name}")
    print("Done.")


if __name__ == "__main__":
    main()
