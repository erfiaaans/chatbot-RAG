import datetime
import json
import logging
import os
import queue
import sys
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.config.config import settings

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.embedding_model

        self.log_queue = queue.Queue()
        threading.Thread(target=self._log_worker, daemon=True).start()

    def _log_worker(self):
        while True:
            log_entry = self.log_queue.get()
            if log_entry is None:
                break
            try:
                with open("embedding_log.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                logger.error(f"Gagal menulis log embedding: {e}")
            self.log_queue.task_done()

    def save_log(
        self,
        log_type: str,
        text: str,
        latency: float,
        total_tokens: int,
        doc_id: str | None = None,
    ):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": log_type,
            "model": self.model_name,
            "doc_id": doc_id,
            "chars_count": len(text),
            "tokens_count": total_tokens,
            "latency_seconds": round(latency, 3),
            "text_snippet": text,
        }
        self.log_queue.put(log_entry)

    def embed(self, text: str, doc_id: str | None = None) -> list[float]:
        start_time = time.time()

        total_tokens = len(text) // 4

        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT", title="document"
            ),
        )

        latency = time.time() - start_time

        logger.warning(
            f"[EMBED_DOC] {f'DocID: {doc_id} | ' if doc_id else ''}"
            f"Model: {self.model_name} | "
            f"Chars: {len(text)} | "
            f"Tokens: ~{total_tokens} | "
            f"Latency: {latency:.3f}s | "
            f"Text: {text[:50]}..."
        )

        self.save_log(
            log_type="EMBED_DOC",
            text=text,
            latency=latency,
            total_tokens=total_tokens,
            doc_id=doc_id,
        )

        if not result.embeddings or result.embeddings[0].values is None:
            return []

        return result.embeddings[0].values

    def embed_query(self, text: str) -> list[float]:
        start_time = time.time()

        token_info = self.client.models.count_tokens(
            model=self.model_name, contents=text
        )
        total_tokens = token_info.total_tokens

        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )

        latency = time.time() - start_time

        logger.warning(
            f"[EMBED_QUERY] Model: {self.model_name} | "
            f"Chars: {len(text)} | Tokens: {total_tokens} | "
            f"Latency: {latency:.3f}s | Text: {text}"
        )

        self.save_log(
            log_type="EMBED_QUERY",
            text=text,
            latency=latency,
            total_tokens=total_tokens,
            doc_id=None,
        )

        if not result.embeddings or result.embeddings[0].values is None:
            return []

        return result.embeddings[0].values


# Testing
if __name__ == "__main__":
    from rich import box
    from rich.console import Console
    from rich.table import Table

    from src.ingestion.document_loader import DocumentLoader

    loader = DocumentLoader()
    documents = loader.load_folder("data/")

    service = EmbeddingService()
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
