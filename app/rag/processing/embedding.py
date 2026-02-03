"""Embedding Generation"""

import time
from typing import List
import ollama
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using Ollama"""

    def __init__(self, model_name: str = None):
        """Initialize embedding generator"""
        self.model_name = model_name or settings.OLLAMA_EMBEDDING_MODEL
        logger.info("Initialized EmbeddingGenerator with model: %s", self.model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            embedding = response["embedding"]
            logger.debug(
                "Generated embedding for text (length: %s, dim: %s)",
                len(text),
                len(embedding),
            )
            return embedding
        except Exception as e:
            logger.error("Error generating embedding: %s", e)
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        """
        embeddings = []
        batch_size = 10  # Increased batch size for efficiency

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(texts) - 1) // batch_size + 1
            logger.info(
                "🔄 Embedding batch %d/%d (chunks %d-%d of %d)",
                batch_num,
                total_batches,
                i + 1,
                min(i + batch_size, len(texts)),
                len(texts),
            )

            for text in batch:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error("Error generating embedding for text %s: %s", i, e)
                    # Append zero vector as fallback
                    embeddings.append([0.0] * 768)

            # Small delay to prevent Ollama overload
            if i + batch_size < len(texts):
                time.sleep(0.05)

        logger.info("Generated %s embeddings total", len(embeddings))
        return embeddings
