from retriever         import Retriever
from generator         import ContextAssembler, GeminiGenerator
from config            import CONVERSATION_WINDOW

class RAGPipeline:
    def __init__(self):
        self.retriever  = Retriever()
        self.assembler  = ContextAssembler()
        self.generator  = GeminiGenerator()
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