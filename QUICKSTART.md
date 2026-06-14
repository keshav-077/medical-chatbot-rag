# 🚀 Quick Start Guide

## For First-Time Setup (After Cloning from GitHub)

### Windows Users

1. **Open PowerShell in the project directory and run:**
   ```powershell
   .\setup_windows.ps1
   ```

2. **Add your API keys to `.env` file:**
   ```ini
   PINECONE_API_KEY=your_actual_pinecone_key
   OPENROUTER_API_KEY=your_actual_openrouter_key
   SECRET_KEY=any_random_string_here
   ```

3. **Initialize the vector database:**
   ```bash
   python store_index.py
   ```
   Wait for: `✅ Successfully stored embeddings in Pinecone!`

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open browser:** http://localhost:8080

---

## After Setup (Running Again)

If you've already set up once:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # PowerShell
# OR
venv\Scripts\activate.bat    # Command Prompt

# Run the app
python app.py
```

---

## Common First-Time Issues

### ❌ "Module not found" errors
**Fix:** Delete `venv` folder and run `.\setup_windows.ps1` again

### ❌ "Invalid API Key"
**Fix:** Check your `.env` file - ensure keys are copied completely with no extra spaces

### ❌ Port 8080 already in use
**Fix:** Kill existing process:
```powershell
netstat -ano | findstr :8080
taskkill /PID <process_id> /F
```

---

## What Gets Installed?

The setup script installs these key packages with **fixed versions** to prevent conflicts:

- ✅ `pinecone>=7.0.0,<8.0.0` (compatible version)
- ✅ `langchain-pinecone>=0.2.0,<0.3.0`
- ✅ `langchain-huggingface>=1.2.0`
- ✅ All gRPC dependencies (grpcio, protobuf, etc.)
- ✅ Flask and authentication libraries

**These versions are tested and working together!**

---

## Need Help?

- 📖 Full setup guide: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- 🐛 Troubleshooting: See "Common Issues" section in SETUP_GUIDE.md
- 📝 Main README: [README.md](README.md)

---

## Development Mode

To run with auto-reload:
```bash
# The app already runs in debug mode by default
python app.py
```

The server will automatically restart when you make code changes.
