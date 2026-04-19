import os
from pypdf import PdfReader
from docx import Document

class DocumentLoader:
    SUPPORTED = [".pdf", ".docx", ".md"]

    def load(self, path: str) -> dict:
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.SUPPORTED:
            raise ValueError(f"Format {ext} tidak didukung.")
        
        if ext == ".pdf":
            text = self._extract_pdf(path)
        elif ext == ".docx":
            text = self._extract_docx(path)
        elif ext == ".md":
            text = self._extract_md(path)

        return {
            "text"     : text,
            "filename" : os.path.basename(path),
            "format"   : ext
        }

    def _extract_pdf(self, path: str) -> str:
        reader = PdfReader(path)
        return "\n".join(
            page.extract_text() for page in reader.pages
            if page.extract_text()
        )

    def _extract_docx(self, path: str) -> str:
        doc = Document(path)
        return "\n".join(
            para.text for para in doc.paragraphs
            if para.text.strip()
        )

    def _extract_md(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        import re
        text = re.sub(r"#{1,6}\s*",    "", text)   # hapus heading #
        text = re.sub(r"\*\*|\*|__",   "", text)   # hapus bold/italic
        text = re.sub(r"`{1,3}",       "", text)   # hapus code block
        text = re.sub(r"\[.*?\]\(.*?\)","", text)  # hapus link
        text = re.sub(r"!\[.*?\]\(.*?\)","",text)  # hapus gambar
        text = re.sub(r"-{3,}|\*{3,}", "", text)   # hapus garis horizontal
        text = re.sub(r"\n{3,}",      "\n\n", text) # rapikan spasi
        return text.strip()