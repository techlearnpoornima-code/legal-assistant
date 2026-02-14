"""
Legal Assistant Core Module
"""

from .vector_engine import VectorEngine
from .chat_engine import ChatEngine
from .document_processor import DocumentProcessor
from .file_reader import FileReader

__all__ = ['VectorEngine', 'ChatEngine', 'DocumentProcessor', 'FileReader']