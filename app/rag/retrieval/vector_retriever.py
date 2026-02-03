"""
Vector Retriever (SAFE)
One instance per processing job
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.rag.processing.embedding import EmbeddingGenerator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorRetriever:
    """Handles document embedding storage and retrieval using ChromaDB.

    This class manages the interaction with the ChromaDB vector database,
    including storing document chunks with their embeddings and metadata.
    One instance should be created per processing job.
    """

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()

        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,
            ),
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
        )

    def add_documents(
        self,
        chunks: List[Dict[str, Any]],
        document_id: int,
        user_id: int,
    ) -> List[str]:
        """Add document chunks to the vector store with embeddings.

        Args:
            chunks: List of chunk dictionaries containing 'content',
                'chunk_index', and 'metadata' keys.
            document_id: Unique identifier for the source document.
            user_id: Unique identifier for the document owner.

        Returns:
            List of generated chunk IDs stored in the collection.
        """
        ids, docs, metas = [], [], []
        texts = []  # Collect texts for batch embedding

        for chunk in chunks:
            ids.append(f"doc_{document_id}_chunk_{chunk['chunk_index']}_user_{user_id}")
            docs.append(chunk["content"])
            texts.append(chunk["content"])
            meta = chunk["metadata"].copy()
            meta.update(
                {
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_index": chunk["chunk_index"],
                }
            )
            metas.append(meta)

        # Generate all embeddings in batch with progress logging
        logger.info("Generating embeddings for %d chunks...", len(texts))
        embeds = self.embedding_generator.generate_embeddings(texts)
        logger.info("All embeddings generated successfully")

        self.collection.add(
            ids=ids,
            documents=docs,
            metadatas=metas,
            embeddings=embeds,
        )

        return ids

    def search(
        self,
        query: str,
        user_id: int,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.

        Args:
            query: The search query text.
            user_id: User ID to filter results.
            top_k: Number of results to return.

        Returns:
            List of matching documents with scores.
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Query ChromaDB with user filter
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": user_id},
        )

        # Format results
        documents = []
        if results and results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append(
                    {
                        "id": (
                            results["ids"][0][i] if results.get("ids") else f"vec_{i}"
                        ),
                        "content": doc,
                        "metadata": (
                            results["metadatas"][0][i]
                            if results.get("metadatas")
                            else {}
                        ),
                        "distance": (
                            results["distances"][0][i]
                            if results.get("distances")
                            else 0.0
                        ),
                        "source": "vector",
                    }
                )

        logger.info(
            "Vector search returned %d results for user %d", len(documents), user_id
        )
        return documents

    def delete_document_chunks(self, document_id: int, user_id: int) -> None:
        """Delete all chunks for a document from the vector store.

        Args:
            document_id: Unique identifier for the document to delete.
            user_id: Unique identifier for the document owner.
        """
        self.collection.delete(
            where={
                "$and": [
                    {"document_id": document_id},
                    {"user_id": user_id},
                ]
            }
        )
