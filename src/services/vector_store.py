import chromadb
import uuid
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config.config import settings
from chromadb.api.types import QueryResult, Metadata
class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name, metadata={"hnsw:space": "cosine"}
        )
    def _get_collection_count(self) -> int:
        try:
            collection = self.client.get_collection(name=settings.collection_name)
            return collection.count()
        except Exception:
            return 0
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
    def delete_by_collection_name(self, collection_name: str) -> dict:
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            return {"status": "not found", "collection_name": collection_name}
        count = collection.count()
        self.client.delete_collection(name=collection_name)
        if collection_name == self.collection.name:
            self.collection = self.client.get_or_create_collection(
                name=settings.collection_name, metadata={"hnsw:space": "cosine"}
            )
        return {
            "status": "deleted",
            "collection_name": collection_name,
            "deleted_chunks": count,
        }
#Testing
if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

    from src.ingestion.document_loader import DocumentLoader
    from src.ingestion.text_chunker import TextChunker
    from src.services.embedding_service import EmbeddingService

    print("Loading dokumen...")
    loader = DocumentLoader()
    # doc = loader.load("data/Skripsi/KB_PEDOMAN_SKRIPSI_BAB II.md")
    doc = loader.load("data/Kurikulum/KB_KURIKULUM.md")
    print(f"Dokumen berhasil dimuat: {doc['filename']}")

    print("Chunking...")
    chunker = TextChunker()
    chunks = chunker.chunk(doc["text"], doc)
    print(f"Total chunk: {len(chunks)}")

    print("Embedding...")
    embedder = EmbeddingService()
    vectors = [embedder.embed(c.text) for c in chunks]
    print(f"Total vektor: {len(vectors)}")

    print("Menyimpan ke VectorStore...")
    store = VectorStore()
    store.add(chunks, vectors, metadata={"doc_id": doc["filename"]})
    print("Data tersimpan!")

    query = "Syarat penulisan skripsi"
    query_vector = embedder.embed_query(query)
    results = store.search(query_vector, k=3)

    print("=" * 50)
    print(f"Filename     : {doc['filename']}")
    print(f"Total chunk  : {len(chunks)}")
    print(f"Total vektor : {len(vectors)}")
    print(f"Query        : {query}")
    print("-" * 50)
    for i, (res_doc, res_meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"\n[Hasil {i+1}]")
        print(f"  Header  : {res_meta['header']}")
        print(f"  Preview : {res_doc[:120]}")
    print("\n" + "=" * 50)
    print("VectorStore berhasil!")