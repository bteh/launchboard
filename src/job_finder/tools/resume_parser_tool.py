"""Resume PDF parser tool for CrewAI agents."""

from __future__ import annotations

import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ResumeParserInput(BaseModel):
    """Input schema for resume parser tool."""

    file_path: str = Field(
        default="",
        description=(
            "Path to resume PDF file. If empty, searches the knowledge/ directory "
            "for the first PDF found."
        ),
    )


class ResumeParserTool(BaseTool):
    """
    Parses a PDF resume and extracts the full text content.
    Used by agents to understand the candidate's background,
    skills, and experience for matching and optimization.
    """

    name: str = "resume_parser"
    description: str = (
        "Reads and extracts text from a PDF resume file. "
        "Returns the full text content of the resume for analysis. "
        "If no file path is provided, it looks in the knowledge/ directory."
    )
    args_schema: Type[BaseModel] = ResumeParserInput

    def _run(self, file_path: str = "") -> str:
        """Parse the resume PDF and return text content."""
        # Check env var override first
        if not file_path:
            file_path = os.getenv("RESUME_PATH", "")

        # Find the resume file
        if not file_path:
            file_path = self._find_resume()

        if not file_path:
            return (
                "ERROR: No resume PDF found. Please place your resume PDF in the "
                "knowledge/ directory or provide a file path."
            )

        if not os.path.exists(file_path):
            return f"ERROR: Resume file not found at: {file_path}"

        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                return (
                    "WARNING: PDF was read but no text was extracted. "
                    "The PDF might be image-based. Consider using an OCR tool."
                )

            return f"=== RESUME CONTENT ===\n\n{full_text}\n\n=== END RESUME ==="

        except ImportError:
            return "ERROR: PyPDF2 not installed. Run: pip install PyPDF2"
        except Exception as e:
            return f"ERROR parsing resume: {str(e)}"

    @staticmethod
    def _find_resume() -> str | None:
        """Search for a resume PDF in the knowledge/ directory."""
        knowledge_dirs = [
            os.path.join(os.getcwd(), "knowledge"),
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "knowledge")
            ),
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "knowledge")
            ),
        ]

        for knowledge_dir in knowledge_dirs:
            if os.path.exists(knowledge_dir):
                pdfs = [
                    f
                    for f in os.listdir(knowledge_dir)
                    if f.lower().endswith(".pdf")
                ]
                if not pdfs:
                    continue
                # Prefer files with "resume" in the name
                resume_pdfs = [f for f in pdfs if "resume" in f.lower()]
                target = resume_pdfs[0] if resume_pdfs else pdfs[0]
                return os.path.join(knowledge_dir, target)
        return None
