"""
Legal Chat Engine - Handles the RAG pipeline and response generation for legal queries
"""

import os
from typing import List, Dict, Any
from openai import OpenAI

class ChatEngine:
    def __init__(self, vector_engine):
        self.vector_engine = vector_engine
        
        # Initialize OpenAI client using environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        
        print(f"[ChatEngine] Using API endpoint: {api_base}")
        
        # Legal disclaimer
        self.legal_disclaimer = """⚠️ LEGAL DISCLAIMER: This information is for educational purposes only and does not constitute legal advice. For specific legal matters, please consult with a qualified attorney licensed in your jurisdiction."""
        
        # System prompt for the legal assistant
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

IMPORTANT: Always remind users that this is informational only and not legal advice. Complex legal matters require consultation with a licensed attorney.

Context from relevant legal documents will be provided with each query."""
    
    def get_response(self, user_query: str) -> Dict[str, Any]:
        """
        Main RAG pipeline for legal queries:
        1. Retrieve relevant legal documents
        2. Augment the prompt with legal context
        3. Generate response with legal considerations
        """
        
        # Step 1: Retrieval - Get relevant legal documents
        relevant_docs = self.vector_engine.search(user_query, limit=5)
        
        # Deduplicate sources by title
        unique_docs = []
        seen_titles = set()
        for doc in relevant_docs:
            title = doc['metadata'].get('title', 'Document')
            if title not in seen_titles:
                seen_titles.add(title)
                unique_docs.append(doc)
        
        # Step 2: Augmentation - Create legal context
        context = self._create_legal_context(unique_docs)
        augmented_prompt = self._create_augmented_prompt(user_query, context)
        
        # Step 3: Generation
        try:
            print( f"[ChatEngine] Generating response for query: '{user_query}' with {len(unique_docs)} unique documents")
            print(f"[ChatEngine] Augmented prompt:\n{augmented_prompt[:500]}...\n")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": augmented_prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual legal responses
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            
            # Add legal disclaimer to response
            answer_with_disclaimer = f"{answer}\n\n{self.legal_disclaimer}"
            
            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(unique_docs)
            
            return {
                "answer": answer_with_disclaimer,
                "sources": unique_docs,
                "confidence": confidence,
                "legal_disclaimer": self.legal_disclaimer
            }
            
        except Exception as e:
            print(f"[ChatEngine] Error: {e}")
            # Fallback response if LLM fails
            return {
                "answer": self._create_fallback_response(user_query, unique_docs),
                "sources": unique_docs,
                "confidence": 0.5,
                "legal_disclaimer": self.legal_disclaimer
            }
    
    def analyze_legal_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze a specific legal text or clause"""
        
        prompts = {
            "general": "Provide a general analysis of this legal text, explaining its purpose and key provisions.",
            "risks": "Identify and explain potential risks, liabilities, or unfavorable terms in this legal text.",
            "obligations": "Extract and list all obligations, duties, and responsibilities mentioned in this legal text."
        }
        
        prompt = prompts.get(analysis_type, prompts["general"])

        import pdb;pdb.set_trace()
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nLEGAL TEXT:\n{text}"}
                ],
                temperature=0.3,
                max_tokens=800
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
    
    def _create_legal_context(self, documents: List[Dict[str, Any]]) -> str:
        """Create legal context string from retrieved documents"""
        if not documents:
            return "No relevant legal documents found in the database."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Legal Document {i}]")
            context_parts.append(f"Title: {doc['metadata']['title']}")
            context_parts.append(f"Category: {doc['metadata']['category']}")
            context_parts.append(f"Document Type: {doc['metadata'].get('file', 'Unknown')}")
            context_parts.append(f"Relevance Score: {doc['score']:.2f}")
            context_parts.append(f"\nContent:\n{doc['text']}")
            context_parts.append("\n" + "-"*80 + "\n")
        
        return "\n".join(context_parts)
    
    def _create_augmented_prompt(self, query: str, context: str) -> str:
        """Create the augmented prompt with query and legal context"""
        return f"""Based on the following legal documents and property law information, please answer the user's question accurately and comprehensively.

LEGAL CONTEXT FROM DATABASE:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Provide accurate legal information based on the context
- Cite specific document sections or clauses when applicable
- Explain legal terms in plain language
- If the context doesn't contain enough information, state this clearly
- Highlight any important obligations, rights, or potential risks
- Be objective and professional

Please provide your response:"""
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieval quality"""
        if not documents:
            return 0.0
        
        # Average of top 3 document scores
        scores = [doc['score'] for doc in documents[:3]]
        avg_score = sum(scores) / len(scores)
        
        # Adjust confidence based on number of relevant documents
        if len(documents) >= 3 and avg_score > 0.7:
            return min(avg_score + 0.1, 1.0)
        
        return avg_score
    
    def _create_fallback_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Create a fallback response when LLM is unavailable"""
        if not documents:
            return f"I couldn't find any relevant legal documents about your question in the database.\n\n{self.legal_disclaimer}"
        
        # Create a structured fallback response
        response = "Based on the available legal documents, here is the relevant information:\n\n"
        
        # Show the most relevant document
        top_doc = documents[0]
        response += f"**{top_doc['metadata']['title']}**\n"
        response += f"Category: {top_doc['metadata']['category']}\n"
        response += f"Relevance: {top_doc['score']:.0%}\n\n"
        
        # Show content from top document
        text = top_doc['text']
        if len(text) > 500:
            text = text[:500]
            last_period = text.rfind('.')
            if last_period > 300:
                text = text[:last_period + 1]
            text += "..."
        
        response += f"{text}\n\n"
        
        # Add other relevant sources
        if len(documents) > 1:
            response += "**Additional Relevant Documents:**\n"
            for doc in documents[1:3]:
                response += f"• {doc['metadata']['title']} ({doc['metadata']['category']})\n"
        
        response += f"\n{self.legal_disclaimer}"
        
        return response