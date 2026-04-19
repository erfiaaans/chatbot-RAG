from embedding_service import EmbeddingService
from vector_store import VectorStore
from config import settings


class QueryEmbedder:
    def __init__(self):
        self.embedder = EmbeddingService()

    def embed_query(self, question: str) -> list[float]:
        question = question.strip().lower()
        return self.embedder.embed_query(question)


class Retriever:
    def __init__(self):
        self.store = VectorStore()
        self.embedder = QueryEmbedder()

    def retrieve(self, question: str) -> list[dict]:
        vector = self.embedder.embed_query(question)
        results = self.store.search(vector, k=settings.top_k)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        chunks = []

        for doc, meta, distance in zip(documents, metadatas, distances):
            chunks.append(
                {
                    "text": doc.strip(),
                    "source": meta.get("source", "-"),
                    "category": meta.get("category", "-"),
                    "header": meta.get("header", ""),
                    "path": meta.get("path", "-"),
                    "score": round(1 - distance, 4),
                }
            )

        return chunks
