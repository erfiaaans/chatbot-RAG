from embedding_service import EmbeddingService
from vector_store      import VectorStore
from config            import TOP_K

class QueryEmbedder:
    def __init__(self):
        self.embedder = EmbeddingService()

    def embed_query(self, question: str) -> list[float]:
        question = question.strip().lower()
        return self.embedder.embed_query(question)

class Retriever:
    def __init__(self):
        self.store    = VectorStore()
        self.embedder = QueryEmbedder()

    def retrieve(self, question: str) -> list[dict]:
        vector  = self.embedder.embed_query(question)
        results = self.store.search(vector, k=TOP_K)
        chunks  = []
        for i, doc in enumerate(results["documents"][0]):
            chunks.append({
                "text"     : doc,
                "filename" : results["metadatas"][0][i]["filename"],
                "score"    : 1 - results["distances"][0][i]
            })
        return chunks