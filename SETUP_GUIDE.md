# Medical Chatbot RAG - Complete Setup Guide

## Quick Setup (Windows)

### Option 1: Using PowerShell (Recommended)
```powershell
.\setup_windows.ps1
```

### Option 2: Using Command Prompt
```cmd
setup_windows.bat
```

### Option 3: Manual Setup
Follow the steps below.

---

## Manual Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Git
- Pinecone account (free tier available)
- OpenRouter API account

### Step 1: Clone Repository
```bash
git clone https://github.com/keshav-077/medical-chatbot-rag.git
cd medical-chatbot-rag
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** The requirements.txt now includes pinned versions to avoid compatibility issues:
- `pinecone>=7.0.0,<8.0.0` (compatible version)
- `langchain-pinecone>=0.2.0,<0.3.0`
- All required gRPC dependencies

### Step 5: Set Up Environment Variables

1. Copy `.env.example` to `.env`:
```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

2. Edit `.env` and add your API keys:
```ini
PINECONE_API_KEY=your_pinecone_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
SECRET_KEY=your_secret_key_here_random_string
```

**Where to get API keys:**
- Pinecone API Key: https://app.pinecone.io → API Keys
- OpenRouter API Key: https://openrouter.ai/keys
- Secret Key: Generate a random string (e.g., using `openssl rand -hex 32`)

### Step 6: Initialize Vector Database
```bash
python store_index.py
```

This will:
- Load the medical PDF from `Data/` directory
- Split it into chunks
- Create embeddings using HuggingFace model
- Upload to Pinecone vector database

**Expected output:**
```
Loading and processing medical documents...
Extracted 5859 text chunks from documents
Loading embeddings model...
Creating new index 'medicalbot'...
✅ Successfully stored 5859 embeddings in Pinecone!
```

### Step 7: Run the Application
```bash
python app.py
```

### Step 8: Access the Application
Open your browser and navigate to: **http://localhost:8080**

---

## Common Issues and Solutions

### Issue 1: Module Import Errors
**Error:** `ModuleNotFoundError: No module named 'langchain_huggingface'`

**Solution:**
```bash
pip install langchain-huggingface
```

### Issue 2: Pinecone Version Conflicts
**Error:** `AttributeError: 'IndexList' object has no attribute 'index_list'`

**Solution:**
This is now fixed in the updated `requirements.txt`. If you still face this:
```bash
pip uninstall pinecone pinecone-client langchain-pinecone -y
pip install "pinecone>=7.0.0,<8.0.0" "langchain-pinecone>=0.2.0,<0.3.0"
```

### Issue 3: gRPC Dependencies Missing
**Error:** `ModuleNotFoundError: No module named 'google'`

**Solution:**
```bash
pip install grpcio grpcio-tools protobuf googleapis-common-protos
```

### Issue 4: Pinecone Authentication Error
**Error:** `[401] Invalid API Key`

**Solution:**
1. Verify your API key in `.env` file
2. Make sure you copied the complete API key from Pinecone dashboard
3. Check if the API key is active and not expired
4. Ensure no extra spaces in the `.env` file

### Issue 5: Port Already in Use
**Error:** `Address already in use`

**Solution:**
Either kill the existing process or change the port in `app.py`:
```bash
# Kill existing process on port 8080
netstat -ano | findstr :8080
taskkill /PID <process_id> /F

# Or change port in app.py (line at the bottom)
app.run(host="0.0.0.0", port=8081, debug=True)
```

### Issue 6: HuggingFace Rate Limit Warning
**Warning:** `You are sending unauthenticated requests to the HF Hub`

**Solution (Optional):**
Get a free HuggingFace token and add to `.env`:
```ini
HF_TOKEN=your_huggingface_token
```

---

## Dependency Version Compatibility

### Working Versions (Tested)
```
pinecone==7.3.0
langchain-pinecone==0.2.13
langchain==1.3.9
langchain-core==1.4.7
langchain-openai==1.3.2
sentence-transformers==5.5.1
flask==3.1.3
grpcio==1.81.1
protobuf==6.33.6
```

### Why These Versions?
- **Pinecone 7.x**: Compatible with `langchain-pinecone 0.2.x`
- **Pinecone 9.x**: Has breaking API changes causing `IndexList` errors
- **gRPC packages**: Required for Pinecone's gRPC features

---

## Fresh Installation Guide

If you're cloning from GitHub for the first time:

1. **Delete any existing virtual environment:**
```bash
rmdir /s /q venv  # Windows
rm -rf venv       # Linux/Mac
```

2. **Run the setup script:**
```powershell
.\setup_windows.ps1  # PowerShell
# OR
setup_windows.bat    # Command Prompt
```

3. **Add your API keys to `.env`**

4. **Initialize database and run:**
```bash
python store_index.py
python app.py
```

---

## Project Structure

```
medical-chatbot-rag/
├── app.py                      # Main Flask application
├── store_index.py              # Vector database initialization
├── models.py                   # Database models
├── requirements.txt            # Python dependencies (FIXED)
├── setup_windows.ps1           # PowerShell setup script
├── setup_windows.bat           # Batch setup script
├── SETUP_GUIDE.md             # This file
├── .env.example               # Environment variables template
├── .env                       # Your actual API keys (git ignored)
├── Data/
│   └── Medical_book.pdf       # Medical knowledge base
├── src/
│   ├── helper.py              # Utility functions
│   ├── prompt.py              # LLM prompts
│   └── __init__.py
├── templates/                 # HTML templates
│   ├── base.html
│   ├── chat.html
│   ├── login.html
│   ├── profile.html
│   └── signup.html
└── static/
    └── style.css              # Styles
```

---

## Features

- ✅ User authentication (signup/login/logout)
- ✅ Conversation history
- ✅ Medical knowledge retrieval from PDF
- ✅ RAG (Retrieval-Augmented Generation) architecture
- ✅ Vector similarity search using Pinecone
- ✅ Responsive web interface
- ✅ Profile management
- ✅ Password change functionality

---

## Technology Stack

- **Backend**: Flask, Python
- **LLM**: OpenRouter API (GPT models)
- **Embeddings**: HuggingFace Sentence Transformers
- **Vector DB**: Pinecone
- **Framework**: LangChain
- **Auth**: Flask-Login
- **Database**: SQLite (for users)

---

## Support

If you face any issues:
1. Check this guide first
2. Verify all API keys are correct
3. Ensure you're using compatible package versions
4. Check the GitHub issues page
5. Create a new issue with error logs

---

## License

MIT License - See LICENSE file for details
