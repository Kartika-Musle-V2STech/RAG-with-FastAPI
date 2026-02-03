"""RAG pipeline"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.rag.retrieval.hybrid_retriever import HybridRetriever
from app.rag.workflow.graph import rag_graph
from app.rag.workflow.state import create_initial_state
from app.utils import calculate_confidence_score
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    """Main RAG Pipeline"""

    def __init__(self, db: Session):
        """Initialize RAG pipeline"""
        self.db = db
        self.hybrid_retriever = HybridRetriever()
        self.graph = rag_graph

        logger.info("RAG pipeline initialized")

    def build_user_index(self, user_id: int):
        """Build BM25 index for user's documents"""
        try:
            chunks = (
                self.db.query(DocumentChunk)
                .join(Document)
                .filter(Document.user_id == user_id)
                .all()
            )

            if not chunks:
                logger.warning("No chunks found for user %s", user_id)
                return

            formatted_chunks = []
            for chunk in chunks:
                formatted_chunks.append(
                    {
                        "content": chunk.content,
                        "metadata": chunk.metadata or {},
                        "chunk_index": chunk.chunk_index,
                    }
                )

            # Build BM25 index
            self.hybrid_retriever.build_bm25_index(formatted_chunks)
            logger.info(
                "Built BM25 index with %s chunks for user %s",
                len(formatted_chunks),
                user_id,
            )

        except Exception as e:
            logger.error("Error building user index: %s", e)
            raise

    def process_query(
        self, query: str, user_id: int, thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process query through the RAG pipeline"""
        try:
            # Build user index (BM25) if not already built
            self.build_user_index(user_id)

            # Create initial state
            initial_state = create_initial_state(
                query=query, user_id=user_id, thread_id=thread_id
            )
            final_state = self.graph.invoke(initial_state)

            # extract results
            answer = final_state.get("answer", "No answer generated")
            context_documents = final_state.get("context_documents", [])
            metadata = final_state.get("metadata", {})

            # calculate confidence score
            if context_documents:
                confidence = calculate_confidence_score(context_documents)
            else:
                confidence = 0.0

            # format sources
            sources = self._format_sources(context_documents)

            # Build response
            response = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "confidence": confidence,
                    "steps": metadata.get("steps", []),
                    "retrieval_time_ms": metadata.get("retrieval_time_ms", 0),
                    "generation_time_ms": metadata.get("generation_time_ms", 0),
                    "total_time_ms": metadata.get("retrieval_time_ms", 0)
                    + metadata.get("generation_time_ms", 0),
                    "documents_retrieved": metadata.get("documents_retrieved", 0),
                    "documents_used": metadata.get("context_documents_used", 0),
                },
            }

            logger.info("Query processed successfully(confidence: %.2f)", confidence)
            return response

        except Exception as e:
            logger.error("Error processing query: %s", e)
            raise

    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            source = {
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index", 0),
                "content": doc.get("content", "")[:200] + "...",
                "relevance_score": doc.get("rerank_score")
                or doc.get("rrf_score")
                or doc.get("score", 0.0),
                "page": metadata.get("page"),
            }
            # Get document filename from database
            if source["document_id"]:
                db_doc = (
                    self.db.query(Document)
                    .filter(Document.id == source["document_id"])
                    .first()
                )
                if db_doc:
                    source["filename"] = db_doc.filename

            sources.append(source)

        return sources
