# 🚀 Quick Start Guide - Legal Property Assistant

Get up and running in 5 minutes using the uv package manager!

## Prerequisites

- Python 3.8+
- OpenAI API key (or compatible endpoint)

## Installation Steps

### 1. Install uv Package Manager

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (with pip):**
```bash
pip install uv
```

### 2. Navigate to Project Directory

```bash
cd legal-assistant
```

### 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- OpenAI SDK (LLM integration)
- All other dependencies

### 4. Set Your API Key

**Option A: Environment Variable**

macOS/Linux:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**Option B: .env File**

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your key
# OPENAI_API_KEY=sk-your-api-key-here
```

### 5. Run the Application

**Option A: Use the run script (easiest)**

macOS/Linux:
```bash
./run.sh
```

Windows:
```bash
run.bat
```

**Option B: Run manually**

```bash
uv run app.py
```

Or:
```bash
python app.py
```

### 6. Open Your Browser

Navigate to: **http://localhost:5252**

## First Run

On first launch, the system will:
1. ✅ Create sample legal documents
2. ✅ Process documents into vector database
3. ✅ Start the web server
4. ✅ Open ready for your questions!

This takes about 30-60 seconds on first run.

## Try These Questions

Once the interface loads, try asking:

- "What are my obligations in a residential lease agreement?"
- "What should I look for in a property deed?"
- "Explain property purchase agreement contingencies"
- "What are the zoning regulations for residential properties?"
- "What are the key components of a warranty deed?"

## Using Your Own Documents

1. Add your legal documents to the appropriate folder:
   - `legal-docs/contracts/` - Purchase agreements
   - `legal-docs/deeds/` - Property deeds
   - `legal-docs/leases/` - Rental agreements
   - `legal-docs/regulations/` - Zoning laws

2. Documents should be in **Markdown (.md)** format

3. Restart the application:
   ```bash
   # Stop with Ctrl+C, then:
   rm -rf chroma_db/  # Clear old database
   uv run app.py      # Restart to reprocess
   ```

## Troubleshooting

### "uv: command not found"
Install uv package manager (see step 1 above)

### "OPENAI_API_KEY environment variable is not set"
Set your API key (see step 4 above)

### "Module not found" errors
Reinstall dependencies:
```bash
uv pip install -r requirements.txt --force-reinstall
```

### Model download taking too long
First-time setup downloads sentence-transformers model (~90MB). This is normal and only happens once.

### No documents found
Check that `legal-docs/` folder exists with subdirectories containing .md files

## API Configuration

### Using Different LLM Providers

**DeepSeek (default in code):**
```bash
export OPENAI_API_KEY="your-deepseek-api-key"
export OPENAI_API_BASE="https://api.deepseek.com/v1"
```

**OpenAI:**
```bash
export OPENAI_API_KEY="sk-your-openai-key"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

**Local LLM (Ollama):**
```bash
export OPENAI_API_KEY="not-needed"
export OPENAI_API_BASE="http://localhost:11434/v1"
```

Then edit `core/chat_engine.py` and change the model name.

## What's Next?

- 📖 Read the full [README.md](README.md) for detailed documentation
- 🔧 Customize the system prompt in `core/chat_engine.py`
- 📊 Adjust chunking parameters in `core/document_processor.py`
- 🎨 Modify the web interface in `templates/chat.html`

## Quick Commands Reference

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run application
uv run app.py

# Check installation
python setup.py

# Clear database and restart
rm -rf chroma_db/ && uv run app.py

# Update dependencies
uv pip install -r requirements.txt --upgrade
```

## Why uv?

uv is a blazingly fast Python package installer and resolver:
- ⚡ **10-100x faster** than pip
- 🔒 **Reliable** dependency resolution
- 💾 **Disk-efficient** with global cache
- 🔄 **Compatible** with pip and requirements.txt

Learn more: https://github.com/astral-sh/uv

---

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or full [README.md](README.md)

**Legal Notice:** This tool is for informational purposes only and does not constitute legal advice. Consult a qualified attorney for legal matters.