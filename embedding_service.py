from google import genai
from config import GEMINI_API_KEY, EMBEDDING_MODEL

class EmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = EMBEDDING_MODEL

    def embed(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model     = self.model,
            contents   = [text]
        )
        return response.embeddings[0].values

    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model     = self.model,
            contents   = [text],
        )
        return response.embeddings[0].values