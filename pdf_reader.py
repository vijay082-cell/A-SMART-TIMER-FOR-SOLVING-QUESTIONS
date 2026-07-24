"""
pdf_reader.py
-------------
Thin wrapper around PyMuPDF (fitz) for reading DPP PDFs.

Responsibilities today:
  * Count pages (so we can auto-suggest a question count)
  * Extract raw text from pages (useful for FUTURE OCR/AI analysis)

No paid APIs are used. The PDF content is kept available for later AI modules.
"""

import fitz  # PyMuPDF


class PDFReader:
    def __init__(self, path):
        self.path = path
        self.doc = fitz.open(path)

    def page_count(self):
        return len(self.doc)

    def get_text(self, page_index=0):
        if 0 <= page_index < len(self.doc):
            return self.doc[page_index].get_text()
        return ""

    def get_all_text(self):
        return "\n".join(page.get_text() for page in self.doc)

    def close(self):
        try:
            self.doc.close()
        except Exception:
            pass


def count_pdf_pages(path):
    """Return number of pages in a PDF, or 0 on failure."""
    try:
        doc = fitz.open(path)
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return 0
