"""Application Configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings configuration."""

    APP_NAME: str = "RAG FastAPI Application"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "sqlite:///./storage/app.db"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma2:2b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_PERSIST_DIRECTORY: str = "./storage/chroma"
    CHROMA_COLLECTION_NAME: str = "documents"

    UPLOAD_DIR: str = "./storage/documents"
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    BM25_TOP_K: int = 10
    VECTOR_TOP_K: int = 10
    HYBRID_TOP_K: int = 5
    RERANK_TOP_K: int = 3

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./storage/app.log"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()
