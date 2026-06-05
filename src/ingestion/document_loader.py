import os
from pypdf import PdfReader
from docx import Document
from rich.console import Console
from rich.table import Table
import re

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
            "text": text, 
            "filename": os.path.basename(path),
            "format": ext,
            "category": os.path.basename(os.path.dirname(path)),  
            "path": path,
        }
    def load_folder(self, base_path: str) -> list:
        documents = []
        for root, _, files in os.walk(base_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.SUPPORTED:
                    path = os.path.join(root, file)
                    try:
                        doc = self.load(path)
                        documents.append(doc)
                    except Exception as e:
                        print(f"Error baca {path}: {e}")
        return documents
    def _extract_pdf(self, path: str) -> str:
        reader = PdfReader(path)
        return "\n".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )
    def _extract_docx(self, path: str) -> str:
        doc = Document(path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    def _extract_md(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

# Testing
if __name__ == "__main__":
    loader = DocumentLoader()
    documents = loader.load_folder("data/")

    # print("=" * 50)
    # print(f"Total dokumen dimuat: {len(documents)}")
    # print("=" * 50)
    
    # for doc in documents:
    #     print(f"[{doc['category']}] {doc['filename']} ({doc['format']})")
    #     print(f"  Preview: {doc['text'][:100]}...")
    #     print()
        
    # TABEL RICH  
    console = Console()
    table = Table(
        title=f"Knowledge Base — {len(documents)} Dokumen",
        show_lines=True,
        header_style="bold black"
    )

    table.add_column("No",       style="black", width=4)
    table.add_column("Category", style="black", width=20)
    table.add_column("Filename", style="black", width=25)
    table.add_column("Format",   style="black", width=8)
    table.add_column("Preview",  style="black", width=50)

    for i, doc in enumerate(documents, 1):
        table.add_row(
            str(i),
            doc["category"],
            doc["filename"],
            doc["format"],
            doc["text"][:80].replace("\n", " ") + "...",
        )

    console.print(table)
    print("DocumentLoader berhasil!")