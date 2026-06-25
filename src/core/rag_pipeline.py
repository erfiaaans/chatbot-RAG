import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import re

from src.config.config import settings
from src.core.generator import ContextAssembler, GeminiGenerator
from src.core.retriever import Retriever
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.text_chunker import TextChunker


class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.assembler = ContextAssembler()
        self.generator = GeminiGenerator()
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.history = []

    def clean_response(self, text: str) -> str:
        """
        Membersihkan format jawaban AI agar lebih rapi
        """
        if not text:
            return "Informasi tidak ditemukan dalam dokumen."
        text = text.strip()
        text = text.replace("```", "")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +", " ", text)
        return text

    def rag_query(self, question: str) -> dict:
        chunks = self.retriever.retrieve(question)
        if not chunks:
            return {"answer": "Informasi tidak ditemukan dalam dokumen.", "sources": []}
        # sources = list({meta.get("source") for c in chunks if (meta := c.get("meta"))})
        unique_sources = {}
        for c in chunks:
            meta = c.get("meta", {})
            source_name = meta.get("source")
            if source_name and source_name not in unique_sources:
                unique_sources[source_name] = {
                    "name": source_name,
                    "url": meta.get(
                        "source_url", "#"
                    ),  # Ambil URL, default '#' jika kosong
                }
        sources = list(unique_sources.values())
        recent = self.history[-settings.conversation_window :]
        prompt = self.assembler.assemble(chunks, question, recent)
        result = self.generator.generate(prompt)
        self.history.append({"question": question, "answer": result})
        return {"answer": result, "sources": sources}

    def reset_history(self):
        self.history = []

    def dummy_rag_query(self, question):
        chunks = self.retriever.retrieve(question)
        if not chunks:
            return {"answer": "Informasi tidak ditemukan dalam dokumen.", "sources": []}
        lines = []
        lines.append(f'Jawaban untuk: "{question}"')
        lines.append("")
        lines.append("HASIL RETRIEVAL")
        lines.append("")
        for i, c in enumerate(chunks, 1):
            meta = c.get("meta", {})
            lines.append(f"[Chunk {i}]")
            lines.append(f"Source   : {meta.get('source', '-')}")
            lines.append(f"Category : {meta.get('category', '-')}")
            lines.append(f"Header   : {meta.get('header', '-')}")
            lines.append(f"Path     : {meta.get('path', '-')}")
            lines.append(f"Score    : {c.get('distance', '-')}")
            lines.append(f"Key ID   : {meta.get('key_id', '-')}")
            lines.append("Text:")
            lines.append(c.get("text", ""))
            lines.append("")
        answer = "\n".join(lines)
        try:
            # sources = list(
            #     {meta.get("source") for c in chunks if (meta := c.get("meta"))}
            # )
            unique_sources = {}
            for c in chunks:
                meta = c.get("meta", {})
                source_name = meta.get("source")
                if source_name and source_name not in unique_sources:
                    unique_sources[source_name] = {
                        "name": source_name,
                        "url": meta.get("source_url", "#"),
                    }
            sources = list(unique_sources.values())
            recent = self.history[-settings.conversation_window :]
            prompt = self.assembler.assemble(chunks, question, recent)
            self.history.append({"question": question, "answer": "Haloo"})
            return {"answer": prompt, "sources": sources}
        except Exception as e:
            return {
                "answer": f"{str(e)}",
                "sources": [],
            }


# Testing
if __name__ == "__main__":
    print("FILE LOADED", flush=True)
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    try:
        print("Inisialisasi pipeline...", flush=True)
        pipeline = RAGPipeline()
        print("Pipeline OK", flush=True)

        conversations = [
            "Apa saja isi dari Kajian Teoritis?",
            "Bagaimana format penulisan daftar pustaka?",
            "Boleh saya tanya lagi tentang kajian teoritis tadi?",
        ]

        for i, question in enumerate(conversations, 1):
            print(f"\n[Giliran {i}]", flush=True)
            print(f"Pertanyaan : {question}", flush=True)
            print(f"Riwayat sebelumnya: {len(pipeline.history)} percakapan", flush=True)

            result = pipeline.rag_query(question)

            print(f"Jawaban    : {result['answer'][:200]} ...", flush=True)
            print(f"Sumber     : {result['sources']}", flush=True)

        print("\n--- Verifikasi History Tersimpan ---", flush=True)
        print(f"Total riwayat : {len(pipeline.history)} percakapan", flush=True)
        for i, h in enumerate(pipeline.history, 1):
            print(f"\n  [History {i}]", flush=True)
            print(f"  Q : {h['question']}", flush=True)
            print(f"  A : {h['answer'][:100]} ...", flush=True)

        print("\n--- Pengujian Reset History ---", flush=True)
        pipeline.reset_history()
        print(f"History setelah reset: {len(pipeline.history)} percakapan", flush=True)
        print("[OK] Reset history berhasil.", flush=True)

        print("\n" + "=" * 60, flush=True)
        print("Pengujian selesai.", flush=True)

    except Exception as e:
        print(f"\nERROR: {e}", flush=True)
        import traceback

        traceback.print_exc()
