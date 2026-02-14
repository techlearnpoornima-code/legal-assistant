"""
Legal Assistant - Interactive RAG Chat Interface for Property Law
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.vector_engine import VectorEngine
from core.chat_engine import ChatEngine
from core.document_processor import DocumentProcessor

# Load .env file
load_dotenv()

app = FastAPI(
    title="Legal Property Assistant",
    description="A sophisticated AI-powered RAG system for legal documents",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize RAG components globally (lazy loading pattern avoids startup issues)
vector_engine: Optional[VectorEngine] = None
chat_engine: Optional[ChatEngine] = None
doc_processor: Optional[DocumentProcessor] = None

def get_rag_components():
    global vector_engine, chat_engine, doc_processor
    
    if vector_engine is None:
        print("\n" + "="*60)
        print("⚖️  Starting Legal Property Assistant")
        print("="*60)
        print("\n[INIT] Loading RAG components...")
        
        vector_engine = VectorEngine(collection_name="legal_property_docs")
        print("[INIT] Vector engine ready")
        
        chat_engine = ChatEngine(vector_engine)
        print("[INIT] Chat engine ready")
        
        doc_processor = DocumentProcessor(vector_engine)
        print("[INIT] Document processor ready")
        
        # Check first run
        if not vector_engine.is_initialized():
            print("\n" + "="*60)
            print("First run detected. Processing legal documents...")
            print("="*60)
            try:
                result = doc_processor.process_all_documents()
                print(f"\n✓ Document processing complete!")
                print(f"  - Processed: {result['processed']} documents")
                print(f"  - Created: {result['chunks']} chunks")
            except Exception as e:
                print(f"Error processing documents on startup: {e}")
            print("="*60 + "\n")
            
    return vector_engine, chat_engine, doc_processor

# Startup event to initialize components
@app.on_event("startup")
async def startup_event():
    get_rag_components()

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class AnalyzeRequest(BaseModel):
    text: str
    type: str = "general"

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the chat interface"""
    print("\n" + "="*60)
    print("⚖️  Legal Property Assistant - Chat Interface")
    print("="*60)
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Handle chat messages"""
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        _, chat_engine, _ = get_rag_components()
        
        # Get response from RAG system
        response = chat_engine.get_response(request.message)
        
        return {
            'response': response['answer'],
            'sources': response['sources'],
            'confidence': response['confidence'],
            'legal_disclaimer': response.get('legal_disclaimer', ''),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Handle chat messages with streaming response"""
    
    async def generate():
        try:
            if not request.message:
                yield f"data: {json.dumps({'error': 'No message provided'})}\n\n"
                return
            
            _, chat_engine, _ = get_rag_components()
            
            # Send initial event
            yield f"data: {json.dumps({'event': 'start'})}\n\n"
            
            # Get response from RAG system - strict sync call might block event loop
            # Ideally this would be async, but for now we wrap it or run it
            # Since get_response is likely blocking, in a real production app we'd use run_in_executor
            # For simplicity here we just call it.
            response = chat_engine.get_response(request.message)
            
            # Stream the response word by word
            words = response['answer'].split()
            for i, word in enumerate(words):
                # Small delay for streaming effect simulation (not ideal for async but okay for demo)
                await asyncio.sleep(0.05) 
                yield f"data: {json.dumps({'event': 'token', 'content': word + ' '})}\n\n"
            
            # Send sources and disclaimer at the end
            yield f"data: {json.dumps({'event': 'sources', 'sources': response['sources'], 'confidence': response['confidence'], 'legal_disclaimer': response.get('legal_disclaimer', '')})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.get("/api/status")
async def status():
    """Get system status"""
    try:
        vector_engine, _, _ = get_rag_components()
        stats = vector_engine.get_stats()
        return {
            'status': 'operational',
            'documents': stats['total_documents'],
            'chunks': stats['total_chunks'],
            'last_updated': stats['last_updated'],
            'categories': stats.get('categories', [])
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'status': 'error',
                'message': str(e)
            }
        )

@app.get("/api/documents")
async def list_documents():
    """List all available legal documents"""
    try:
        _, _, doc_processor = get_rag_components()
        docs = doc_processor.list_available_documents()
        return {
            'documents': docs,
            'total': len(docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_document(request: AnalyzeRequest):
    """Analyze a specific legal document or clause"""
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No document text provided")
        
        _, chat_engine, _ = get_rag_components()
        
        # Get analysis from chat engine
        analysis = chat_engine.analyze_legal_text(request.text, request.type)
        
        return {
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Legal Property Assistant is running (FastAPI)!")
    print("Access at: http://localhost:8000")
    print("="*60)
    # Use reload=True for dev, remove for prod
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)