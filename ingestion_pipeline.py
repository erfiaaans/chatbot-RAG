import uuid
from document_loader import DocumentLoader
from text_chunker    import TextChunker
from embedding_service import EmbeddingService
from vector_store    import VectorStore

class IngestionPipeline:
    def __init__(self):
        self.loader    = DocumentLoader()
        self.chunker   = TextChunker()
        self.embedder  = EmbeddingService()
        self.store     = VectorStore()

    def run(self, file_path: str) -> dict:
        # doc     = self.loader.load(file_path)
        # chunks  = self.chunker.chunk(doc["text"])
        chunks = ["chunk 1", "chunk 2", "chunk 3"] # untuk testing
        vectors = [self.embedder.embed(chunk) for chunk in chunks]
        doc_id  = str(uuid.uuid4())
        self.store.add(
            chunks   = chunks,
            vectors  = vectors,
            metadata = {
                "filename" : doc["filename"],
                "doc_id"   : doc_id
            }
        )
        return {
            "status"   : "berhasil",
            "filename" : doc["filename"],
            "chunks"   : len(chunks),
            "doc_id"   : doc_id
        }

    def re_ingest(self, file_path: str, doc_id: str) -> dict:
        self.store.delete(doc_id)
        return self.run(file_path)