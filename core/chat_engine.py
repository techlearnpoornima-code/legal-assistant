"""
IMPROVED Legal Chat Engine - Enhanced RAG pipeline with better context handling
Key improvements:
1. Retrieves 12 chunks instead of 5
2. Increased max_tokens from 800 to 1500 for more complete answers
3. Better context formatting with priorities
4. Token-aware context window management
5. Query classification for better retrieval strategy
"""

import os
from typing import List, Dict, Any
from openai import OpenAI


class ChatEngineImproved:
    """Enhanced chat engine with improved RAG pipeline"""

    def __init__(self, vector_engine):
        self.vector_engine = vector_engine

        # Initialize OpenAI client
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )

        print(f"[ChatEngine] Using API endpoint: {api_base}")

        self.legal_disclaimer = """⚠️ LEGAL DISCLAIMER: This information is for educational purposes only and does not constitute legal advice. For specific legal matters, please consult with a qualified attorney licensed in your jurisdiction."""

        # IMPROVED: More detailed system prompt with better instructions
        self.system_prompt = """You are a Legal Property Assistant, a specialized AI that helps users understand property law, contracts, deeds, leases, and related legal documents.

Your knowledge base includes:
- Property deeds and title documents
- Lease agreements and rental contracts
- Purchase and sale agreements
- Property regulations and zoning laws
- Landlord-tenant laws
- Property rights and easements
- Mortgage and financing documents

When answering questions:
1. Be precise and cite specific clauses or sections from the provided legal documents
2. Explain legal terms in plain language when needed
3. Highlight important obligations, rights, and potential risks
4. If the information isn't in the context, clearly state so
5. Use bullet points for clarity when listing multiple items
6. Always maintain a professional, objective tone
7. Reference specific document sections when applicable
8. Prioritize information from documents with higher relevance scores
9. When multiple documents contain relevant information, synthesize the information coherently
10. If the context is insufficient to fully answer the question, acknowledge what's missing

CRITICAL: The context provided contains the most relevant legal document excerpts. Use ALL provided context to give a comprehensive answer. If different documents provide different perspectives or details, mention all of them.

IMPORTANT: Always remind users that this is informational only and not legal advice. Complex legal matters require consultation with a licensed attorney.

Context from relevant legal documents will be provided with each query."""

    def get_response(self, user_query: str) -> Dict[str, Any]:
        """
        IMPROVED RAG pipeline with enhanced retrieval and context handling
        """

        print(f"[ChatEngine] Processing query: '{user_query}'")

        # Step 1: Classify query to determine retrieval strategy
        query_type = self._classify_query(user_query)
        print(f"[ChatEngine] Query classified as: {query_type}")

        # Step 2: IMPROVED Retrieval - Get MORE relevant documents (12 instead of 5)
        retrieval_limit = 12  # INCREASED from 5 to 12
        relevant_docs = self.vector_engine.search(
            user_query,
            limit=retrieval_limit,
            use_query_expansion=True,
            use_reranking=True
        )

        print(f"[ChatEngine] Retrieved {len(relevant_docs)} documents")

        # Step 3: Deduplicate and prioritize sources
        unique_docs = self._deduplicate_and_prioritize(relevant_docs)
        print(f"[ChatEngine] After deduplication: {len(unique_docs)} unique documents")

        # Step 4: IMPROVED Context Creation - Token-aware, prioritized
        context = self._create_enhanced_legal_context(unique_docs, max_tokens=6000)

        # Step 5: Create augmented prompt
        augmented_prompt = self._create_augmented_prompt(user_query, context, query_type)

        # Step 6: Generation with INCREASED max_tokens
        try:
            print(f"[ChatEngine] Generating response...")
            print(f"[ChatEngine] Context size: {len(context)} chars")
            print(f"[ChatEngine] Using {len(unique_docs)} unique sources")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": augmented_prompt}
                ],
                temperature=0.3,
                max_tokens=1500  # INCREASED from 800 to 1500
            )

            answer = response.choices[0].message.content

            # Add legal disclaimer
            answer_with_disclaimer = f"{answer}\n\n{self.legal_disclaimer}"

            # Calculate confidence
            confidence = self._calculate_confidence(unique_docs)

            return {
                "answer": answer_with_disclaimer,
                "sources": unique_docs[:8],  # Return top 8 sources for display
                "confidence": confidence,
                "legal_disclaimer": self.legal_disclaimer,
                "query_type": query_type,
                "total_sources_used": len(unique_docs)
            }

        except Exception as e:
            print(f"[ChatEngine] Error: {e}")
            return {
                "answer": self._create_fallback_response(user_query, unique_docs),
                "sources": unique_docs[:8],
                "confidence": 0.5,
                "legal_disclaimer": self.legal_disclaimer
            }

    def _classify_query(self, query: str) -> str:
        """
        Classify the query to determine retrieval strategy
        This helps tailor the response to the query type
        """
        query_lower = query.lower()

        if any(word in query_lower for word in ['what is', 'define', 'meaning', 'explain']):
            return 'definition'
        elif any(word in query_lower for word in ['how to', 'process', 'procedure', 'steps']):
            return 'procedural'
        elif any(word in query_lower for word in ['can i', 'am i allowed', 'is it legal', 'rights']):
            return 'rights_and_obligations'
        elif any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return 'comparison'
        elif any(word in query_lower for word in ['risk', 'danger', 'warning', 'avoid', 'liability']):
            return 'risk_analysis'
        else:
            return 'general'

    def _deduplicate_and_prioritize(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate by title and prioritize by relevance score
        Ensures we don't show redundant information from the same document
        """
        unique_docs = []
        seen_titles = set()

        # Sort by score first
        documents_sorted = sorted(documents, key=lambda x: x.get('score', 0), reverse=True)

        for doc in documents_sorted:
            title = doc['metadata'].get('title', 'Document')
            # Use title + chunk_index as unique identifier
            unique_key = f"{title}_{doc['metadata'].get('chunk_index', 0)}"

            if unique_key not in seen_titles:
                seen_titles.add(unique_key)
                unique_docs.append(doc)

        return unique_docs

    def _create_enhanced_legal_context(self, documents: List[Dict[str, Any]], max_tokens: int = 6000) -> str:
        """
        IMPROVED: Create token-aware context with priorities
        Ensures high-relevance documents get full representation
        """
        if not documents:
            return "No relevant legal documents found in the database."

        context_parts = []
        estimated_tokens = 0
        tokens_per_char = 0.25  # Rough estimate: 1 token ≈ 4 chars

        for i, doc in enumerate(documents, 1):
            # Estimate tokens for this document
            doc_text = doc['text']
            doc_tokens = len(doc_text) * tokens_per_char

            # Check if adding this document would exceed token limit
            if estimated_tokens + doc_tokens > max_tokens and i > 3:
                # Keep at least top 3 documents, then stop if token limit reached
                print(f"[ChatEngine] Stopping at document {i} to stay within token limit")
                break

            # Format document with clear structure
            doc_section = []
            doc_section.append(f"[Legal Document {i}]")
            doc_section.append(f"Title: {doc['metadata']['title']}")
            doc_section.append(f"Category: {doc['metadata']['category']}")
            doc_section.append(f"Document Type: {doc['metadata'].get('document_type', 'Unknown')}")

            # Add section information if available
            if 'section' in doc['metadata']:
                doc_section.append(f"Section: {doc['metadata']['section']}")

            doc_section.append(f"Relevance Score: {doc['score']:.2f}")

            # Add context marker if this chunk has extended context
            if doc.get('has_extended_context'):
                doc_section.append("(Note: This excerpt includes surrounding context for better understanding)")

            doc_section.append(f"\nContent:\n{doc_text}")
            doc_section.append("\n" + "-" * 80 + "\n")

            full_section = "\n".join(doc_section)
            context_parts.append(full_section)
            estimated_tokens += doc_tokens

        final_context = "\n".join(context_parts)
        print(f"[ChatEngine] Context created: ~{int(estimated_tokens)} tokens, {len(documents)} documents included")

        return final_context

    def _create_augmented_prompt(self, query: str, context: str, query_type: str) -> str:
        """
        IMPROVED: Create augmented prompt with query-type-specific instructions
        """

        # Query-type-specific instructions
        type_instructions = {
            'definition': "Focus on providing clear definitions and explanations of legal terms.",
            'procedural': "Explain the step-by-step process clearly, noting any requirements or deadlines.",
            'rights_and_obligations': "Clearly distinguish between rights and obligations. Highlight any conditions or exceptions.",
            'comparison': "Provide a clear comparison, highlighting key differences and similarities.",
            'risk_analysis': "Identify potential risks, liabilities, or concerns. Be thorough and cautious.",
            'general': "Provide a comprehensive answer based on all available context."
        }

        specific_instruction = type_instructions.get(query_type, type_instructions['general'])

        prompt = f"""Based on the following legal documents and property law information, please answer the user's question accurately and comprehensively.

LEGAL CONTEXT FROM DATABASE:
{context}

USER QUESTION:
{query}

QUERY TYPE: {query_type}

INSTRUCTIONS:
- {specific_instruction}
- Provide accurate legal information based on the context above
- Cite specific document sections or clauses when applicable
- Explain legal terms in plain language
- If the context doesn't contain enough information, state this clearly and explain what information is missing
- Highlight any important obligations, rights, or potential risks
- Be objective and professional
- Use information from ALL provided documents when relevant
- If multiple documents provide different perspectives, mention all of them
- Prioritize information from documents with higher relevance scores

Please provide your comprehensive response:"""

        return prompt

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """
        IMPROVED: Better confidence calculation based on retrieval quality
        """
        if not documents:
            return 0.0

        # Factor 1: Average score of top documents
        top_scores = [doc['score'] for doc in documents[:5]]
        avg_top_score = sum(top_scores) / len(top_scores)

        # Factor 2: Number of relevant documents (more is better, up to a point)
        num_docs_factor = min(len(documents) / 10.0, 1.0)

        # Factor 3: Score consistency (less variance = higher confidence)
        if len(documents) > 1:
            scores = [doc['score'] for doc in documents]
            score_variance = sum((s - avg_top_score) ** 2 for s in scores) / len(scores)
            consistency_factor = 1.0 / (1.0 + score_variance)
        else:
            consistency_factor = 1.0

        # Combine factors
        confidence = (0.5 * avg_top_score) + (0.3 * num_docs_factor) + (0.2 * consistency_factor)

        return min(confidence, 1.0)

    def _create_fallback_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Create a fallback response when LLM is unavailable"""
        if not documents:
            return f"I couldn't find any relevant legal documents about your question in the database.\n\n{self.legal_disclaimer}"

        response = "Based on the available legal documents, here is the relevant information:\n\n"

        # Show top 3 documents
        for i, doc in enumerate(documents[:3], 1):
            response += f"**{i}. {doc['metadata']['title']}**\n"
            response += f"Category: {doc['metadata']['category']}\n"
            response += f"Relevance: {doc['score']:.0%}\n\n"

            text = doc['text']
            if len(text) > 500:
                text = text[:500]
                last_period = text.rfind('.')
                if last_period > 300:
                    text = text[:last_period + 1]
                text += "..."

            response += f"{text}\n\n"

        response += f"{self.legal_disclaimer}"

        return response

    def analyze_legal_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze a specific legal text or clause"""

        prompts = {
            "general": "Provide a general analysis of this legal text, explaining its purpose and key provisions.",
            "risks": "Identify and explain potential risks, liabilities, or unfavorable terms in this legal text.",
            "obligations": "Extract and list all obligations, duties, and responsibilities mentioned in this legal text."
        }

        prompt = prompts.get(analysis_type, prompts["general"])

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nLEGAL TEXT:\n{text}"}
                ],
                temperature=0.3,
                max_tokens=1500  # INCREASED from 800
            )

            analysis = response.choices[0].message.content

            return {
                "analysis": f"{analysis}\n\n{self.legal_disclaimer}",
                "type": analysis_type
            }

        except Exception as e:
            return {
                "analysis": f"Unable to analyze text: {str(e)}\n\n{self.legal_disclaimer}",
                "type": analysis_type
            }
