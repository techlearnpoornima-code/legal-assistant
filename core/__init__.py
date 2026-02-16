"""
Legal Assistant Core Module
"""

from .vector_engine import VectorEngineImproved as VectorEngine
from .chat_engine import ChatEngineImproved as ChatEngine
from .document_processor import DocumentProcessorImproved as DocumentProcessor
from .file_reader import FileReader as FileReader

__all__ = ['VectorEngine', 'ChatEngine', 'DocumentProcessor', 'FileReader']