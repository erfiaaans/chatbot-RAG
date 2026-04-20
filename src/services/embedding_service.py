from sentence_transformers import SentenceTransformer  # type: ignore
from src.config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer(
            settings.embedding_model,
            cache_folder="./cache/hf_cache",
        )
        print("Embedding model berhasil di-load")
    return _model


class EmbeddingService:
    def __init__(self):
        self.model = get_model()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
