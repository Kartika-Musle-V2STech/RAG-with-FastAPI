"""Hybrid Retriever"""

from typing import List, Dict, Any
from app.rag.retrieval.bm25_retriever import BM25Retriever
from app.rag.retrieval.vector_retriever import VectorRetriever
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """Hybrid search combining BM25 and vector search"""

    def __init__(self):
        """Initialize hybrid retriever"""
        self.bm25_retriever = BM25Retriever()
        self.vector_retriever = VectorRetriever()
        self.rrf_k = 60

        logger.info("Initialized HybridRetriever")

    def build_bm25_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Build BM25 index from chunks"""
        self.bm25_retriever.build_index(chunks)

    def search(
        self, query: str, user_id: int, top_k: int | None = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search using BM25 + Vector with RRF"""
        top_k = top_k if top_k is not None else settings.HYBRID_TOP_K

        bm25_results = self.bm25_retriever.search(
            query=query, top_k=settings.BM25_TOP_K
        )

        vector_results = self.vector_retriever.search(
            query=query, user_id=user_id, top_k=settings.VECTOR_TOP_K
        )

        logger.info(
            "Hybrid candidates: bm25=%d vector=%d",
            len(bm25_results),
            len(vector_results),
        )

        return self._reciprocal_rank_fusion(bm25_results, vector_results, top_k)

    # RRF
    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Fuse ranked lists using reciprocal rank fusion"""

        fused: dict[str, dict[str, Any]] = {}

        def add_results(results: List[Dict[str, Any]], source: str):
            for rank, result in enumerate(results):
                chunk_id = result.get("id") or f"{source}_{rank}"

                score = 1.0 / (self.rrf_k + rank + 1)

                if chunk_id not in fused:
                    fused[chunk_id] = {
                        "result": result.copy(),
                        "rrf_score": 0.0,
                        "sources": set(),
                    }

                fused[chunk_id]["rrf_score"] += score
                fused[chunk_id]["sources"].add(source)

        add_results(bm25_results, "bm25")
        add_results(vector_results, "vector")

        ranked = sorted(
            fused.values(),
            key=lambda x: x["rrf_score"],
            reverse=True,
        )
        final_results = []
        for item in ranked[:top_k]:
            result = item["result"]
            result["rrf_score"] = round(item["rrf_score"], 6)
            result["sources"] = sorted(item["sources"])
            result["source"] = "hybrid"
            final_results.append(result)
        return final_results
