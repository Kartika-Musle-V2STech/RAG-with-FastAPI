"""Reranker"""

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Reranker:
    """Rerank documents using cross-encoder model"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize reranker"""
        try:
            self.model = CrossEncoder(model_name)
            logger.info("Initialized Reranker with model: %s", model_name)
        except Exception as e:
            logger.warning(
                "Could not initialize reranker: %s. Reranking will be skipped.", e
            )
            self.model = None

    def rerank(
        self, query: str, documents: List[Dict[str, Any]], top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on query relevance"""
        if not self.model:
            logger.warning("Reranker not initialized, returning original results")
            return documents[:top_k] if top_k else documents

        if not documents:
            return []

        top_k = top_k or settings.RERANK_TOP_K

        try:
            # Prepare query-document pairs
            pairs = [[query, doc["content"]] for doc in documents]
            # Get relevance scores
            scores = self.model.predict(pairs)
            # Add scores to documents
            for doc, score in zip(documents, scores):
                doc["rerank_score"] = float(score)
            # Sort by rerank score
            reranked_docs = sorted(
                documents, key=lambda doc: doc["rerank_score"], reverse=True
            )
            # Return top-k
            results = reranked_docs[:top_k]
            logger.info(
                "Reranked %s documents, returning top %s", len(documents), len(results)
            )
            return results
        except Exception as e:
            logger.error("Error during reranking: %s", e)
            return documents[:top_k]
