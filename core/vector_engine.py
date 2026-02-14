"""
Vector Engine - Manages vector database operations using ChromaDB for legal documents
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from datetime import datetime
import os

class VectorEngine:

    def __init__(self, collection_name: str = "legal_property_docs"):

        print("[VectorEngine] Initializing ChromaDB for legal documents...")
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '0'  # Allow downloading
        
        print("[VectorEngine] Loading embedding model...")
        print("[VectorEngine] Note: First-time download may take 2-3 minutes (~90MB)")
        
        try:
            # Try to load model with progress indication
            import sys
            sys.stdout.flush()
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            print("[VectorEngine] Model loaded successfully!")
        except Exception as e:
            print(f"[VectorEngine] Error loading model: {e}")
            print("[VectorEngine] Attempting offline mode...")
            # Try to work offline if model exists
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            import warnings
            warnings.filterwarnings('ignore')
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        self.collection_name = collection_name
        self.last_updated = datetime.now()
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Add a legal document chunk to the vector store"""
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()
        
        # Add to collection
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        
        self.last_updated = datetime.now()
    
    def search(self, query: str, limit: int = 5, category_filter: str = None) -> List[Dict[str, Any]]:
        """Search for relevant legal documents using semantic similarity"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Prepare where clause for category filtering
        where_clause = None
        if category_filter:
            where_clause = {"category": category_filter}
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'title': results['metadatas'][0][i].get('title', 'Unknown'),
                    'category': results['metadatas'][0][i].get('category', 'Unknown'),
                    'snippet': results['documents'][0][i][:200] + '...'
                })
        
        return formatted_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the legal document vector store"""
        count = self.collection.count()
        
        # Count unique documents and categories
        all_metadata = self.collection.get()['metadatas']
        unique_files = set()
        categories = set()
        
        if all_metadata:
            for meta in all_metadata:
                unique_files.add(meta.get('file', ''))
                categories.add(meta.get('category', ''))
        
        return {
            'total_chunks': count,
            'total_documents': len(unique_files),
            'categories': sorted(list(categories)),
            'last_updated': self.last_updated.isoformat()
        }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        # Delete and recreate collection
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass  # Collection might not exist
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.last_updated = datetime.now()
    
    def is_initialized(self) -> bool:
        """Check if the vector store has been initialized with documents"""
        return self.collection.count() > 0
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text (useful for analysis)"""
        return self.embedding_model.encode(text).tolist()
    
    def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all documents from a specific legal category"""
        try:
            results = self.collection.get(
                where={"category": category},
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    formatted_results.append({
                        'id': results['ids'][i],
                        'text': results['documents'][i],
                        'metadata': results['metadatas'][i],
                        'title': results['metadatas'][i].get('title', 'Unknown')
                    })
            
            return formatted_results
        except Exception as e:
            print(f"[VectorEngine] Error searching by category: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a specific document by ID"""
        try:
            result = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception as e:
            print(f"[VectorEngine] Error retrieving document: {e}")
            return None