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

        chunk_text = "\n\n".join(
            [
                f"[Chunk {i + 1}]\n{c.page_content if hasattr(c, 'page_content') else str(c)}"
                for i, c in enumerate(chunks)
            ]
        )

        sources = list(
            {
                c.metadata.get("source")
                for c in chunks
                if hasattr(c, "metadata") and c.metadata.get("source")
            }
        )

        answer = f"Jawaban untuk: '{question}'\n\n--- CHUNKS ---\n{chunk_text}"

        return {"answer": answer, "sources": ", ".join(sources)}
