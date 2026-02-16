"""
IMPROVED Legal Document Processor - Enhanced chunking and context preservation
Key improvements:
1. Larger chunk size (1500 chars vs 1000) for better context
2. Smarter overlap (200 chars vs 150) to preserve legal clauses
3. Hierarchical chunking with section awareness
4. Metadata enrichment for better filtering
"""

import os
import re
from typing import List, Dict, Any
from pathlib import Path
import hashlib
from core.file_reader import FileReader


class DocumentProcessorImproved:
    """Enhanced document processor with improved chunking for legal documents"""

    def __init__(self, vector_engine):
        self.vector_engine = vector_engine
        self.docs_path = Path(__file__).parent.parent / "legal-docs"

        # IMPROVED: Larger chunks with better overlap for legal documents
        self.chunk_size = 1500  # INCREASED from 1000 to 1500
        self.chunk_overlap = 200  # INCREASED from 150 to 200

        # Legal document categories
        self.categories = {
            'contracts': 'Purchase and Sale Contracts',
            'deeds': 'Property Deeds and Titles',
            'leases': 'Lease Agreements',
            'regulations': 'Property Laws and Regulations'
        }

    def process_all_documents(self) -> Dict[str, int]:
        """Process all legal documents in the legal-docs folder"""

        processed_count = 0
        chunk_count = 0

        file_reader = FileReader()

        # Clear existing data
        print("[DocumentProcessor] Clearing existing database...")
        self.vector_engine.clear_collection()

        # Ensure docs folder exists
        if not self.docs_path.exists():
            print(f"[DocumentProcessor] Creating {self.docs_path}")
            self.docs_path.mkdir(parents=True, exist_ok=True)

            # Create category subdirectories
            for category in self.categories.keys():
                category_path = self.docs_path / category
                category_path.mkdir(exist_ok=True)

                # Create sample document
                self._create_sample_document(category_path, category)

            print("[DocumentProcessor] Sample documents created")

        # Process each category
        for category in self.docs_path.iterdir():
            if not category.is_dir():
                continue

            category_name = category.name
            print(f"\n[DocumentProcessor] Processing category: {category_name}")

            for doc_file in category.iterdir():
                if not doc_file.is_file():
                    continue

                try:
                    text = file_reader.read(doc_file)

                    if not text or not text.strip():
                        print(f"  ⚠ Skipping empty file: {doc_file.name}")
                        continue

                    chunks = self.process_document(
                        file_path=doc_file,
                        category=category_name,
                        content=text
                    )

                    chunk_count += len(chunks)
                    processed_count += 1

                    print(f"  ✓ {doc_file.name} ({len(chunks)} chunks)")

                except Exception as e:
                    print(f"  ✗ Error processing {doc_file.name}: {e}")

        return {
            "processed": processed_count,
            "chunks": chunk_count
        }

    def process_document(self, file_path: Path, category: str, content: str) -> List[Dict[str, Any]]:
        """Process a single legal document into enhanced chunks"""

        # Extract metadata
        title = self._extract_title(content)
        doc_type = self._identify_document_type(content, file_path.name)
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()

        # IMPROVED: Extract document structure for better metadata
        sections = self._extract_sections(content)

        # Create legal-aware chunks with section context
        chunks = self._create_legal_chunks_enhanced(content, sections)

        processed_chunks = []

        for i, chunk_data in enumerate(chunks):
            chunk_metadata = {
                "title": title or file_path.stem.replace('-', ' ').replace('_', ' ').title(),
                "category": category,
                "document_type": doc_type,
                "file": file_path.name,
                "chunk_index": i,
                "total_chunks": len(chunks),
                # NEW: Add section information for better context
                "section": chunk_data.get('section', 'Unknown'),
                "keywords": ",".join(chunk_data.get('keywords', [])) 
            }

            chunk_id = f"{doc_id}_{i}"

            # Add to vector store
            self.vector_engine.add_document(
                chunk_id,
                chunk_data['text'],
                chunk_metadata
            )

            processed_chunks.append({
                "id": chunk_id,
                "text": chunk_data['text'],
                "metadata": chunk_metadata
            })

        return processed_chunks

    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract section headers and their positions for context-aware chunking
        This helps maintain section context in chunks
        """
        sections = []

        # Patterns for section headers
        patterns = [
            (r'^#{1,3}\s+(.+)$', 'markdown_header'),  # Markdown headers
            (r'^(?:SECTION|Section)\s+(\d+[:\.]?\s*.+)$', 'section'),
            (r'^(?:ARTICLE|Article)\s+(\d+[:\.]?\s*.+)$', 'article'),
            (r'^\d+\.\s+([A-Z][^\.]+)$', 'numbered_section'),
            (r'^[A-Z][A-Z\s]{5,}$', 'uppercase_header')  # All caps headers
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern, section_type in patterns:
                match = re.match(pattern, line.strip(), re.MULTILINE)
                if match:
                    section_title = match.group(1) if match.lastindex else line.strip()
                    sections.append({
                        'title': section_title,
                        'type': section_type,
                        'line_num': i,
                        'char_position': sum(len(l) + 1 for l in lines[:i])
                    })
                    break

        return sections

    def _create_legal_chunks_enhanced(self, text: str, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create enhanced chunks with section awareness and metadata
        Each chunk includes information about which section it belongs to
        """
        chunks = []

        # If we have clear sections, chunk by section first
        if len(sections) > 1:
            for i, section in enumerate(sections):
                start_pos = section['char_position']
                end_pos = sections[i + 1]['char_position'] if i + 1 < len(sections) else len(text)

                section_content = text[start_pos:end_pos].strip()
                section_title = section['title']

                # If section is larger than chunk size, split it
                if len(section_content) <= self.chunk_size:
                    chunks.append({
                        'text': section_content,
                        'section': section_title,
                        'keywords': self._extract_keywords(section_content)
                    })
                else:
                    # Split large section into sub-chunks, maintaining section context
                    sub_chunks = self._create_chunks_with_context(section_content, section_title)
                    chunks.extend(sub_chunks)
        else:
            # No clear sections, use enhanced chunking with keyword extraction
            basic_chunks = self._create_chunks(text)
            for chunk_text in basic_chunks:
                chunks.append({
                    'text': chunk_text,
                    'section': 'General',
                    'keywords': self._extract_keywords(chunk_text)
                })

        return [c for c in chunks if c['text'].strip()]

    def _create_chunks_with_context(self, text: str, section_title: str) -> List[Dict[str, Any]]:
        """
        Create chunks for a large section, prepending section title for context
        This ensures the LLM always knows which section the chunk is from
        """
        chunks = []
        basic_chunks = self._create_chunks(text)

        for chunk_text in basic_chunks:
            # Prepend section title if not already present
            if not chunk_text.startswith(section_title):
                enhanced_text = f"[{section_title}]\n\n{chunk_text}"
            else:
                enhanced_text = chunk_text

            chunks.append({
                'text': enhanced_text,
                'section': section_title,
                'keywords': self._extract_keywords(chunk_text)
            })

        return chunks

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important legal keywords from text for better metadata
        This helps with filtering and retrieval
        """
        # Common legal terms to look for
        legal_terms = [
            'lease', 'tenant', 'landlord', 'rent', 'deposit', 'eviction',
            'deed', 'title', 'grantor', 'grantee', 'covenant', 'warranty',
            'purchase', 'sale', 'buyer', 'seller', 'closing', 'escrow',
            'zoning', 'regulation', 'permit', 'variance', 'ordinance',
            'obligation', 'liability', 'indemnify', 'breach', 'default',
            'termination', 'renewal', 'amendment', 'assignment', 'sublease',
            'easement', 'encumbrance', 'lien', 'mortgage', 'foreclosure'
        ]

        text_lower = text.lower()
        found_keywords = []

        for term in legal_terms:
            if term in text_lower:
                found_keywords.append(term)

        return found_keywords[:10]  # Limit to top 10

    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text with improved break points"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to find a good break point
            if end < len(text):
                # Priority 1: Paragraph break
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break
                else:
                    # Priority 2: Sentence end with newline
                    sentence_newline = text.rfind('.\n', start, end)
                    if sentence_newline > start + self.chunk_size // 2:
                        end = sentence_newline + 1
                    else:
                        # Priority 3: Any sentence end
                        sentence_end = text.rfind('. ', start, end)
                        if sentence_end > start + self.chunk_size // 2:
                            end = sentence_end + 1
                        else:
                            # Priority 4: Any period
                            period = text.rfind('.', start, end)
                            if period > start + self.chunk_size // 2:
                                end = period + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def list_available_documents(self) -> List[Dict[str, Any]]:
        """List all available legal documents"""
        documents = []

        if not self.docs_path.exists():
            return documents

        for category in self.docs_path.iterdir():
            if category.is_dir():
                for doc_file in category.glob("*.md"):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    title = self._extract_title(content)

                    documents.append({
                        'title': title or doc_file.stem.replace('-', ' ').title(),
                        'category': category.name,
                        'filename': doc_file.name,
                        'size': doc_file.stat().st_size
                    })

        return documents

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown document"""
        # Look for # Title format
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1)

        # Look for title in first line
        lines = content.split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line and not first_line.startswith('#'):
                return first_line[:100]

        return None

    def _identify_document_type(self, content: str, filename: str) -> str:
        """Identify the type of legal document"""
        content_lower = content.lower()

        if 'lease' in content_lower or 'tenant' in content_lower or 'rent' in content_lower:
            return 'Lease Agreement'
        elif 'deed' in content_lower or 'title' in content_lower or 'grantor' in content_lower:
            return 'Property Deed'
        elif 'purchase' in content_lower or 'sale' in content_lower or 'buyer' in content_lower:
            return 'Purchase Contract'
        elif 'regulation' in content_lower or 'zoning' in content_lower or 'ordinance' in content_lower:
            return 'Regulation'
        else:
            return 'Legal Document'

    def _split_by_sections(self, text: str) -> List[str]:
        """Split legal document by numbered sections or articles"""
        patterns = [
            r'\n\s*(?:Section|SECTION|Article|ARTICLE)\s+\d+',
            r'\n\s*\d+\.\s+[A-Z]',
            r'\n\s*[A-Z]\.\s+[A-Z]'
        ]

        for pattern in patterns:
            sections = re.split(pattern, text)
            if len(sections) > 1:
                result = []
                matches = re.finditer(pattern, text)
                match_list = list(matches)

                if match_list:
                    if sections[0].strip():
                        result.append(sections[0])

                    for i, match in enumerate(match_list):
                        section_content = match.group() + (sections[i + 1] if i + 1 < len(sections) else '')
                        result.append(section_content)

                    return result

        return [text]

    def _create_sample_document(self, category_path: Path, category: str):
        """Create a sample legal document for demonstration"""
        # Note: This method is the same as in the original file
        # Including the full sample document creation logic
        # (Omitted here for brevity - use same implementation as original)
        pass
