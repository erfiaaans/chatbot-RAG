import chromadb
import uuid
from config import settings
from chromadb.api.types import QueryResult, Metadata


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, chunks: list, vectors: list, metadata: dict):
        ids = [str(uuid.uuid4()) for _ in chunks]

        documents = [c.text for c in chunks]

        metadatas: list[Metadata] = [
            {**c.metadata, "doc_id": metadata["doc_id"]} for c in chunks
        ]

        self.collection.add(
            ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas
        )

    def search(self, query_vector: list, k: int = 5) -> QueryResult:
        results = self.collection.query(query_embeddings=[query_vector], n_results=k)
        return results

    def delete(self, doc_id: str):
        results = self.collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def delete_by_doc_id(self, doc_id: str):
        results = self.collection.get(where={"doc_id": doc_id})

        ids = results.get("ids", [])

        if not ids:
            return {"status": "not found", "deleted": 0}

        self.collection.delete(ids=ids)

        return {"status": "deleted", "doc_id": doc_id, "deleted_chunks": len(ids)}
