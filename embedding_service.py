from llama_index.embeddings.huggingface import HuggingFaceEmbedding

class EmbeddingService:
    def __init__(self):
        self.model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def embed(self, text: str) -> list[float]:
        return self.model.get_text_embedding(text)

    def embed_query(self, text: str) -> list[float]:
        return self.model.get_query_embedding(text)