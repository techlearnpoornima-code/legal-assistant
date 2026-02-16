#!/usr/bin/env python3
"""
Quick script to re-process documents with improved chunking
"""

import sys
import shutil
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from core.vector_engine import VectorEngineImproved as VectorEngine
from core.document_processor import DocumentProcessorImproved as DocumentProcessor

def main():
    print("\n" + "="*80)
    print("  Re-processing Documents with Improved Chunking")
    print("="*80 + "\n")

    # Delete old database
    db_path = Path(__file__).parent / "chroma_db"
    if db_path.exists():
        print(f"[1] Deleting old database: {db_path}")
        shutil.rmtree(db_path)
        print("  ✓ Old database deleted")
    else:
        print("[1] No existing database found")

    # Initialize components
    print("\n[2] Initializing improved components...")
    vector_engine = VectorEngine(collection_name="legal_property_docs")
    print("  ✓ Vector engine initialized")

    doc_processor = DocumentProcessor(vector_engine)
    print("  ✓ Document processor initialized")

    # Process documents
    print("\n[3] Processing documents with new chunking strategy...")
    print("  - Chunk size: 1500 chars (was 1000)")
    print("  - Chunk overlap: 200 chars (was 150)")
    print("  - Section-aware: Yes")
    print("  - Keyword extraction: Yes")

    result = doc_processor.process_all_documents()

    print("\n" + "="*80)
    print("  ✓ Re-processing Complete!")
    print("="*80)
    print(f"\n  Processed: {result['processed']} documents")
    print(f"  Created: {result['chunks']} chunks")

    # Show stats
    stats = vector_engine.get_stats()
    print(f"\n  Database Statistics:")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Total documents: {stats['total_documents']}")
    print(f"  - Categories: {', '.join(stats['categories'])}")

    print("\n" + "="*80)
    print("  Next Steps:")
    print("  1. Start your application: python app.py")
    print("  2. Test with a query to see the improvements")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
