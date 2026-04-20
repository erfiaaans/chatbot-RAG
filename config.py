from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    embedding_model: str = Field(default="embedding-001", alias="EMBEDDING_MODEL")
    llm_model: str = Field(default="gemini-1.5-flash", alias="LLM_MODEL")

    # LLM Config
    temperature: float = Field(default=0.2, alias="TEMPERATURE")
    max_output_tokens: int = Field(default=1024, alias="MAX_OUTPUT_TOKENS")

    # RAG Config
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=3, alias="TOP_K")

    # Vector DB
    chroma_path: str = Field(default="./chroma_db", alias="CHROMA_PATH")
    collection_name: str = Field(default="akademik_tif_unipma", alias="COLLECTION_NAME")

    # Chat Memory
    conversation_window: int = Field(default=5, alias="CONVERSATION_WINDOW")

    model_config = {"env_file": ".env", "populate_by_name": True, "extra": "ignore"}


settings = Settings()
