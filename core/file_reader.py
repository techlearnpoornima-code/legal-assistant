"""
Universal File Reader
Supports: PDF, TXT, Word, Excel, Images (OCR)
"""

import re
from pathlib import Path
from typing import Optional
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path

class FileReader:
    """Extract text from multiple document formats."""

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".docx",
        ".xlsx",
        ".xls",
        ".png",
        ".jpg",
        ".jpeg"
    }

    def read(self, file_path: Path) -> Optional[str]:
        suffix = file_path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            print(f"[FileReader] Unsupported file type: {suffix}")
            return None

        try:
            if suffix == ".pdf":
                return self._read_pdf(file_path)

            elif suffix == ".txt":
                return self._read_txt(file_path)

            elif suffix == ".docx":
                return self._read_docx(file_path)

            elif suffix in {".xlsx", ".xls"}:
                return self._read_excel(file_path)

            elif suffix in {".png", ".jpg", ".jpeg"}:
                return self._read_image(file_path)

        except Exception as e:
            print(f"[FileReader] Error reading {file_path.name}: {e}")
            return ""


    def _read_pdf_with_ocr(self, file_path: Path) -> str:
        """
        Extract text from scanned/image-based PDFs using OCR.
        """

        text = ""

        try:
            # Convert PDF pages to images
            images = convert_from_path(
                str(file_path),
                dpi=300,              # Higher DPI = better OCR accuracy
                fmt="png",
                thread_count=2        # Speed optimization
            )

            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)

                # Clean whitespace
                page_text = re.sub(r"\s+\n", "\n", page_text)
                page_text = re.sub(r"\n{2,}", "\n\n", page_text)

                if page_text.strip():
                    text += f"\n--- Page {i + 1} ---\n"
                    text += page_text.strip() + "\n"

        except Exception as e:
            print(f"[OCR Error] Failed to process {file_path}: {e}")

        return text.strip()


    # -------------------------
    # PDF READER
    # -------------------------
    def _read_pdf(self, file_path: Path) -> str:

        reader = PdfReader(str(file_path))
        text = ""

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n"
                text += page_text

        # Fallback to OCR if empty
        if not text.strip():
            print("[DocumentProcessor] No embedded text found. Using OCR...")
            text = self._read_pdf_with_ocr(file_path)

        return text.strip()



    # -------------------------
    # TXT READER
    # -------------------------
    def _read_txt(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")

    # -------------------------
    # WORD READER (.docx)
    # -------------------------
    def _read_docx(self, file_path: Path) -> str:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    # -------------------------
    # EXCEL READER
    # -------------------------
    def _read_excel(self, file_path: Path) -> str:
        text = ""
        excel_file = pd.ExcelFile(file_path)

        for sheet in excel_file.sheet_names:
            df = excel_file.parse(sheet)
            text += f"\n--- Sheet: {sheet} ---\n"
            text += df.to_string(index=False)
            text += "\n"

        return text.strip()

    # -------------------------
    # IMAGE READER (OCR)
    # -------------------------
    def _read_image(self, file_path: Path) -> str:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()