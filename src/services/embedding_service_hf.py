import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from src.config.config import settings

load_dotenv()
_model = None


def get_model():
    global _model
    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer(
            settings.embedding_model,
            cache_folder="./cache/hf_cache",
        )
        print("Embedding model berhasil di-load")
    return _model


class EmbeddingServiceHF:
    def __init__(self):
        self.model = get_model()

    def embed(self, text: str, doc_id: str | None = None) -> list[float]:
        return self.model.encode(text).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()


# Testing
if __name__ == "__main__":
    from rich import box
    from rich.console import Console
    from rich.table import Table

    from src.ingestion.document_loader import DocumentLoader

    loader = DocumentLoader()
    documents = loader.load_folder("data/")

    service = EmbeddingServiceHF()
    console = Console()

    print("=" * 50)
    print(f"Total Dokumen : {len(documents)}")
    print("=" * 50)

    table = Table(
        title="Embedding Preview — Seluruh Dokumen",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold black",
    )
    table.add_column("No", style="black", width=4, justify="center")
    table.add_column("Category", style="black", width=12)
    table.add_column("Filename", style="black", width=30)
    table.add_column("Input Text", style="black", width=35)
    table.add_column("Dimensi", style="black", width=8, justify="center")
    table.add_column("Preview Vector", style="black", width=30)

    for i, doc in enumerate(documents):
        sample_text = doc["text"].split("\n")[0][:100]
        vector = service.embed(sample_text)

        table.add_row(
            str(i + 1),
            doc["category"] or "-",
            doc["filename"],
            sample_text[:80] + "..." if len(sample_text) > 80 else sample_text,
            str(len(vector)),
            str([round(v, 4) for v in vector[:3]]) + "...",
        )

    console.print(table)
    print("EmbeddingService berhasil!")
# if __name__ == "__main__":
#     import sys, os
#     sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

#     from src.ingestion.document_loader import DocumentLoader

#     loader = DocumentLoader()
#     doc = loader.load("data/Skripsi/KB_PEDOMAN_SKRIPSI_BAB II.md")

#     sample_text = doc["text"].split("\n")[0]

#     service = EmbeddingService()
#     vector = service.embed(sample_text)

#     print("=" * 50)
#     print(f"Filename   : {doc['filename']}")
#     print(f"Input text : {sample_text}")
#     print(f"Dimensi    : {len(vector)}")
#     print(f"Preview    : {vector[:5]}")
#     print("=" * 50)
#     print("EmbeddingService berhasil!")
