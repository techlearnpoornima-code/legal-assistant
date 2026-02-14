# Legal Property Assistant 📚⚖️

A sophisticated AI-powered Retrieval-Augmented Generation (RAG) system designed to help users understand property law documents, contracts, leases, and legal regulations. This system combines vector search with large language models to provide accurate, context-aware answers to legal questions.

---

## 📋 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [File Hierarchy](#file-hierarchy)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Adding Your Documents](#adding-your-documents)
- [Troubleshooting](#troubleshooting)
- [Legal Disclaimer](#legal-disclaimer)
- [Advanced Features](#advanced-features)

---

## ✨ Features

### Core Capabilities
- 🏛️ **Legal Document Analysis** - Process and analyze property deeds, contracts, leases, and regulations
- 🔍 **Semantic Search** - AI-powered vector search finds relevant legal information intelligently
- 💬 **Interactive Chat Interface** - Ask questions in natural language and get accurate answers
- 📊 **Source Citations** - See exactly which documents informed each answer
- 🎯 **Confidence Scoring** - Understand how reliable each answer is based on document relevance

### Document Categories
- 📄 **Property Purchase Contracts** - Purchase agreements, sales contracts, contingencies
- 📜 **Deeds and Titles** - Warranty deeds, quitclaim deeds, title documents
- 🏠 **Lease Agreements** - Residential leases, commercial leases, rental agreements
- 🏗️ **Zoning and Regulations** - Property laws, building codes, zoning ordinances

### AI Features
- **Context-Aware Responses** - Answers based on your specific legal documents
- **Legal Term Explanations** - Complex legal jargon explained in plain language
- **Risk Highlighting** - Identifies potential obligations, rights, and risks
- **Automatic Disclaimers** - Every response includes appropriate legal disclaimers

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Web Interface                       │
│                  (Flask + HTML/CSS/JS)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application                          │
│                      (app.py)                                │
└─────┬───────────────┬───────────────┬───────────────────────┘
      │               │               │
      ▼               ▼               ▼
┌──────────┐   ┌─────────────┐   ┌──────────────────┐
│  Vector  │   │    Chat     │   │    Document      │
│  Engine  │◄──┤   Engine    │◄──┤   Processor      │
└────┬─────┘   └─────────────┘   └──────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│           ChromaDB Vector Database                           │
│        (Stores document embeddings)                          │
└──────────────────────────────────────────────────────────────┘
```

### RAG Pipeline Flow

1. **Document Ingestion** → Documents are split into chunks and embedded
2. **Vector Storage** → Embeddings stored in ChromaDB for fast retrieval
3. **User Query** → Question submitted through web interface
4. **Retrieval** → Semantic search finds relevant document chunks
5. **Augmentation** → Context added to prompt with retrieved documents
6. **Generation** → LLM generates answer based on context
7. **Response** → Answer displayed with sources and confidence score

---

## 📁 File Hierarchy

```
legal-assistant/
│
├── 📄 app.py                          # Main Flask application entry point
│   ├── Routes: /, /api/chat, /api/status, /api/documents, /api/analyze
│   ├── Initializes RAG components
│   └── Handles HTTP requests and responses
│
├── 📁 core/                           # Core RAG system modules
│   │
│   ├── 📄 __init__.py                 # Package initializer
│   │
│   ├── 📄 vector_engine.py            # Vector database operations
│   │   ├── Class: VectorEngine
│   │   ├── Manages ChromaDB connection
│   │   ├── Handles document embeddings (SentenceTransformers)
│   │   ├── Methods:
│   │   │   ├── add_document()         # Add document to vector DB
│   │   │   ├── search()               # Semantic similarity search
│   │   │   ├── get_stats()            # Database statistics
│   │   │   ├── clear_collection()     # Reset database
│   │   │   └── is_initialized()       # Check if DB has data
│   │   └── Embedding Model: all-MiniLM-L6-v2 (384 dimensions)
│   │
│   ├── 📄 chat_engine.py              # RAG pipeline and LLM integration
│   │   ├── Class: ChatEngine
│   │   ├── Handles query-response pipeline
│   │   ├── Integrates with OpenAI API (or compatible)
│   │   ├── Methods:
│   │   │   ├── get_response()         # Main RAG pipeline
│   │   │   ├── analyze_legal_text()   # Analyze specific text
│   │   │   ├── _create_legal_context() # Format retrieved docs
│   │   │   └── _calculate_confidence() # Compute confidence score
│   │   ├── System Prompt: Legal-specific instructions
│   │   ├── Temperature: 0.3 (factual responses)
│   │   └── Max Tokens: 800
│   │
│   └── 📄 document_processor.py       # Document chunking and processing
│       ├── Class: DocumentProcessor
│       ├── Processes legal documents into chunks
│       ├── Methods:
│       │   ├── process_all_documents() # Batch process all docs
│       │   ├── process_document()      # Process single document
│       │   ├── _create_legal_chunks()  # Legal-aware chunking
│       │   ├── _split_by_sections()    # Detect legal sections
│       │   └── _create_sample_document() # Generate samples
│       ├── Chunk Size: 600 characters
│       ├── Chunk Overlap: 150 characters
│       └── Supports: Markdown (.md) files
│
├── 📁 templates/                      # HTML templates
│   │
│   └── 📄 chat.html                   # Web chat interface
│       ├── Responsive design with legal theme
│       ├── Real-time message handling
│       ├── Source citation display
│       ├── Example question suggestions
│       ├── Typing indicators
│       └── Confidence score badges
│
├── 📁 legal-docs/                     # Legal document repository
│   │
│   ├── 📁 contracts/                  # Purchase & sale agreements
│   │   └── 📄 sample-purchase-agreement.md
│   │       ├── Parties and property description
│   │       ├── Purchase price and payment terms
│   │       ├── Closing dates and procedures
│   │       ├── Title and inspection contingencies
│   │       └── Default remedies
│   │
│   ├── 📁 deeds/                      # Property deeds and titles
│   │   └── 📄 sample-warranty-deed.md
│   │       ├── Grantor and grantee information
│   │       ├── Legal property description
│   │       ├── Covenants and warranties
│   │       └── Appurtenant rights
│   │
│   ├── 📁 leases/                     # Rental and lease agreements
│   │   └── 📄 sample-residential-lease.md
│   │       ├── Lease terms and rent details
│   │       ├── Utilities and responsibilities
│   │       ├── Pet policies
│   │       ├── Maintenance obligations
│   │       └── Security deposit procedures
│   │
│   └── 📁 regulations/                # Laws and regulations
│       └── 📄 zoning-and-property-regulations.md
│           ├── Zoning classifications
│           ├── Building permit requirements
│           ├── Property maintenance standards
│           ├── Fence and structure regulations
│           └── Variance procedures
│
├── 📁 chroma_db/                      # Vector database storage (auto-created)
│   └── Persistent ChromaDB data
│
├── 📁 static/                         # Static assets (optional)
│   └── CSS, JavaScript, images
│
├── 📄 requirements.txt                # Python dependencies
│   ├── flask==3.0.0
│   ├── chromadb==0.4.22
│   ├── sentence-transformers==2.3.1
│   ├── openai==1.12.0
│   ├── numpy==1.26.3
│   └── werkzeug==3.0.1
│
├── 📄 setup.py                        # Quick setup script
│   ├── Checks Python version
│   ├── Installs dependencies
│   ├── Validates configuration
│   └── Creates directory structure
│
├── 📄 .env.example                    # Environment variables template
│   ├── OPENAI_API_KEY
│   └── OPENAI_API_BASE
│
├── 📄 .gitignore                      # Git ignore rules
│   ├── Python cache files
│   ├── Virtual environments
│   ├── ChromaDB data
│   └── Environment variables
│
└── 📄 README.md                       # This file
```

---

## 🔧 Prerequisites

### Required Software
- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (Python package manager - included with Python)
- **Git** (optional, for version control)

### Required API Access
- **OpenAI API Key** or compatible endpoint (DeepSeek, OpenRouter, local LLM)
  - Get OpenAI key: https://platform.openai.com/api-keys
  - Alternative: Use local models with Ollama or LM Studio

### System Requirements
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 500MB for dependencies + your documents
- **OS:** Windows 10/11, macOS 10.14+, or Linux

---

## 🚀 Installation & Setup

### Step 1: Download the Project

**Option A: Download ZIP**
```bash
# Extract the zip file to your desired location
cd path/to/legal-assistant
```

**Option B: Clone with Git**
```bash
git clone <repository-url>
cd legal-assistant
```

### Step 2: Create Virtual Environment

**On Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your command prompt
```

**On macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**Installation Progress:**
- This will download ~500MB of dependencies
- First time installation takes 5-10 minutes
- SentenceTransformers model (~90MB) downloads automatically on first run

### Step 4: Configure Environment Variables

**Option A: Create .env file** (Recommended)
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# For Windows, use: copy .env.example .env
```

Edit `.env` file:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
```

**Option B: Set environment variables directly**

On Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
```

On macOS/Linux:
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

### Step 5: Verify Installation (Optional)

Run the setup script to check everything:
```bash
python setup.py
```

This will verify:
- ✓ Python version
- ✓ Virtual environment
- ✓ Dependencies installed
- ✓ API key configured
- ✓ Directory structure

---

## 🎯 Running the Application

### Start the Server

```bash
# Make sure virtual environment is activated
# You can run it directly with Python (uses uvicorn internally):
uv run app.py

# OR use uvicorn directly (recommended for development):
uvicorn app:app --reload
```

**First Run Process:**
```
============================================================
🚀 Starting Legal Property Assistant
============================================================

[INIT] Loading RAG components...
[VectorEngine] Initializing ChromaDB...
[VectorEngine] Loading embedding model...
[VectorEngine] Note: First-time download may take 2-3 minutes (~90MB)
[VectorEngine] Model loaded successfully!
[INIT] Vector engine ready
[INIT] Chat engine ready
[INIT] Document processor ready

============================================================
First run detected. Processing legal documents...
============================================================

[DocumentProcessor] Clearing existing database...
[DocumentProcessor] Processing category: contracts
  ✓ sample-purchase-agreement.md (8 chunks)
[DocumentProcessor] Processing category: deeds
  ✓ sample-warranty-deed.md (6 chunks)
[DocumentProcessor] Processing category: leases
  ✓ sample-residential-lease.md (12 chunks)
[DocumentProcessor] Processing category: regulations
  ✓ zoning-and-property-regulations.md (15 chunks)

✓ Document processing complete!
  - Processed: 4 documents
  - Created: 41 chunks
============================================================

🚀 Legal Assistant is ready!
   Access at: http://localhost:5252
============================================================

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5252
```

### Access the Interface

1. **Open your web browser**
2. **Navigate to:** `http://localhost:5252`
3. **Start asking questions!**

### Stop the Server

Press `Ctrl + C` in the terminal

---

## 📖 Usage Guide

### Example Questions to Ask

**About Lease Agreements:**
```
- What are my obligations in a residential lease agreement?
- Can the landlord enter my apartment without notice?
- What happens if I need to break my lease early?
- What is covered under normal wear and tear?
```

**About Property Deeds:**
```
- What should I look for in a property deed?
- What is the difference between a warranty deed and quitclaim deed?
- What are appurtenant rights?
- What covenants are included in a general warranty deed?
```

**About Purchase Contracts:**
```
- Explain property purchase agreement contingencies
- What is earnest money and how does it work?
- What happens if the inspection reveals problems?
- What are my rights if the seller defaults?
```

**About Regulations:**
```
- What are the zoning regulations for residential properties?
- Do I need a permit to build a fence?
- What are the requirements for an accessory dwelling unit?
- What are the property maintenance standards?
```

### Understanding the Response

Each response includes:

1. **Answer** - AI-generated response based on your documents
2. **Sources** - Documents that informed the answer
   - Document title
   - Category
   - Relevance score (0-100%)
3. **Confidence Score** - How confident the system is
   - 🟢 High (70-100%) - Strong evidence in documents
   - 🟡 Medium (50-70%) - Moderate evidence
   - 🔴 Low (<50%) - Limited evidence
4. **Legal Disclaimer** - Reminder that this is informational only

---

## ⚙️ Configuration

### Adjusting Chunking Strategy

In `core/document_processor.py`:

```python
# Current settings
self.chunk_size = 600        # Characters per chunk
self.chunk_overlap = 150     # Overlap between chunks

# For longer context:
self.chunk_size = 1000       # Increase for more context
self.chunk_overlap = 200     # Increase overlap

# For shorter, more precise chunks:
self.chunk_size = 400        # Decrease for precision
self.chunk_overlap = 100     # Decrease overlap
```

### Adjusting Search Parameters

In `core/chat_engine.py`:

```python
# Number of documents to retrieve
relevant_docs = self.vector_engine.search(user_query, limit=5)
# Increase to 10 for more comprehensive answers

# LLM temperature (0.0 = factual, 1.0 = creative)
temperature=0.3
# Lower for more factual, higher for more creative

# Response length
max_tokens=800
# Increase for longer responses
```

### Changing LLM Model

In `core/chat_engine.py`, line ~75:

```python
# Current model
model="deepseek/deepseek-chat"

# Change to:
model="gpt-4"                    # OpenAI GPT-4
model="gpt-3.5-turbo"            # OpenAI GPT-3.5
model="claude-3-sonnet"          # Anthropic Claude (with appropriate endpoint)
model="llama-2-70b-chat"         # Open source (with local endpoint)
```

### Using Local LLMs

With Ollama or LM Studio:

```bash
# .env configuration
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=dummy-key-not-needed-for-local
```

Update model in `chat_engine.py`:
```python
model="llama2"  # or whatever model you have installed
```

---

## 📡 API Documentation

### POST /api/chat

Send a message and receive a response.

**Request:**
```json
{
  "message": "What are my lease obligations?"
}
```

**Response:**
```json
{
  "response": "Based on the residential lease agreement...",
  "sources": [
    {
      "id": "abc123_0",
      "title": "Residential Lease Agreement",
      "category": "leases",
      "score": 0.85,
      "snippet": "Tenant obligations include..."
    }
  ],
  "confidence": 0.87,
  "legal_disclaimer": "⚠️ LEGAL DISCLAIMER: ...",
  "timestamp": "2024-02-12T10:30:00"
}
```

### GET /api/status

Get system status and statistics.

**Response:**
```json
{
  "status": "operational",
  "documents": 4,
  "chunks": 41,
  "categories": ["contracts", "deeds", "leases", "regulations"],
  "last_updated": "2024-02-12T10:00:00"
}
```

### GET /api/documents

List all available documents.

**Response:**
```json
{
  "documents": [
    {
      "title": "Property Purchase Agreement",
      "category": "contracts",
      "filename": "sample-purchase-agreement.md",
      "size": 5432
    }
  ],
  "total": 4
}
```

### POST /api/analyze

Analyze specific legal text.

**Request:**
```json
{
  "text": "The tenant shall pay rent...",
  "type": "obligations"  // or "general", "risks"
}
```

**Response:**
```json
{
  "analysis": "This clause establishes the following obligations...",
  "timestamp": "2024-02-12T10:30:00"
}
```

---

## 📝 Adding Your Documents

### Step 1: Prepare Your Documents

Convert documents to Markdown (.md) format:

```markdown
# Title of Document

## Section 1: Introduction
Text of section 1...

## Section 2: Terms
Text of section 2...
```

**Supported Format:** Markdown (.md)
**Recommended:** Use clear section headers (##) for better chunking

### Step 2: Place in Correct Category

```
legal-docs/
├── contracts/      # Purchase agreements, sales contracts
├── deeds/          # Property deeds, title documents
├── leases/         # Rental agreements, lease contracts
└── regulations/    # Laws, codes, ordinances
```

### Step 3: Reprocess Documents

**Option A: Restart the application**
```bash
# Stop the server (Ctrl + C)
# Clear the database
rm -rf chroma_db/

# Restart
python app.py
```

**Option B: Use the processing function** (in Python console)
```python
from core.document_processor import DocumentProcessor
from core.vector_engine import VectorEngine

vector_engine = VectorEngine()
doc_processor = DocumentProcessor(vector_engine)
doc_processor.process_all_documents()
```

### Best Practices for Documents

1. **Use Clear Structure**
   - Start with # heading
   - Use ## for major sections
   - Use ### for subsections

2. **Legal Sections**
   - The system recognizes "Section 1:", "Article 1:", etc.
   - Numbered and lettered lists work well

3. **File Naming**
   - Use descriptive names: `residential-lease-2024.md`
   - Avoid special characters
   - Use hyphens instead of spaces

4. **Document Length**
   - No strict limit
   - Longer documents are automatically chunked
   - 2000-5000 words per document is optimal

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "OPENAI_API_KEY environment variable is not set"

**Solution:**
```bash
# Check if variable is set
echo $OPENAI_API_KEY  # macOS/Linux
echo %OPENAI_API_KEY%  # Windows CMD
$env:OPENAI_API_KEY    # Windows PowerShell

# Set the variable
export OPENAI_API_KEY="sk-..."  # macOS/Linux
$env:OPENAI_API_KEY="sk-..."    # Windows PowerShell
```

#### 2. "Module not found" errors

**Solution:**
```bash
# Verify virtual environment is activated
which python  # macOS/Linux (should show venv path)
where python  # Windows (should show venv path)

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 3. Model download takes too long

**Solution:**
```bash
# Download model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Or use cached model (if available)
export TRANSFORMERS_OFFLINE=1
```

#### 4. "Port 5252 already in use"

**Solution:**
```bash
# Option A: Kill the process
# On macOS/Linux:
lsof -ti:5252 | xargs kill -9

# On Windows:
netstat -ano | findstr :5252
taskkill /PID <PID> /F

# Option B: Change port in app.py
app.run(host='0.0.0.0', port=5000, debug=True)
```

#### 5. ChromaDB errors

**Solution:**
```bash
# Delete and recreate database
rm -rf chroma_db/  # macOS/Linux
rmdir /s chroma_db  # Windows

# Restart application
python app.py
```

#### 6. Poor answer quality

**Causes & Solutions:**
- ❌ Not enough relevant documents
  - ✅ Add more documents to the relevant category
- ❌ Documents not well-structured
  - ✅ Use clear section headers and formatting
- ❌ Question too vague
  - ✅ Be more specific in your question
- ❌ Low confidence score
  - ✅ Check if question matches available documents

#### 7. Slow responses

**Solutions:**
```bash
# Reduce number of retrieved documents
# In chat_engine.py, line ~50:
relevant_docs = self.vector_engine.search(user_query, limit=3)

# Reduce max tokens
# In chat_engine.py, line ~80:
max_tokens=500
```

### Debug Mode

Enable detailed logging:

```python
# In app.py, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## ⚠️ Legal Disclaimer

**IMPORTANT - READ CAREFULLY:**

This Legal Property Assistant is provided for **INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY**. 

### What This System IS:
- ✓ A tool to help understand legal documents
- ✓ A way to research property law topics
- ✓ An educational resource about legal concepts
- ✓ A document organization and search system

### What This System IS NOT:
- ❌ Legal advice
- ❌ A substitute for a licensed attorney
- ❌ Authorized to practice law
- ❌ Responsible for legal decisions you make

### Your Responsibilities:
1. **Consult an Attorney** for specific legal matters
2. **Verify Information** - Laws vary by jurisdiction
3. **Do Not Rely Solely** on AI-generated responses
4. **Understand Limitations** - AI can make mistakes
5. **Protect Privacy** - Don't upload confidential documents without authorization

### No Attorney-Client Relationship:
Using this system does NOT create an attorney-client relationship. The creators, developers, and operators of this system:
- Are not providing legal advice
- Make no warranties about accuracy
- Are not liable for your legal decisions
- Do not guarantee specific outcomes

**When in doubt, always consult with a qualified attorney licensed in your jurisdiction.**

---

## 🔐 Security & Privacy

### Data Privacy
- Documents are stored **locally** on your machine
- Vector database is **not shared** with any external service
- Only queries are sent to the LLM API (OpenAI, etc.)
- Consider data protection regulations (GDPR, CCPA, etc.)

### Best Practices
1. **Do NOT** upload client confidential documents without authorization
2. **Do NOT** include personally identifiable information (PII)
3. **Do** review documents before processing
4. **Do** use environment variables for API keys
5. **Do** keep your .env file secure and never commit it

### API Key Security
```bash
# NEVER commit .env file
echo ".env" >> .gitignore

# Use restricted API keys
# Set spending limits on OpenAI dashboard
# Rotate keys regularly
```

---

## 🚀 Advanced Features

### Custom Document Categories

Add new categories in `document_processor.py`:

```python
self.categories = {
    'contracts': 'Purchase and Sale Contracts',
    'deeds': 'Property Deeds and Titles',
    'leases': 'Lease Agreements',
    'regulations': 'Property Laws and Regulations',
    'disputes': 'Legal Disputes and Cases',  # NEW
    'financing': 'Mortgage and Financing'     # NEW
}
```

Create folders and restart:
```bash
mkdir legal-docs/disputes
mkdir legal-docs/financing
python app.py
```

### Batch Document Upload

```python
# scripts/batch_upload.py
from core.document_processor import DocumentProcessor
from core.vector_engine import VectorEngine
import os

vector_engine = VectorEngine()
doc_processor = DocumentProcessor(vector_engine)

# Process all .md files in a directory
for file in os.listdir('path/to/documents'):
    if file.endswith('.md'):
        doc_processor.process_document(file, 'category_name')
```

### Export Chat History

Add to `app.py`:

```python
@app.route('/api/export-chat', methods=['POST'])
def export_chat():
    data = request.json
    messages = data.get('messages', [])
    
    # Export to JSON
    with open('chat_export.json', 'w') as f:
        json.dump(messages, f, indent=2)
    
    return jsonify({'status': 'success'})
```

### Search by Category

```python
# In chat interface, add category filter
category = request.json.get('category', None)
relevant_docs = self.vector_engine.search(
    user_query, 
    limit=5,
    category_filter=category
)
```

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Multi-language support
- [ ] PDF document support
- [ ] Document comparison features
- [ ] Export to Word/PDF
- [ ] User authentication
- [ ] Document version tracking
- [ ] Advanced search filters
- [ ] Mobile app
- [ ] Voice input/output

---

## 📚 Additional Resources

### Learning Resources
- [RAG Systems Explained](https://www.anthropic.com/index/contextual-retrieval)
- [Vector Databases Guide](https://www.pinecone.io/learn/vector-database/)
- [Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)

### Related Projects
- **LangChain** - Framework for LLM applications
- **LlamaIndex** - Data framework for LLM apps
- **Haystack** - End-to-end NLP framework

### Support
- Check the [Troubleshooting](#troubleshooting) section
- Review configuration files
- Test with sample questions first
- Verify all dependencies are installed

---

## 📄 License

This project is provided as-is for educational purposes. See LICENSE file for details.

---

## 🙏 Acknowledgments

Built with:
- **Flask** - Web framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding models
- **OpenAI API** - Language models

---

## 📞 Contact & Support

For issues, questions, or contributions:
- Review this README thoroughly
- Check troubleshooting section
- Verify your configuration
- Test with provided sample documents

---

**Remember: This system provides information, not legal advice. Always consult qualified legal professionals for your specific legal needs.**

---

*Last Updated: February 2024*
*Version: 1.0.0*