import chromadb
import uuid
from config import settings


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, chunks: list, vectors: list, metadata: dict):
        ids = [str(uuid.uuid4()) for _ in chunks]

        documents = [c.text for c in chunks]
        metadatas = [{**c.metadata, "doc_id": metadata["doc_id"]} for c in chunks]

        self.collection.add(
            ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas
        )

    def search(self, query_vector: list, k: int = 5) -> dict:
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        return results

    def delete(self, doc_id: str):
        results = self.collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
