import chromadb
import uuid
from config import CHROMA_PATH, COLLECTION_NAME

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name     = COLLECTION_NAME,
            metadata = {"hnsw:space": "cosine"}
        )

    def add(self, chunks: list, vectors: list, metadata: dict):
        ids = [str(uuid.uuid4()) for _ in chunks]
        metas = [
            {
                "filename" : metadata["filename"],
                "doc_id"   : metadata["doc_id"],
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        self.collection.add(
            ids        = ids,
            documents  = chunks,
            embeddings = vectors,
            metadatas  = metas
        )

    def search(self, query_vector: list, k: int = 5) -> dict:
        results = self.collection.query(
            query_embeddings = [query_vector],
            n_results        = k,
            include          = ["documents", "metadatas", "distances"]
        )
        return results

    def delete(self, doc_id: str):
        results = self.collection.get(
            where = {"doc_id": doc_id}
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])