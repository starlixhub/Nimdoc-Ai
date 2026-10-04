import os
from typing import Dict, List, Optional
import fitz  # PyMuPDF


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

        extracted_pages = []
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

        return extracted_pages


extraction_service = ExtractionService()
