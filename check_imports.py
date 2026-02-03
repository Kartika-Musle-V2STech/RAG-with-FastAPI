#!/usr/bin/env python3
"""
Import Checker
Checks if all imports work correctly
"""

print("Checking imports...")

try:
    print("✓ Checking config...")
    from app.config import settings

    print("✓ Checking database...")
    from app.db.base import Base
    from app.db.session import engine, get_db
    from app.db.init_db import init_database

    print("✓ Checking models...")
    from app.models import User, Conversation, Message, Document, DocumentChunk

    print("✓ Checking schemas...")
    from app.schemas.user import UserCreate, UserResponse, Token
    from app.schemas.document import DocumentResponse, DocumentList
    from app.schemas.conversation import ChatRequest, ChatResponse

    print("✓ Checking core...")
    from app.core.security import get_password_hash, verify_password

    print("✓ Checking services...")
    from app.services.auth_service import authenticate_user, create_user
    from app.services.document_service import save_document, process_document
    from app.services.chat_service import process_chat_query

    print("✓ Checking RAG components...")
    from app.rag.processing.docling import DocumentProcessor
    from app.rag.processing.chunking import TextChunker
    from app.rag.processing.embedding import EmbeddingGenerator
    from app.rag.retrieval.vector_retriever import VectorRetriever
    from app.rag.retrieval.bm25_retriever import BM25Retriever
    from app.rag.retrieval.hybrid_retriever import HybridRetriever
    from app.rag.retrieval.reranker import Reranker
    from app.rag.llm.ollama_client import OllamaClient
    from app.rag.workflow.state import RAGState
    from app.rag.workflow.nodes import retrieval_node
    from app.rag.workflow.graph import build_rag_graph
    from app.rag.pipeline import RAGPipeline

    print("✓ Checking routes...")
    from app.api.routes import auth, documents, chat
    from app.api.deps import get_current_user

    print("✓ Checking main app...")
    from app.main import app

    print("\n" + "=" * 60)
    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("=" * 60)

except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nFix this error before running the application.")
    exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    exit(1)
