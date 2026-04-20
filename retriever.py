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

        docs = results.get("documents") or []
        metas = results.get("metadatas") or []
        dists = results.get("distances") or []

        if not docs:
            return []

        return [
            {"text": d, "meta": m, "distance": dist}
            for d, m, dist in zip(docs[0], metas[0], dists[0])
        ]
