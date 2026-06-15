<div align="center">

# 🏥 Medical Chatbot RAG

### *Intelligent Healthcare Assistant powered by Advanced AI*

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=00D9FF&center=true&vCenter=true&width=600&lines=Retrieval+Augmented+Generation;Medical+Knowledge+Base;Multi-LLM+Support;Serverless+Architecture;PostgreSQL+%2B+Pinecone+Vector+DB" alt="Typing SVG" />

---

## 🌐 **LIVE DEPLOYMENT**

<div style="font-size: 28px; font-weight: bold; margin: 20px 0;">
  
### 🚀 **[Try it Live on Vercel →](https://medical-chatbot-179320.vercel.app)**

</div>

[![Vercel](https://img.shields.io/badge/Vercel-Deployed-00D9FF?style=for-the-badge&logo=vercel&logoColor=white)](https://medical-chatbot-179320.vercel.app)
[![Status](https://img.shields.io/badge/Status-Online-brightgreen?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## 📸 **Application Screenshots**

<table>
  <tr>
    <td align="center">
      <img src="screenshots/screenshot1.png" alt="Chat Interface" width="400px" />
      <br />
      <sub><b>💬 Interactive Chat Interface</b></sub>
    </td>
    <td align="center">
      <img src="screenshots/screenshot2.png" alt="Medical Response" width="400px" />
      <br />
      <sub><b>🩺 Medical Q&A in Action</b></sub>
    </td>
  </tr>
</table>

> **Note:** Add your screenshots to a `screenshots/` folder in the root directory

---

## ✨ **Key Features**

<div align="left">

```diff
+ 🧠 RAG Architecture - Retrieval-Augmented Generation for accurate medical responses
+ 🔐 User Authentication - Secure login/signup with Flask-Login & Bcrypt
+ 💾 PostgreSQL Database - Serverless-ready with Neon integration
+ 🎯 Multi-LLM Support - OpenRouter (GPT) → Groq fallback
+ 🌐 Pinecone Vector DB - Lightning-fast similarity search
+ 📊 Conversation History - Save & load chat sessions
+ 🚀 Serverless Deploy - Vercel + AWS EC2 compatible
+ 🔄 API-Based Embeddings - Jina AI → HuggingFace fallback
+ ⚡ Rate Limiting - Built-in protection with Flask-Limiter
+ 🎨 Responsive UI - Modern chat interface with dark mode support
```

</div>

---

## 🛠️ **Tech Stack**

<div align="center">

### **Backend & AI**
![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI_GPT-412991?style=for-the-badge&logo=openai&logoColor=white)

### **Databases**
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)

### **Deployment**
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![AWS](https://img.shields.io/badge/AWS_EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

</div>

---

</div>

<div align="center">

## 📋 **Prerequisites**

</div>

| Requirement | Version | Get It |
|------------|---------|--------|
| 🐍 **Python** | 3.10+ | [Download](https://www.python.org/downloads/) |
| 🔑 **Pinecone API** | Latest | [Sign Up](https://app.pinecone.io) |
| 🤖 **OpenRouter API** | Latest | [Get Key](https://openrouter.ai/keys) |
| 🎯 **Jina AI API** | Latest | [Dashboard](https://jina.ai/) |
| 🗃️ **Neon PostgreSQL** | Latest | [Create DB](https://console.neon.tech) |

---

<div align="center">

## 🚀 **Quick Start**

</div>

### **Option 1: Automated Setup (Recommended)**

<details open>
<summary><b>🪟 Windows</b></summary>

**PowerShell:**
```powershell
.\setup_windows.ps1
```

**Command Prompt:**
```cmd
setup_windows.bat
```

</details>

<details>
<summary><b>🐧 Linux / macOS</b></summary>

```bash
chmod +x setup.sh
./setup.sh
```

</details>

---

### **Option 2: Manual Setup**

<details>
<summary><b>📦 Step-by-Step Installation</b></summary>

#### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/keshav-077/medical-chatbot-rag.git
cd medical-chatbot-rag
```

#### **2️⃣ Create Virtual Environment**

**Using venv:**
```bash
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

**Or using Conda:**
```bash
conda create -n medibot python=3.10 -y
conda activate medibot
```

#### **3️⃣ Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### **4️⃣ Configure Environment Variables**

```bash
# Copy example file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

**Edit `.env` and add your credentials:**

```ini
# === REQUIRED ===
PINECONE_API_KEY=your-pinecone-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
SECRET_KEY=your-random-secret-key

# === EMBEDDINGS (at least one) ===
JINA_API_KEY=your-jina-api-key
HUGGINGFACE_API_KEY=your-huggingface-token

# === DATABASE (for production) ===
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# === OPTIONAL ===
GROQ_API_KEY=your-groq-api-key
FLASK_ENV=development
APP_URL=http://localhost:8080
```

#### **5️⃣ Initialize Vector Database**

```bash
python store_index.py
```

This processes medical documents and creates embeddings in Pinecone.

#### **6️⃣ Run the Application**

```bash
python app.py
```

🎉 **Access at:** `http://localhost:8080`

</details>

---

<div align="center">

## 🐳 **Docker Deployment**

</div>

<details>
<summary><b>🔧 Build & Run with Docker</b></summary>

### **Build Image**

```bash
docker build -t medical-chatbot-rag .
```

### **Run Container**

```bash
docker run -p 8080:8080 --env-file .env medical-chatbot-rag
```

### **Docker Compose (Recommended)**

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    restart: unless-stopped
```

```bash
docker-compose up -d
```

</details>

---

<div align="center">

## ☁️ **Deployment Options**

</div>

### **🟢 Option 1: Vercel (Recommended - Serverless)**

<details open>
<summary><b>📦 Deploy to Vercel</b></summary>

#### **Prerequisites**
- GitHub account connected to Vercel
- Neon PostgreSQL database (free tier)
- All API keys ready

#### **Steps**

1. **Fork/Push this repo to GitHub**

2. **Go to [Vercel Dashboard](https://vercel.com/new)**

3. **Import your repository**

4. **Add Environment Variables:**

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | Your Neon PostgreSQL connection string |
   | `PINECONE_API_KEY` | Your Pinecone API key |
   | `OPENROUTER_API_KEY` | Your OpenRouter API key |
   | `JINA_API_KEY` | Your Jina API key |
   | `HUGGINGFACE_API_KEY` | Your HuggingFace token |
   | `GROQ_API_KEY` | Your Groq API key |
   | `SECRET_KEY` | Random secret key |
   | `FLASK_ENV` | `production` |

5. **Deploy!** 🚀

> **✅ Live Demo:** [https://medical-chatbot-179320.vercel.app](https://medical-chatbot-179320.vercel.app)

#### **Important Files for Vercel:**
- `vercel.json` - Routing configuration
- `api/index.py` - Serverless entry point
- `requirements.txt` - Python dependencies

</details>

---

### **🟠 Option 2: AWS EC2 + ECR (Traditional Hosting)**

<details>
<summary><b>☁️ AWS Deployment Guide</b></summary>

#### **Prerequisites**

- AWS Account with IAM user
- EC2 instance access
- ECR (Elastic Container Registry) access
- GitHub repository with self-hosted runner

---

#### **Deployment Steps**

**1️⃣ Create ECR Repository**

```bash
aws ecr create-repository --repository-name medical-chatbot-rag
```

Save the repository URI (e.g., `123456789.dkr.ecr.us-east-1.amazonaws.com/medical-chatbot-rag`)

**2️⃣ Launch EC2 Instance**

- **AMI:** Ubuntu 22.04 LTS
- **Instance Type:** t2.medium (or larger)
- **Security Group:** Allow ports 22 (SSH), 80 (HTTP), 8080 (App)

**3️⃣ Install Docker on EC2**

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker
```

**4️⃣ Configure GitHub Secrets**

Go to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key |
| `AWS_DEFAULT_REGION` | `us-east-1` (or your region) |
| `ECR_REPO` | Your ECR repository URI |
| `PINECONE_API_KEY` | Your Pinecone API key |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `JINA_API_KEY` | Your Jina API key |

**5️⃣ Setup Self-Hosted Runner**

On your EC2 instance:
- Go to **GitHub Repo → Settings → Actions → Runners → New self-hosted runner**
- Follow the setup instructions for Linux

**6️⃣ Push to GitHub**

The GitHub Actions workflow will automatically:
- Build the Docker image
- Push to ECR
- Deploy to EC2

**7️⃣ Access Your App**

```
http://your-ec2-public-ip:8080
```

</details>

---

<div align="center">

## � **Project Architecture**

</div>

```
medical-chatbot-rag/
│
├── 📄 app.py                      # Main Flask application
├── 📄 config.py                   # Environment-based configuration
├── 📄 models.py                   # Database models (User, Conversation, Message)
├── 📄 store_index.py              # Vector DB initialization script
├── 📄 requirements.txt            # Python dependencies
├── 📄 vercel.json                 # Vercel deployment config
├── 📄 Dockerfile                  # Docker image configuration
│
├── 📁 api/
│   └── 📄 index.py               # Vercel serverless entry point
│
├── 📁 src/
│   ├── 📄 embeddings.py          # API-based embeddings (Jina/HF)
│   ├── 📄 llm_providers.py       # Multi-LLM manager (OpenRouter/Groq)
│   ├── 📄 helper.py              # PDF processing utilities
│   └── 📄 prompt.py              # System prompts for RAG
│
├── 📁 templates/
│   ├── 📄 base.html              # Base template
│   ├── 📄 chat.html              # Chat interface
│   ├── 📄 login.html             # Login page
│   ├── 📄 signup.html            # Signup page
│   └── 📄 profile.html           # User profile
│
├── 📁 static/
│   └── 📄 style.css              # Styles & animations
│
├── 📁 Data/
│   └── 📄 Medical_book.pdf       # Medical knowledge base
│
└── 📁 instance/
    └── 📄 medical_chatbot.db     # SQLite (dev only)
```

---

<div align="center">

## 🔍 **How It Works**

</div>

```mermaid
graph LR
    A[User Query] --> B[Embedding API]
    B --> C[Pinecone Vector Search]
    C --> D[Top-K Similar Docs]
    D --> E[LLM Context]
    E --> F[Generated Response]
    F --> G[User]
    
    style A fill:#4CAF50
    style F fill:#2196F3
    style C fill:#FF9800
```

### **RAG Pipeline**

1. **📚 Document Ingestion**
   - Medical PDFs are split into chunks (500 chars, 50 overlap)
   - Text is cleaned and preprocessed

2. **🧮 Embedding Generation**
   - Chunks → Jina AI embeddings (768 dims)
   - Fallback to HuggingFace if Jina fails

3. **💾 Vector Storage**
   - Embeddings stored in Pinecone
   - Index: `medicalbot` with cosine similarity

4. **🔎 Query Processing**
   - User question → embedding
   - Similarity search retrieves top-3 relevant chunks

5. **🤖 Response Generation**
   - Context + Query → OpenRouter GPT
   - Fallback to Groq if primary fails

6. **💬 User Interface**
   - Flask serves responsive chat UI
   - Conversation history saved in PostgreSQL

---

<div align="center">

## 🐛 **Troubleshooting**

</div>

<details>
<summary><b>❌ Common Issues & Solutions</b></summary>

### **Issue 1: Pinecone Version Conflicts**

```bash
# Error: incompatible pinecone version
pip uninstall pinecone pinecone-client langchain-pinecone -y
pip install -r requirements.txt
```

### **Issue 2: gRPC/Protobuf Errors**

```bash
pip install --upgrade grpcio grpcio-tools protobuf googleapis-common-protos
```

### **Issue 3: Pinecone Authentication Failed**

- Verify API key in `.env` (no extra spaces or quotes)
- Check key is active in [Pinecone Dashboard](https://app.pinecone.io)
- Ensure index name is `medicalbot`

### **Issue 4: Database Connection Error (Vercel)**

```bash
# Vercel shows: Read-only file system error
# Solution: Add DATABASE_URL to Vercel environment variables
# Use Neon PostgreSQL with -pooler endpoint
```

### **Issue 5: Embedding API Timeouts**

```python
# src/embeddings.py already includes fallback logic:
# Jina AI → HuggingFace → Error
# Check both API keys are valid
```

### **Issue 6: Module Import Errors**

```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### **Issue 7: Port Already in Use**

```bash
# Find and kill process on port 8080
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8080 | xargs kill -9
```

</details>

<details>
<summary><b>📖 Additional Resources</b></summary>

- 📘 [Setup Guide](SETUP_GUIDE.md) - Detailed installation instructions
- 📙 [Documentation](DOCUMENTATION.md) - API & architecture docs
- 📕 [Changelog](CHANGELOG.md) - Version history
- 📗 [Quick Start](QUICKSTART.md) - Get running in 5 minutes

</details>

---

<div align="center">

## 🎯 **API Endpoints**

</div>

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/health` | Health check & system status | ❌ |
| `GET` | `/` | Chat interface | ✅ |
| `POST` | `/login` | User authentication | ❌ |
| `POST` | `/signup` | Create new account | ❌ |
| `GET` | `/logout` | Logout user | ✅ |
| `POST` | `/get` | Send message & get AI response | ✅ |
| `POST` | `/new-chat` | Create new conversation | ✅ |
| `GET` | `/load-chat/<id>` | Load conversation history | ✅ |
| `POST` | `/delete-chat/<id>` | Delete conversation | ✅ |
| `GET` | `/get-conversations` | List all conversations | ✅ |
| `GET` | `/profile` | User profile page | ✅ |
| `POST` | `/change-password` | Update password | ✅ |

---

## 🔐 **Environment Variables**

<details>
<summary><b>📝 Complete .env Reference</b></summary>

```ini
# ============================================================
# REQUIRED API KEYS
# ============================================================

# Pinecone Vector Database
PINECONE_API_KEY=your-pinecone-api-key

# OpenRouter (Primary LLM)
OPENROUTER_API_KEY=your-openrouter-api-key

# Flask Secret Key (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-random-secret-key

# ============================================================
# EMBEDDINGS (at least one required)
# ============================================================

# Jina AI (Primary - 768 dims, 10M free tokens/month)
JINA_API_KEY=your-jina-api-key

# HuggingFace (Fallback - 768 dims, free)
HUGGINGFACE_API_KEY=your-huggingface-token

# ============================================================
# DATABASE
# ============================================================

# Development: Uses SQLite (automatic)
# Production: Use Neon PostgreSQL
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# ============================================================
# OPTIONAL
# ============================================================

# Groq (LLM Fallback - 30 req/min free)
GROQ_API_KEY=your-groq-api-key

# Environment Mode
FLASK_ENV=development  # or 'production'

# Application URL
APP_URL=http://localhost:8080

# Rate Limiting (use Upstash Redis for production)
RATELIMIT_STORAGE_URI=memory://  # or redis://...
```

</details>

---

## 🤝 **Contributing**

<div align="center">

Contributions are welcome! Feel free to open issues or submit pull requests.

### **Development Workflow**

```bash
# 1. Fork & clone
git clone https://github.com/YOUR_USERNAME/medical-chatbot-rag.git

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make changes & commit
git commit -m "Add amazing feature"

# 4. Push & create PR
git push origin feature/amazing-feature
```

[![Contributors](https://img.shields.io/github/contributors/keshav-077/medical-chatbot-rag?style=for-the-badge)](https://github.com/keshav-077/medical-chatbot-rag/graphs/contributors)

</div>

---

## 📄 **License**

<div align="center">

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

## �‍💻 **Author**

<div align="center">

### **Keshav Ardhan**

[![GitHub](https://img.shields.io/badge/GitHub-keshav--077-181717?style=for-the-badge&logo=github)](https://github.com/keshav-077)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/your-profile)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:your-email@example.com)

</div>

---

## 🙏 **Acknowledgments**

<div align="center">

| Technology | Purpose |
|------------|---------|
| [LangChain](https://langchain.com) | RAG framework & orchestration |
| [OpenRouter](https://openrouter.ai) | Multi-LLM gateway |
| [Pinecone](https://pinecone.io) | Vector database |
| [Jina AI](https://jina.ai) | Embedding API |
| [Groq](https://groq.com) | Fast LLM inference |
| [Neon](https://neon.tech) | Serverless PostgreSQL |
| [Vercel](https://vercel.com) | Serverless hosting |

</div>

---

<div align="center">

### ⭐ **If you found this helpful, please star the repository!**

![Star History](https://img.shields.io/github/stars/keshav-077/medical-chatbot-rag?style=social)

---

**Made with ❤️ by [Keshav](https://github.com/keshav-077)**

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=14&duration=3000&pause=1000&color=808080&center=true&vCenter=true&width=400&lines=Thanks+for+visiting!;Happy+Coding+%F0%9F%9A%80" alt="Footer" />

</div>
