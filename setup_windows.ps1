# Medical Chatbot Setup Script for Windows (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Medical Chatbot RAG - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping..." -ForegroundColor Gray
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/5] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "[3/5] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host ""
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host ".env file found!" -ForegroundColor Green
} else {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "Copying .env.example to .env..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "IMPORTANT: Please edit .env file and add your API keys:" -ForegroundColor Red
    Write-Host "  - PINECONE_API_KEY" -ForegroundColor Yellow
    Write-Host "  - OPENROUTER_API_KEY" -ForegroundColor Yellow
    Write-Host "  - SECRET_KEY" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env file with your API keys" -ForegroundColor White
Write-Host "  2. Run: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  3. Run: python store_index.py" -ForegroundColor White
Write-Host "  4. Run: python app.py" -ForegroundColor White
Write-Host "  5. Open: http://localhost:8080" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
