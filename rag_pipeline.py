from retriever import Retriever
from generator import ContextAssembler, GeminiGenerator
from document_loader import DocumentLoader
from text_chunker import TextChunker
from config import settings


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
            lines.append(f"[Chunk {i}]")
            lines.append(f"Source   : {c['source']}")
            lines.append(f"Category : {c['category']}")
            lines.append(f"Header   : {c['header']}")
            lines.append(f"Path     : {c['path']}")
            lines.append(f"Score    : {c['score']}")
            lines.append(f"key_id    : {c['key_id']}")
            lines.append("Text:")
            lines.append(c["text"])
            lines.append("")

        sources = list({c["source"] for c in chunks if c["source"]})

        return {"answer": "\n".join(lines), "sources": sources}
