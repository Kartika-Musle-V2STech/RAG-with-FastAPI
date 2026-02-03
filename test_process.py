#!/usr/bin/env python3
"""
Manual document processing test
"""

from app.db.session import SessionLocal
from app.services.document_service import process_document

# Document ID from database
DOCUMENT_ID = 1

db = SessionLocal()

try:
    print(f"Processing document {DOCUMENT_ID}...")
    document = process_document(DOCUMENT_ID, db)
    print(
        f"✅ Success! Status: {document.processed_status}, Chunks: {document.chunk_count}"
    )
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    db.close()
