import os
from pypdf import PdfReader
from docx import Document
import re


class DocumentLoader:
    SUPPORTED = [".pdf", ".docx", ".md"]

    # ==============================
    #  LOAD SINGLE FILE
    # ==============================
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
            "text": text,  # type: ignore
            "filename": os.path.basename(path),
            "format": ext,
            "category": os.path.basename(os.path.dirname(path)),  #  tambahan
            "path": path,
        }

    # ==============================
    #  LOAD FOLDER (RECURSIVE)
    # ==============================
    def load_folder(self, base_path: str) -> list:
        documents = []

        for root, _, files in os.walk(base_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()

                if ext in self.SUPPORTED:
                    path = os.path.join(root, file)

                    try:
                        doc = self.load(path)  # pakai fungsi load tadi
                        documents.append(doc)
                    except Exception as e:
                        print(f"❌ Error baca {path}: {e}")

        return documents

    # ==============================
    #  EXTRACT PDF
    # ==============================
    def _extract_pdf(self, path: str) -> str:
        reader = PdfReader(path)
        return "\n".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )

    # ==============================
    #  EXTRACT DOCX
    # ==============================
    def _extract_docx(self, path: str) -> str:
        doc = Document(path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

    # ==============================
    #  EXTRACT MARKDOWN
    # ==============================
    def _extract_md(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # optional cleaning aman:
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
