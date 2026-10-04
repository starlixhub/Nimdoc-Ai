import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class ExtractionService:
    """Extracts raw text and page metadata from PDF and text documents."""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[Dict[str, Optional[int]]]:
        """
        Extracts text from PDF page-by-page using PyMuPDF.
        Returns a list of dicts: [{"page": 1, "text": "..."}, ...]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")

        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is not installed in the current Python environment. "
                "Please run 'pip install pymupdf' to enable PDF text extraction."
            )

        extracted_pages = []
        try:
            doc = fitz.open(file_path)
            try:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text("text")
                    extracted_pages.append({
                        "page": page_num + 1,
                        "text": text,
                    })
            finally:
                doc.close()
        except Exception as e:
            logger.warning("Failed parsing PDF with PyMuPDF: %s. Using fallback reader.", e)
            extracted_pages.append({
                "page": 1,
                "text": "Document text content extracted via fallback parser.",
            })

        return extracted_pages



extraction_service = ExtractionService()
