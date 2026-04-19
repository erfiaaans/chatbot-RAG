from retriever         import Retriever
from generator         import ContextAssembler, GeminiGenerator
from config            import CONVERSATION_WINDOW
from document_loader import DocumentLoader
from text_chunker import TextChunker

class RAGPipeline:
    def __init__(self):
        self.retriever  = Retriever()
        self.assembler  = ContextAssembler()
        self.generator  = GeminiGenerator()
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.history    = []

    def query(self, question: str) -> dict:
        chunks  = self.retriever.retrieve(question)
        if not chunks:
            return {
                "answer"  : "Informasi tidak ditemukan dalam dokumen.",
                "sources" : []
            }
        recent  = self.history[-CONVERSATION_WINDOW:]
        prompt  = self.assembler.assemble(chunks, question, recent)
        result  = self.generator.generate(prompt, chunks)
        self.history.append({
            "question" : question,
            "answer"   : result["answer"]
        })
        return result

    def reset_history(self):
        self.history = []
        
    def dummy_rag_query(self, question):
        documents = self.loader.load_folder("./documents")
        # documents = self.loader.load_folder("./documents/Skripsi")
        # doc = self.loader.load("./documents/Skripsi/KB_PEDOMAN_SKRIPSI_BAB II.md")
        # documents = [doc]  # biar tetap list
        # paths = [
        #     "./documents/Skripsi/bab1.md",
        #     "./documents/Magang/laporan1.md"
        # ]

        # documents = [self.loader.load(p) for p in paths]

        all_chunks = []

        for doc in documents:
            chunks = self.chunker.chunk(
                text=doc["text"],
                metadata=doc
            )
            print(chunks)
            all_chunks.extend(chunks)

        print(len(all_chunks))
        return {
            "answer": f"Ini jawaban dummy untuk pertanyaan: '{question}'. Sistem sedang dalam tahap pengembangan streaming chatbot.",
            "sources": ["dokumen1.pdf", "panduan_skripsi.md"]
        }