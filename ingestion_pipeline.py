import uuid
from document_loader import DocumentLoader
from text_chunker import TextChunker
from embedding_service import EmbeddingService
from vector_store import VectorStore


class IngestionPipeline:
    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.embedder = EmbeddingService()
        self.store = VectorStore()

    def run_documents(
        self,
        documents: list[dict],
        overwrite: bool = False,
        doc_id: str | None = None,
    ) -> dict:
        all_chunks = []
        all_vectors = []

        doc_id = doc_id or str(uuid.uuid4())

        for doc in documents:
            source = doc.get("source", "")

            if overwrite and source:
                self.store.delete(doc_id=doc_id)

            chunks = self.chunker.chunk(text=doc["text"], metadata=doc)

            vectors = [self.embedder.embed(c.text) for c in chunks]

            all_chunks.extend(chunks)
            all_vectors.extend(vectors)

        self.store.add(
            chunks=all_chunks,
            vectors=all_vectors,
            metadata={"doc_id": doc_id, "total_files": len(documents)},
        )
        data = {
            "status": "berhasil",
            "doc_id": doc_id,
            "overwrite": overwrite,
            "total_files": len(documents),
            "total_chunks": len(all_chunks),
        }
        print(data)
        return data

    # ==============================
    # 🔥 INGEST SINGLE FILE
    # ==============================
    def run(self, file_path: str) -> dict:
        doc = self.loader.load(file_path)

        chunks = self.chunker.chunk(text=doc["text"], metadata=doc)

        vectors = [self.embedder.embed(c.text) for c in chunks]

        doc_id = str(uuid.uuid4())

        self.store.add(
            chunks=chunks,
            vectors=vectors,
            metadata={
                "filename": doc["filename"],
                "category": doc.get("category"),
                "doc_id": doc_id,
            },
        )

        return {
            "status": "berhasil",
            "filename": doc["filename"],
            "chunks": len(chunks),
            "doc_id": doc_id,
        }

    # ==============================
    # 🔥 INGEST FOLDER (INI YANG KAMU BUTUH)
    # ==============================
    def run_folder(self, folder_path: str) -> dict:
        documents = self.loader.load_folder(folder_path)

        all_chunks = []
        all_vectors = []

        doc_id = str(uuid.uuid4())

        for doc in documents:
            chunks = self.chunker.chunk(text=doc["text"], metadata=doc)

            vectors = [self.embedder.embed(c.text) for c in chunks]

            all_chunks.extend(chunks)
            all_vectors.extend(vectors)

        self.store.add(
            chunks=all_chunks,
            vectors=all_vectors,
            metadata={"doc_id": doc_id, "total_files": len(documents)},
        )

        return {
            "status": "berhasil",
            "total_files": len(documents),
            "total_chunks": len(all_chunks),
            "doc_id": doc_id,
        }

    # ==============================
    # 🔄 RE-INGEST
    # ==============================
    def re_ingest(self, file_path: str, doc_id: str) -> dict:
        self.store.delete(doc_id)
        return self.run(file_path)
