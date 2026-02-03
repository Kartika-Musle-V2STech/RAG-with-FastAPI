#!/usr/bin/env python3
"""
Structure Checker
Verifies all required files exist
"""

import os
from pathlib import Path

REQUIRED_FILES = [
    # Root
    "pyproject.toml",
    ".env",
    ".gitignore",
    # App core
    "app/__init__.py",
    "app/main.py",
    "app/config.py",
    # Database
    "app/db/__init__.py",
    "app/db/base.py",
    "app/db/session.py",
    "app/db/init_db.py",
    # Models
    "app/models/__init__.py",
    "app/models/user.py",
    "app/models/conversation.py",
    "app/models/document.py",
    # Schemas
    "app/schemas/__init__.py",
    "app/schemas/user.py",
    "app/schemas/conversation.py",
    "app/schemas/document.py",
    # Core
    "app/core/__init__.py",
    "app/core/security.py",
    # API
    "app/api/__init__.py",
    "app/api/deps.py",
    "app/api/routes/__init__.py",
    "app/api/routes/auth.py",
    "app/api/routes/documents.py",
    "app/api/routes/chat.py",
    # Services
    "app/services/__init__.py",
    "app/services/auth_service.py",
    "app/services/document_service.py",
    "app/services/chat_service.py",
    # RAG
    "app/rag/__init__.py",
    "app/rag/pipeline.py",
    "app/rag/processing/__init__.py",
    "app/rag/processing/docling.py",
    "app/rag/processing/chunking.py",
    "app/rag/processing/embedding.py",
    "app/rag/retrieval/__init__.py",
    "app/rag/retrieval/vector_retriever.py",
    "app/rag/retrieval/bm25_retriever.py",
    "app/rag/retrieval/hybrid_retriever.py",
    "app/rag/retrieval/reranker.py",
    "app/rag/llm/__init__.py",
    "app/rag/llm/ollama_client.py",
    "app/rag/llm/tools.py",
    "app/rag/llm/tool_executor.py",
    "app/rag/workflow/__init__.py",
    "app/rag/workflow/state.py",
    "app/rag/workflow/nodes.py",
    "app/rag/workflow/graph.py",
    # Utils
    "app/utils/__init__.py",
    "app/utils/logger.py",
    "app/utils/helpers.py",
    # Scripts
    "scripts/__init__.py",
    "scripts/create_admin.py",
]

REQUIRED_DIRS = [
    "storage",
]

print("Checking file structure...\n")

missing_files = []
for file in REQUIRED_FILES:
    if not os.path.exists(file):
        missing_files.append(file)
        print(f"❌ Missing: {file}")
    else:
        print(f"✓ Found: {file}")

print("\nChecking directories...\n")

missing_dirs = []
for dir_path in REQUIRED_DIRS:
    if not os.path.exists(dir_path):
        missing_dirs.append(dir_path)
        print(f"❌ Missing directory: {dir_path}")
    else:
        print(f"✓ Found directory: {dir_path}")

print("\n" + "=" * 60)

if missing_files or missing_dirs:
    print("❌ STRUCTURE CHECK FAILED")
    print(f"\nMissing {len(missing_files)} files and {len(missing_dirs)} directories")
    exit(1)
else:
    print("✅ ALL FILES AND DIRECTORIES PRESENT!")
    print("=" * 60)
