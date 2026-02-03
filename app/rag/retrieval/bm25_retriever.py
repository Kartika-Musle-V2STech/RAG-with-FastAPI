"""
BM25 Retriever
Keyword-based search using BM25
"""

from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BM25Retriever:
    """Keyword search using BM25"""

    def __init__(self):
        self.corpus: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        logger.info("Initialized BM25Retriever")

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from document chunks.
        """

        if not chunks:
            logger.warning("Attempted to build BM25 index with empty chunks")
            return

        try:

            self.corpus = list(chunks)

            for chunk in self.corpus:
                if "content" not in chunk:
                    raise ValueError("Chunk missing required key: 'content'")

            # Tokenize documents
            self.tokenized_corpus = [
                self._tokenize(chunk["content"]) for chunk in self.corpus
            ]

            # Build BM25 index
            self.bm25 = BM25Okapi(self.tokenized_corpus)

            logger.info("BM25 index built successfully with %d chunks", len(chunks))

        except (ValueError, TypeError, KeyError) as e:
            logger.error("Data error building BM25 index: %s", str(e))
            raise
        except Exception:
            logger.exception("Unexpected error building BM25 index")
            raise

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words
        """
        return text.lower().split()

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25.
        """

        top_k = top_k if top_k is not None else settings.BM25_TOP_K

        if self.bm25 is None or not self.corpus:
            logger.warning("BM25 index not built, returning empty results")
            return []

        try:
            tokenized_query = self._tokenize(query)

            scores = self.bm25.get_scores(tokenized_query)

            ranked_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True,
            )[:top_k]

            results: List[Dict[str, Any]] = []

            for idx in ranked_indices:
                score = float(scores[idx])
                if score <= 0:
                    continue

                chunk = self.corpus[idx]

                results.append(
                    {
                        "id": chunk.get("id") or f"bm25_{idx}",
                        "content": chunk["content"],
                        "metadata": chunk.get("metadata", {}),
                        "score": score,
                        "source": "bm25",
                        "chunk_index": chunk.get("chunk_index", idx),
                    }
                )

            logger.info("BM25 search returned %d results", len(results))
            return results

        except (ValueError, TypeError) as e:
            logger.error("Error searching with BM25: %s", str(e))
            return []
        except Exception:
            logger.exception("Unexpected error searching with BM25")
            return []
