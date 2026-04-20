from src.core.retriever import Retriever
from src.core.generator import ContextAssembler, GeminiGenerator
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.text_chunker import TextChunker
from src.config import settings


class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.assembler = ContextAssembler()
        self.generator = GeminiGenerator()
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.history = []

    def query(self, question: str) -> dict:
        chunks = self.retriever.retrieve(question)
        if not chunks:
            return {"answer": "Informasi tidak ditemukan dalam dokumen.", "sources": []}
        recent = self.history[-settings.conversation_window :]
        prompt = self.assembler.assemble(chunks, question, recent)
        result = self.generator.generate(prompt, chunks)
        self.history.append({"question": question, "answer": result["answer"]})
        return result

    def reset_history(self):
        self.history = []

    # def dummy_rag_query(self, question):
    #     return {
    #         "answer": f"Ini jawaban dummy untuk pertanyaan: '{question}'. Sistem sedang dalam tahap pengembangan streaming chatbot.",
    #         "sources": ["dokumen1.pdf", "panduan_skripsi.md"]
    #     }

    def dummy_rag_query(self, question):
        chunks = self.retriever.retrieve(question)

        if not chunks:
            return {"answer": "Informasi tidak ditemukan dalam dokumen.", "sources": []}

        lines = []
        lines.append(f'Jawaban untuk: "{question}"')
        lines.append("")
        lines.append("--- HASIL RETRIEVAL ---")
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
            sources = list(
                {meta.get("source") for c in chunks if (meta := c.get("meta"))}
            )
            recent = self.history[-settings.conversation_window :]
            prompt = self.assembler.assemble(chunks, question, recent)
            self.history.append({"question": question, "answer": "Haloo"})
            return {"answer": prompt, "sources": sources}
        except Exception as e:
            return {
                "answer": f"{str(e)}",
                "sources": [],
            }
