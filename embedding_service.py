# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            cache_folder="./hf_cache"
        )

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()