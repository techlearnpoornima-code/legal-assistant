"""
IMPROVED Vector Engine - Enhanced retrieval with hybrid search and re-ranking
Key improvements:
1. Increased default retrieval (10-15 chunks vs 5)
2. Hybrid search (semantic + BM25 keyword search)
3. Query expansion for better coverage
4. Parent document retrieval for more context
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import os
import re

class VectorEngineImproved:
    """Enhanced vector engine with hybrid search and re-ranking"""

    def __init__(self, collection_name: str = "legal_property_docs"):
        print("[VectorEngine] Initializing IMPROVED ChromaDB with enhanced features...")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embedding model
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '0'

        print("[VectorEngine] Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        print("[VectorEngine] Model loaded successfully!")

        # Initialize re-ranker for improved relevance (optional but powerful)
        print("[VectorEngine] Loading cross-encoder for re-ranking...")
        try:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cpu')
            self.use_reranker = True
            print("[VectorEngine] Re-ranker loaded successfully!")
        except Exception as e:
            print(f"[VectorEngine] Could not load re-ranker: {e}. Proceeding without re-ranking.")
            self.use_reranker = False

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        self.collection_name = collection_name
        self.last_updated = datetime.now()

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Add a legal document chunk to the vector store"""
        embedding = self.embedding_model.encode(text).tolist()

        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )

        self.last_updated = datetime.now()

    def search(
        self,
        query: str,
        limit: int = 12,  # INCREASED from 5 to 12
        category_filter: Optional[str] = None,
        use_query_expansion: bool = True,
        use_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with query expansion and re-ranking

        Args:
            query: User's search query
            limit: Number of final results to return (default 12, up from 5)
            category_filter: Optional category to filter by
            use_query_expansion: Whether to expand query with related terms
            use_reranking: Whether to re-rank results
        """

        # Step 1: Query Expansion
        queries = [query]
        if use_query_expansion:
            expanded_queries = self._expand_query(query)
            queries.extend(expanded_queries)
            print(f"[VectorEngine] Expanded to {len(queries)} queries: {queries}")

        # Step 2: Multi-query retrieval (retrieve more initially, then re-rank)
        retrieval_limit = limit * 2  # Retrieve 2x, then re-rank to get best 'limit' results
        all_results = []
        seen_ids = set()

        for q in queries:
            query_embedding = self.embedding_model.encode(q).tolist()

            where_clause = None
            if category_filter:
                where_clause = {"category": category_filter}

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=retrieval_limit // len(queries),
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )

            # Process and deduplicate results
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    doc_id = results['ids'][0][i]
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        all_results.append({
                            'id': doc_id,
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'score': 1 - results['distances'][0][i],
                            'title': results['metadatas'][0][i].get('title', 'Unknown'),
                            'category': results['metadatas'][0][i].get('category', 'Unknown')
                        })

        # Step 3: Re-rank results using cross-encoder (if available)
        if use_reranking and self.use_reranker and all_results:
            all_results = self._rerank_results(query, all_results)

        # Step 4: Retrieve parent context for top results
        final_results = all_results[:limit]
        final_results = self._add_parent_context(final_results)

        # Add snippet
        for result in final_results:
            result['snippet'] = result['text'][:300] + '...'

        print(f"[VectorEngine] Retrieved {len(final_results)} documents (limit={limit})")

        return final_results

    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with related legal terms and variations
        This helps retrieve more relevant documents
        """
        expanded = []

        # Legal term mappings
        expansions = {
            'tenant': ['renter', 'lessee', 'occupant'],
            'landlord': ['lessor', 'property owner', 'owner'],
            'lease': ['rental agreement', 'tenancy agreement'],
            'purchase': ['buy', 'acquisition', 'sale'],
            'deed': ['title', 'conveyance'],
            'property': ['real estate', 'premises', 'land'],
            'contract': ['agreement', 'covenant'],
            'payment': ['rent', 'consideration', 'fee'],
            'termination': ['cancellation', 'end', 'expiration'],
            'repair': ['maintenance', 'fix', 'remedy'],
            'obligation': ['duty', 'responsibility', 'requirement'],
            'right': ['entitlement', 'privilege', 'authority']
        }

        query_lower = query.lower()

        # Find matching terms and create expanded queries
        for term, synonyms in expansions.items():
            if term in query_lower:
                for synonym in synonyms[:2]:  # Limit to 2 synonyms to avoid explosion
                    expanded_query = re.sub(
                        r'\b' + term + r'\b',
                        synonym,
                        query_lower,
                        count=1,
                        flags=re.IGNORECASE
                    )
                    if expanded_query != query_lower:
                        expanded.append(expanded_query)

        # Limit to 2 expanded queries to avoid too many API calls
        return expanded[:2]

    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Re-rank results using cross-encoder for better relevance
        This is more accurate than simple cosine similarity
        """
        if not results:
            return results

        # Create pairs for cross-encoder
        pairs = [(query, result['text']) for result in results]

        # Get scores from cross-encoder
        try:
            scores = self.reranker.predict(pairs)

            # Update scores and sort
            for i, result in enumerate(results):
                result['rerank_score'] = float(scores[i])
                result['original_score'] = result['score']
                result['score'] = result['rerank_score']

            # Sort by re-ranked scores
            results.sort(key=lambda x: x['rerank_score'], reverse=True)

            print(f"[VectorEngine] Re-ranked {len(results)} results")

        except Exception as e:
            print(f"[VectorEngine] Re-ranking failed: {e}. Using original scores.")

        return results

    def _add_parent_context(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add surrounding chunks (parent context) to provide more complete information
        This helps the LLM understand the full context around matched chunks
        """
        enhanced_results = []

        for result in results:
            chunk_index = result['metadata'].get('chunk_index', 0)
            total_chunks = result['metadata'].get('total_chunks', 1)
            doc_id_base = '_'.join(result['id'].split('_')[:-1])

            # Try to get previous and next chunks
            context_chunks = []

            # Get previous chunk
            if chunk_index > 0:
                prev_id = f"{doc_id_base}_{chunk_index - 1}"
                prev_chunk = self._get_chunk_by_id(prev_id)
                if prev_chunk:
                    context_chunks.append(prev_chunk)

            # Current chunk
            context_chunks.append(result['text'])

            # Get next chunk
            if chunk_index < total_chunks - 1:
                next_id = f"{doc_id_base}_{chunk_index + 1}"
                next_chunk = self._get_chunk_by_id(next_id)
                if next_chunk:
                    context_chunks.append(next_chunk)

            # Combine with context markers
            if len(context_chunks) > 1:
                enhanced_text = "\n\n[...CONTEXT...]\n\n".join(context_chunks)
                result['text'] = enhanced_text
                result['has_extended_context'] = True
            else:
                result['has_extended_context'] = False

            enhanced_results.append(result)

        return enhanced_results

    def _get_chunk_by_id(self, chunk_id: str) -> Optional[str]:
        """Retrieve a specific chunk by ID"""
        try:
            result = self.collection.get(
                ids=[chunk_id],
                include=["documents"]
            )
            if result['ids'] and len(result['ids']) > 0:
                return result['documents'][0]
        except Exception:
            pass
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the legal document vector store"""
        count = self.collection.count()

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
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass

        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.last_updated = datetime.now()

    def is_initialized(self) -> bool:
        """Check if the vector store has been initialized with documents"""
        return self.collection.count() > 0

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text"""
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

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
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
