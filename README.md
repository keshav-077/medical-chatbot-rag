# Medical Chatbot with RAG Architecture

An intelligent medical chatbot powered by Retrieval-Augmented Generation (RAG) using LangChain, OpenAI GPT, and Pinecone vector database. The chatbot provides accurate medical information by retrieving relevant context from medical literature.

## 🚀 Features

- **RAG Architecture**: Combines retrieval and generation for accurate responses
- **Medical Knowledge Base**: Trained on medical literature for domain-specific answers
- **Vector Search**: Uses Pinecone for efficient similarity search
- **Flask Web Interface**: Clean and intuitive chat interface
- **OpenAI Integration**: Leverages GPT models for natural language understanding
- **Docker Support**: Containerized deployment for easy scaling
- **CI/CD Pipeline**: Automated deployment with GitHub Actions

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **LLM Framework**: LangChain
- **Vector Database**: Pinecone
- **Language Model**: OpenAI GPT
- **Embeddings**: HuggingFace Transformers
- **Deployment**: Docker, AWS EC2, ECR
- **CI/CD**: GitHub Actions

## 📋 Prerequisites

- Python 3.10+
- Pinecone API Key
- OpenAI API Key
- Conda (recommended)

## 🔧 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/keshav-077/medical-chatbot-rag.git
cd medical-chatbot-rag
```

### Step 2: Create Conda Environment

```bash
conda create -n medibot python=3.10 -y
conda activate medibot
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory:

```ini
PINECONE_API_KEY=your_pinecone_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 5: Initialize Vector Database

```bash
python store_index.py
```

This command processes the medical documents and stores embeddings in Pinecone.

### Step 6: Run the Application

```bash
python app.py
```

Access the chatbot at `http://localhost:8080`

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t medical-chatbot .
```

### Run Container

```bash
docker run -p 8080:8080 --env-file .env medical-chatbot
```

## ☁️ AWS Deployment

### Prerequisites

1. AWS Account with IAM user
2. EC2 access
3. ECR (Elastic Container Registry) access

### Deployment Steps

1. **Create ECR Repository**
   - Save the repository URI

2. **Launch EC2 Instance** (Ubuntu)

3. **Install Docker on EC2**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker
```

4. **Configure GitHub Secrets**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`
   - `ECR_REPO`
   - `PINECONE_API_KEY`
   - `OPENAI_API_KEY`

5. **Setup Self-Hosted Runner**
   - Go to Settings > Actions > Runners
   - Follow the setup instructions

## 📁 Project Structure

```
├── app.py                 # Flask application
├── store_index.py         # Vector database initialization
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .dockerignore         # Docker ignore file
├── Data/                 # Medical documents
│   └── Medical_book.pdf
├── src/                  # Source code
│   ├── helper.py        # Utility functions
│   ├── prompt.py        # Prompt templates
│   └── __init__.py
├── static/              # CSS and assets
│   └── style.css
└── templates/           # HTML templates
    └── chat.html
```

## 🔍 How It Works

1. **Document Processing**: Medical documents are split into chunks and converted to embeddings
2. **Vector Storage**: Embeddings are stored in Pinecone for fast retrieval
3. **Query Processing**: User questions are embedded and similar chunks are retrieved
4. **Response Generation**: Retrieved context is passed to GPT for generating accurate answers
5. **Web Interface**: Flask serves the chat interface for user interaction

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Keshav**
- GitHub: [@keshav-077](https://github.com/keshav-077)

## 🙏 Acknowledgments

- LangChain for the RAG framework
- OpenAI for GPT models
- Pinecone for vector database
- HuggingFace for embeddings

---

⭐ Star this repository if you find it helpful!
