# Medical Chatbot with RAG - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [System Components](#system-components)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Installation Guide](#installation-guide)
9. [Configuration](#configuration)
10. [Deployment](#deployment)
11. [Security](#security)
12. [File Structure](#file-structure)
13. [Development Guide](#development-guide)

---

## Project Overview

The Medical Chatbot is an AI-powered conversational assistant that provides accurate medical information using **Retrieval-Augmented Generation (RAG)** architecture. It combines the power of vector databases, large language models, and medical literature to deliver evidence-based responses to medical queries.

### Key Capabilities
- Answers medical questions based on a curated knowledge base
- Maintains conversation history with multi-session support
- User authentication and profile management
- Real-time chat interface with responsive design
- Conversation management (create, load, delete)
- Secure password handling with bcrypt encryption

---

## Architecture

### High-Level Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   User      │◄────►│  Flask App   │◄────►│   Database   │
│  Browser    │      │  (Backend)   │      │  (SQLite)    │
└─────────────┘      └──────┬───────┘      └──────────────┘
                            │
                            │
                   ┌────────┴────────┐
                   │                 │
            ┌──────▼──────┐   ┌─────▼──────┐
            │  Pinecone   │   │ OpenRouter │
            │  (Vectors)  │   │   (LLM)    │
            └─────────────┘   └────────────┘
```

### RAG Pipeline Flow

```
User Query
    │
    ▼
┌──────────────────────────────────────────┐
│ 1. Query Embedding                       │
│    (HuggingFace sentence-transformers)   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 2. Vector Search (Top 3 Similar Chunks)  │
│    (Pinecone - Cosine Similarity)        │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 3. Context Retrieval                     │
│    (Retrieved medical text chunks)       │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 4. Prompt Construction                   │
│    System Prompt + Context + User Query  │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 5. LLM Generation                        │
│    (GPT via OpenRouter API)              │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 6. Response + Save to Database           │
└──────────────────────────────────────────┘
```

### Component Interaction

- **Frontend (HTML/CSS/JS)**: User interface with AJAX-based messaging
- **Backend (Flask)**: Request handling, authentication, business logic
- **Database (SQLite)**: User data, conversations, messages
- **Embeddings (HuggingFace)**: Convert text to 384-dimensional vectors
- **Vector Store (Pinecone)**: Similarity search over medical documents
- **LLM (OpenRouter)**: Generate responses using GPT models

---

## Features

### 1. User Authentication
- **Sign Up**: Create new account with email and password
- **Login**: Session-based authentication with "Remember Me" option
- **Logout**: Secure session termination
- **Password Management**: Change password with current password verification
- **Profile Page**: View user information and account details

### 2. RAG-Powered Medical Q&A
- **Context-Aware Responses**: Retrieves relevant medical text before generating answers
- **Vector Similarity Search**: Uses Pinecone to find top 3 most relevant document chunks
- **Embeddings**: Sentence-transformers model (all-MiniLM-L6-v2) for semantic search
- **LLM Generation**: GPT model via OpenRouter for natural language responses
- **Concise Answers**: Configured to provide 3-sentence maximum responses

### 3. Conversation Management
- **Multi-Session Support**: Create and manage multiple conversations
- **Auto-Save**: Messages automatically saved to database
- **Conversation History**: Load previous conversations with full message history
- **Delete Conversations**: Remove unwanted conversation threads
- **Auto-Titling**: First message becomes the conversation title
- **Date Grouping**: Conversations grouped by Today, Yesterday, Last 7 Days, Older

### 4. Real-Time Chat Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Loading Indicators**: Shimmer effect during AI response generation
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Auto-Scroll**: Automatically scrolls to latest message
- **Sidebar Navigation**: Easy access to conversation history
- **Empty State**: Helpful placeholder when starting new conversation

### 5. Security Features
- **Password Hashing**: Bcrypt encryption for secure password storage
- **XSS Prevention**: HTML escaping for all user inputs and outputs
- **Session Management**: HTTP-only cookies with SameSite protection
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Environment Variables**: Sensitive keys stored in .env file
- **CSRF Protection**: Secure form submissions

---

## Technology Stack

### Backend
- **Python 3.10+**: Core programming language
- **Flask**: Web framework for API and routing
- **Flask-Login**: User session management
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Bcrypt**: Password hashing and verification

### AI/ML Stack
- **LangChain**: RAG pipeline orchestration framework
- **LangChain-OpenAI**: OpenAI/OpenRouter integration
- **LangChain-Pinecone**: Vector store integration
- **LangChain-Community**: Document loaders (PyPDF)
- **Sentence-Transformers**: Text embeddings (all-MiniLM-L6-v2, 384 dimensions)
- **OpenRouter API**: LLM access (GPT-OSS-120B model)
- **Pinecone**: Serverless vector database (AWS us-east-1)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Styling with animations and responsive design
- **JavaScript (jQuery)**: AJAX requests and DOM manipulation
- **Font Awesome**: Icon library

### Database
- **SQLite**: Relational database for user and conversation data

### DevOps
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline (implied from README)
- **AWS EC2**: Cloud hosting
- **AWS ECR**: Container registry

---

## System Components

### 1. Flask Application (`app.py`)

**Purpose**: Main application entry point

**Key Responsibilities**:
- Initialize Flask app and extensions (SQLAlchemy, Bcrypt, LoginManager)
- Configure RAG pipeline (embeddings, vector store, LLM, retriever)
- Define routes for authentication, chat, and conversation management
- Handle AJAX requests for real-time chat
- Manage database sessions and error handling

**Configuration**:
```python
# Security
SECRET_KEY: Flask session encryption key
SESSION_COOKIE_HTTPONLY: True (prevent JavaScript access)
SESSION_COOKIE_SAMESITE: 'Lax' (CSRF protection)

# Database
SQLALCHEMY_DATABASE_URI: 'sqlite:///medical_chatbot.db'
SQLALCHEMY_TRACK_MODIFICATIONS: False

# RAG Components
- Embeddings: sentence-transformers/all-MiniLM-L6-v2
- Vector Store: Pinecone index "medicalbot"
- Retriever: Top 3 similar documents (cosine similarity)
- LLM: openai/gpt-oss-120b:free via OpenRouter
  - Temperature: 0.4 (balanced creativity)
  - Max Tokens: 500
```

### 2. Database Models (`models.py`)

**Purpose**: Define database schema and relationships

**Models**:

#### User Model
```python
- id: Primary key (Integer)
- name: User's full name (String, 100 chars)
- email: Unique email address (String, 120 chars)
- password_hash: Bcrypt hashed password (String, 200 chars)
- created_at: Account creation timestamp
- last_login: Last login timestamp
- conversations: One-to-many relationship with Conversation

Methods:
- set_password(password): Hash and store password
- check_password(password): Verify password against hash
```

#### Conversation Model
```python
- id: Primary key (Integer)
- user_id: Foreign key to User (Integer)
- title: Conversation title (String, 200 chars)
- created_at: Creation timestamp
- updated_at: Last update timestamp
- messages: One-to-many relationship with Message

Cascade: Delete all messages when conversation is deleted
```

#### Message Model
```python
- id: Primary key (Integer)
- conversation_id: Foreign key to Conversation (Integer)
- content: Message text (Text, unlimited)
- is_user: True for user, False for assistant (Boolean)
- timestamp: Message creation time

Cascade: Automatically deleted when parent conversation is deleted
```

### 3. Helper Functions (`src/helper.py`)

**Purpose**: Document processing and embedding utilities

**Functions**:

#### `load_pdf_file(data)`
- Loads all PDF files from specified directory
- Uses PyPDFLoader from LangChain
- Returns: List of Document objects

```python
# Example usage
documents = load_pdf_file(data='Data/')
```

#### `text_split(extracted_data)`
- Splits documents into smaller chunks for embedding
- Uses RecursiveCharacterTextSplitter
- Configuration:
  - chunk_size: 500 characters
  - chunk_overlap: 20 characters (maintains context between chunks)
- Returns: List of text chunks

#### `download_hugging_face_embeddings()`
- Initializes HuggingFace embedding model
- Model: sentence-transformers/all-MiniLM-L6-v2
- Returns: 384-dimensional embeddings
- Used for both indexing and query embedding

### 4. Prompt Template (`src/prompt.py`)

**Purpose**: Define system prompts for the LLM

**System Prompt**:
```
You are an assistant for question-answering tasks. Use the following pieces 
of retrieved context to answer the question. If you don't know the answer, 
say that you don't know. Use three sentences maximum and keep the answer concise.

{context}
```

**Role**: Instructs the LLM to:
- Stay factual and use retrieved context
- Admit when information is not available
- Keep responses concise (max 3 sentences)
- Context is injected dynamically from vector retrieval

### 5. Vector Store Initialization (`store_index.py`)

**Purpose**: Process medical documents and create Pinecone index

**Process Flow**:
1. Load PDF files from `Data/` directory
2. Split documents into 500-character chunks with 20-char overlap
3. Generate embeddings using HuggingFace model
4. Check if Pinecone index exists
5. Create index if needed:
   - Name: "medicalbot"
   - Dimension: 384 (matches embedding model)
   - Metric: cosine similarity
   - Cloud: AWS, Region: us-east-1
6. Upsert embeddings and metadata to Pinecone
7. Index ready for similarity search

**Configuration**:
```python
Index Name: medicalbot
Dimension: 384
Metric: cosine
Spec: Serverless (AWS, us-east-1)
```

**Usage**: Run once during initial setup or when updating medical documents
```bash
python store_index.py
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────┐
│       User          │
├─────────────────────┤
│ id (PK)             │
│ name                │
│ email (UNIQUE)      │
│ password_hash       │
│ created_at          │
│ last_login          │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│   Conversation      │
├─────────────────────┤
│ id (PK)             │
│ user_id (FK)        │
│ title               │
│ created_at          │
│ updated_at          │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│      Message        │
├─────────────────────┤
│ id (PK)             │
│ conversation_id (FK)│
│ content             │
│ is_user             │
│ timestamp           │
└─────────────────────┘
```

### Cascade Behavior
- Deleting a User → Deletes all Conversations → Deletes all Messages
- Deleting a Conversation → Deletes all associated Messages

---

## API Endpoints

### Authentication Endpoints

#### `GET/POST /login`
**Purpose**: User login

**Methods**: GET (show form), POST (process login)

**POST Parameters**:
- `email`: User's email address
- `password`: User's password
- `remember`: Optional, "remember me" checkbox

**Response**:
- Success: Redirect to chat page or `next` parameter
- Failure: Flash error message and reload login page

**Security**: Updates `last_login` timestamp on success

---

#### `GET/POST /signup`
**Purpose**: New user registration

**Methods**: GET (show form), POST (process signup)

**POST Parameters**:
- `name`: User's full name (min 2 chars)
- `email`: Valid email address (must be unique)
- `password`: Password (min 6 chars)
- `confirm_password`: Password confirmation

**Validation**:
- Name length check
- Email format validation (regex)
- Password length check
- Password match verification
- Email uniqueness check

**Response**:
- Success: Redirect to login with success message
- Failure: Flash error message and reload signup page

---

#### `GET /logout`
**Purpose**: Log out current user

**Authentication**: Required (@login_required)

**Response**: Redirect to login page

---

#### `GET /profile`
**Purpose**: Display user profile page

**Authentication**: Required

**Template**: `profile.html`

**Data**: Current user information

---

#### `POST /change-password`
**Purpose**: Update user password

**Authentication**: Required

**POST Parameters**:
- `current_password`: Current password for verification
- `new_password`: New password (min 6 chars)
- `confirm_new_password`: Confirmation of new password

**Validation**:
- Verify current password
- Check new passwords match
- Enforce minimum length

**Response**: Redirect to profile with flash message

---

### Chat Endpoints

#### `GET /`
**Purpose**: Main chat interface

**Authentication**: Required

**Template**: `chat.html`

**Features**: Responsive UI with sidebar, chat area, and input

---

#### `POST /get`
**Purpose**: Process chat message and generate response

**Authentication**: Required

**POST Parameters**:
- `msg`: User's message text
- `conversation_id`: Optional, existing conversation ID

**Process**:
1. Escape HTML in user message (XSS prevention)
2. Get or create conversation
3. Save user message to database
4. Invoke RAG chain:
   - Embed query
   - Retrieve top 3 similar chunks from Pinecone
   - Generate response using LLM
5. Escape HTML in AI response
6. Save assistant message to database
7. Update conversation timestamp and title

**Response JSON**:
```json
{
  "answer": "AI generated response",
  "conversation_id": 123
}
```

**Error Response**:
```json
{
  "error": "Error message"
}
```

---

#### `POST /new-chat`
**Purpose**: Create new conversation

**Authentication**: Required

**Response JSON**:
```json
{
  "conversation_id": 456
}
```

---

#### `GET /load-chat/<conversation_id>`
**Purpose**: Load conversation history

**Authentication**: Required

**URL Parameter**: `conversation_id` (Integer)

**Response JSON**:
```json
{
  "conversation": {
    "id": 123,
    "title": "Conversation Title",
    "created_at": "2024-01-15 10:30",
    "updated_at": "2024-01-15 14:45"
  },
  "messages": [
    {
      "content": "Message text",
      "is_user": true,
      "timestamp": "10:30"
    }
  ]
}
```

**Error**: 404 if conversation not found or doesn't belong to user

---

#### `POST /delete-chat/<conversation_id>`
**Purpose**: Delete conversation

**Authentication**: Required

**URL Parameter**: `conversation_id` (Integer)

**Process**: Cascade deletes all associated messages

**Response JSON**:
```json
{
  "success": true
}
```

**Error**: 404 if conversation not found

---

#### `GET /get-conversations`
**Purpose**: List all user's conversations

**Authentication**: Required

**Response JSON**:
```json
{
  "conversations": [
    {
      "id": 123,
      "title": "Medical Question",
      "created_at": "2024-01-15 10:30",
      "updated_at": "2024-01-15 14:45",
      "message_count": 8
    }
  ]
}
```

**Sort Order**: Descending by `updated_at` (most recent first)

---

## Installation Guide

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git
- Pinecone account ([app.pinecone.io](https://app.pinecone.io))
- OpenRouter account ([openrouter.ai](https://openrouter.ai))

### Step-by-Step Installation

#### 1. Clone Repository
```bash
git clone https://github.com/keshav-077/medical-chatbot-rag.git
cd medical-chatbot-rag
```

#### 2. Create Virtual Environment (Recommended)

**Using Conda**:
```bash
conda create -n medibot python=3.10 -y
conda activate medibot
```

**Using venv**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- Flask and extensions (SQLAlchemy, Login, Bcrypt)
- LangChain and integrations
- Pinecone client
- Sentence-transformers
- PyPDF for document processing

#### 4. Configure Environment Variables

Create `.env` file in project root:
```bash
# Copy example file
cp .env.example .env
```

Edit `.env` with your API keys:
```ini
PINECONE_API_KEY=your-pinecone-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
SECRET_KEY=your-random-secret-key-for-flask-sessions
```

**Getting API Keys**:
- **Pinecone**: Sign up at [app.pinecone.io](https://app.pinecone.io), create API key
- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai), get API key from Keys page
- **SECRET_KEY**: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`

#### 5. Initialize Vector Database
```bash
python store_index.py
```

**What this does**:
- Loads PDFs from `Data/` directory
- Splits text into chunks
- Generates embeddings
- Creates Pinecone index "medicalbot"
- Uploads vectors to Pinecone

**Note**: This step takes 2-5 minutes depending on document size and internet speed.

#### 6. Initialize SQLite Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

Or simply run the app once (database auto-initializes):

#### 7. Run Application
```bash
python app.py
```

Application starts at: **http://localhost:8080**

---

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PINECONE_API_KEY` | Yes | Pinecone API authentication | None |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API access | None |
| `SECRET_KEY` | Yes* | Flask session encryption | dev-secret-key** |

\* Development uses fallback, production MUST set this  
\** Insecure default, warning issued if not set

### Flask Configuration

```python
# Security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

### RAG Configuration

```python
# Embedding Model
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
embedding_dimension = 384

# Text Chunking
chunk_size = 500
chunk_overlap = 20

# Vector Search
search_type = "similarity"
top_k = 3  # Number of retrieved documents

# LLM Configuration
model = "openai/gpt-oss-120b:free"
temperature = 0.4  # Lower = more factual
max_tokens = 500
```

### Pinecone Index Configuration

```python
index_name = "medicalbot"
dimension = 384
metric = "cosine"
cloud = "aws"
region = "us-east-1"
spec = ServerlessSpec  # Auto-scales, pay-per-use
```

---

## Deployment

### Docker Deployment

#### Build Image
```bash
docker build -t medical-chatbot-rag:latest .
```

#### Run Container
```bash
docker run -d \
  -p 8080:8080 \
  --env-file .env \
  --name medical-chatbot \
  medical-chatbot-rag:latest
```

#### Docker Compose (Optional)
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    volumes:
      - ./instance:/app/instance  # Persist database
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

### AWS Deployment

#### Prerequisites
- AWS Account
- AWS CLI configured
- IAM user with EC2 and ECR permissions

#### Step 1: Create ECR Repository
```bash
aws ecr create-repository --repository-name medical-chatbot
```

Save the repository URI (e.g., `123456789.dkr.ecr.us-east-1.amazonaws.com/medical-chatbot`)

#### Step 2: Push Docker Image
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_URI>

# Tag image
docker tag medical-chatbot-rag:latest <ECR_URI>:latest

# Push
docker push <ECR_URI>:latest
```

#### Step 3: Launch EC2 Instance
- AMI: Ubuntu 22.04 LTS
- Instance Type: t2.medium (minimum)
- Security Group: Allow inbound 8080, 22 (SSH)
- Storage: 20GB minimum

#### Step 4: Install Docker on EC2
```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker
```

#### Step 5: Pull and Run Container
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_URI>

# Pull image
docker pull <ECR_URI>:latest

# Run container
docker run -d \
  -p 8080:8080 \
  -e PINECONE_API_KEY=<your-key> \
  -e OPENROUTER_API_KEY=<your-key> \
  -e SECRET_KEY=<your-secret> \
  --name medical-chatbot \
  --restart unless-stopped \
  <ECR_URI>:latest
```

#### Step 6: Access Application
Visit: `http://<EC2_PUBLIC_IP>:8080`

### Production Considerations

1. **Use HTTPS**: Set up SSL/TLS with Let's Encrypt or AWS Certificate Manager
2. **Load Balancer**: Use AWS ALB for multiple instances
3. **Database**: Migrate to PostgreSQL/MySQL for production
4. **Secrets**: Use AWS Secrets Manager instead of .env
5. **Monitoring**: CloudWatch logs and metrics
6. **Backup**: Regular database backups
7. **Rate Limiting**: Implement API rate limiting
8. **Auto-Scaling**: Use EC2 Auto Scaling Groups

---

## Security

### Implemented Security Measures

#### 1. Authentication & Authorization
- **Flask-Login**: Session-based authentication
- **Login Required**: Decorators protect all sensitive routes
- **User Isolation**: Users can only access their own conversations

#### 2. Password Security
- **Bcrypt Hashing**: Passwords hashed with salt (cost factor 12)
- **No Plain Text**: Passwords never stored in plain text
- **Password Validation**: Minimum 6 characters enforced

#### 3. XSS Prevention
- **HTML Escaping**: All user inputs escaped before display
- **MarkupSafe**: Uses Flask's `escape()` function
- **Template Auto-Escaping**: Jinja2 auto-escapes by default

#### 4. SQL Injection Prevention
- **SQLAlchemy ORM**: Parameterized queries prevent injection
- **No Raw SQL**: All database operations use ORM methods

#### 5. CSRF Protection
- **SESSION_COOKIE_HTTPONLY**: JavaScript cannot access session cookies
- **SESSION_COOKIE_SAMESITE**: 'Lax' mode prevents CSRF attacks

#### 6. Environment Security
- **Environment Variables**: Sensitive keys in .env, not in code
- **.gitignore**: .env file excluded from version control
- **Warning System**: Alerts if SECRET_KEY not set

#### 7. API Security
- **API Key Protection**: Keys stored in environment, not hardcoded
- **HTTP Referer**: OpenRouter API includes referer header

### Security Best Practices (Recommendations)

1. **HTTPS**: Always use HTTPS in production
2. **Rate Limiting**: Implement rate limiting on chat endpoint
3. **Input Validation**: Add stricter input validation
4. **Content Security Policy**: Add CSP headers
5. **Database**: Use PostgreSQL with connection pooling in production
6. **Logging**: Implement audit logging for sensitive actions
7. **2FA**: Consider two-factor authentication
8. **Session Timeout**: Implement automatic session expiration

---

## File Structure

```
medical-chatbot-rag/
│
├── app.py                      # Main Flask application
├── models.py                   # Database models (User, Conversation, Message)
├── store_index.py              # Vector database initialization script
├── setup.py                    # Package setup configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container configuration
├── .dockerignore               # Docker ignore rules
├── .env                        # Environment variables (not in git)
├── .env.example                # Example environment file
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── README.md                   # Project overview
│
├── src/                        # Source code package
│   ├── __init__.py            # Package initializer
│   ├── helper.py              # Utility functions (PDF load, text split, embeddings)
│   └── prompt.py              # LLM prompt templates
│
├── Data/                       # Medical documents
│   └── Medical_book.pdf       # Source medical literature
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template (if used)
│   ├── chat.html              # Main chat interface
│   ├── login.html             # Login page
│   ├── signup.html            # Registration page
│   └── profile.html           # User profile page
│
├── static/                     # Static assets
│   └── style.css              # Application styles
│
├── instance/                   # Instance-specific files
│   └── medical_chatbot.db     # SQLite database (auto-generated)
│
├── research/                   # Development notebooks
│   └── trials.ipynb           # Experimentation notebook
│
└── medical_chatbot_rag.egg-info/  # Package metadata (auto-generated)
    ├── dependency_links.txt
    ├── PKG-INFO
    ├── SOURCES.txt
    └── top_level.txt
```

### Key Files Explained

| File | Purpose |
|------|---------|
| `app.py` | Main application with routes, RAG setup, database init |
| `models.py` | SQLAlchemy models for User, Conversation, Message |
| `store_index.py` | One-time script to create Pinecone vector index |
| `src/helper.py` | PDF loading, text splitting, embedding functions |
| `src/prompt.py` | System prompt template for LLM |
| `requirements.txt` | All Python package dependencies |
| `.env` | Environment variables (API keys, secrets) |
| `Dockerfile` | Container build instructions |

---

## Development Guide

### Local Development Setup

1. **Install in Development Mode**:
```bash
pip install -e .
```

2. **Enable Debug Mode**:
In `app.py`, debug mode is already enabled:
```python
app.run(host="0.0.0.0", port=8080, debug=True)
```

3. **Hot Reload**: Flask automatically reloads on file changes in debug mode

### Adding New Medical Documents

1. **Add PDF**: Place new PDF in `Data/` directory
2. **Re-index**: Run `python store_index.py`
3. **Verify**: Test queries related to new content

### Modifying LLM Behavior

**Change Model**:
```python
# In app.py
llm = ChatOpenAI(
    model="openai/gpt-4-turbo",  # Change model
    temperature=0.3,             # Adjust creativity
    max_tokens=1000,             # Increase response length
)
```

**Change Prompt**:
Edit `src/prompt.py`:
```python
system_prompt = (
    "You are a medical expert assistant. "
    "Provide detailed, accurate answers based on the context. "
    "If uncertain, explain the limitations. "
    "{context}"
)
```

**Change Retrieval Settings**:
```python
# In app.py
retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}  # Retrieve top 5 instead of 3
)
```

### Database Migrations

For schema changes, consider using Flask-Migrate:

```bash
pip install flask-migrate
```

Initialize:
```python
from flask_migrate import Migrate
migrate = Migrate(app, db)
```

### Testing Recommendations

1. **Unit Tests**: Test helper functions
```python
# test_helper.py
from src.helper import text_split

def test_text_split():
    docs = [{"page_content": "A" * 1000}]
    chunks = text_split(docs)
    assert len(chunks) > 1
    assert len(chunks[0].page_content) <= 500
```

2. **Integration Tests**: Test API endpoints
```python
# test_app.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
```

3. **RAG Tests**: Validate retrieval quality
```python
def test_retriever():
    query = "What is diabetes?"
    docs = retriever.invoke(query)
    assert len(docs) == 3
    assert "diabetes" in docs[0].page_content.lower()
```

### Frontend Customization

**Change Colors** (`static/style.css`):
```css
:root {
    --primary-color: #4a90e2;    /* Change primary color */
    --background-color: #f5f5f5;
    --text-color: #333;
}
```

**Modify Layout** (`templates/chat.html`):
- Edit HTML structure
- JavaScript functions for behavior changes
- jQuery for AJAX handling

### Common Development Tasks

#### Reset Database
```bash
rm instance/medical_chatbot.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### Re-index Documents
```bash
python store_index.py
```

#### View Database
```bash
sqlite3 instance/medical_chatbot.db
# SQLite commands
.tables
.schema user
SELECT * FROM user;
.quit
```

#### Check Pinecone Index
```python
from pinecone.grpc import PineconeGRPC as PineconeClient
import os

pc = PineconeClient(api_key=os.environ['PINECONE_API_KEY'])
index = pc.Index("medicalbot")
stats = index.describe_index_stats()
print(stats)
```

### API Usage Examples

#### Chat API with curl
```bash
curl -X POST http://localhost:8080/get \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "msg=What is hypertension?&conversation_id="
```

#### Load Conversations
```bash
curl -X GET http://localhost:8080/get-conversations \
  -H "Cookie: session=<session-cookie>"
```

---

## Troubleshooting

### Common Issues

#### 1. Pinecone Connection Error
**Error**: `PineconeException: API key not found`

**Solution**:
- Verify `.env` file exists and contains `PINECONE_API_KEY`
- Check API key is valid at [app.pinecone.io](https://app.pinecone.io)
- Ensure `.env` is loaded: `load_dotenv()` called before usage

#### 2. OpenRouter API Error
**Error**: `401 Unauthorized` or `Invalid API key`

**Solution**:
- Verify `OPENROUTER_API_KEY` in `.env`
- Check credits at [openrouter.ai](https://openrouter.ai)
- Ensure model name is correct: `openai/gpt-oss-120b:free`

#### 3. Embedding Model Download Slow
**Issue**: First run downloads 90MB model

**Solution**:
- Wait for download to complete (happens once)
- Model cached in `~/.cache/huggingface/`
- Subsequent runs use cached model

#### 4. Database Locked Error
**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
- Close other connections to database
- Use single-threaded mode: `app.run(threaded=False)`
- Consider PostgreSQL for production

#### 5. Port Already in Use
**Error**: `Address already in use: Port 8080`

**Solution**:
```bash
# Find process using port 8080
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8080 | xargs kill -9

# Or change port in app.py
app.run(host="0.0.0.0", port=8081)
```

#### 6. Module Not Found
**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install <package-name>
```

#### 7. Empty Responses from LLM
**Issue**: AI returns empty or very short responses

**Solution**:
- Check OpenRouter API credits
- Verify Pinecone index has data: `python store_index.py`
- Check retriever returns documents: `retriever.invoke("test query")`
- Increase `max_tokens` in LLM config

---

## Performance Optimization

### 1. Vector Search Optimization
- **Batch Queries**: Process multiple queries together
- **Namespace Filtering**: Use Pinecone namespaces for medical specialties
- **Metadata Filtering**: Add metadata (document type, date) for filtered search

### 2. Database Optimization
- **Indexes**: Add indexes on frequently queried columns
```python
# In models.py
class Conversation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
```

- **Connection Pooling**: Use PostgreSQL with connection pool in production

### 3. Caching
- **Cache Embeddings**: Store user query embeddings
- **Response Caching**: Cache common medical questions
- **Redis**: Use Redis for session and response caching

### 4. LLM Optimization
- **Streaming**: Implement streaming responses for better UX
- **Token Limits**: Adjust `max_tokens` based on needs
- **Model Selection**: Balance cost vs quality (free vs paid models)

### 5. Frontend Optimization
- **Lazy Loading**: Load conversations on demand
- **Pagination**: Paginate message history for long conversations
- **Debouncing**: Debounce typing indicators

---

## Extending the Application

### Adding New Features

#### 1. Multi-Language Support
```python
# Install flask-babel
pip install flask-babel

# Configure
from flask_babel import Babel
babel = Babel(app)
```

#### 2. Voice Input/Output
```python
# Add speech recognition
pip install SpeechRecognition pyttsx3

# Implement in frontend with Web Speech API
```

#### 3. PDF Export
```python
# Export conversation as PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@app.route("/export/<int:conversation_id>")
@login_required
def export_conversation(conversation_id):
    # Implementation
    pass
```

#### 4. Admin Dashboard
```python
# Add admin role and dashboard
class User(UserMixin, db.Model):
    is_admin = db.Column(db.Boolean, default=False)

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    # Admin stats and management
```

#### 5. Conversation Sharing
```python
# Share conversation with unique link
@app.route("/share/<share_token>")
def shared_conversation(share_token):
    # Validate token and display read-only conversation
    pass
```

#### 6. Medical Image Analysis
```python
# Add vision model for medical images
from langchain.chains import MultiModalChain

# Process medical images with text queries
```

### Integration Options

#### 1. Telegram Bot
```python
pip install python-telegram-bot

# Create bot endpoint
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    # Process Telegram messages
    pass
```

#### 2. WhatsApp Integration
```python
# Use Twilio WhatsApp API
pip install twilio

# Webhook for WhatsApp messages
```

#### 3. Slack Bot
```python
pip install slack-sdk

# Slack event listener
```

---

## API Reference (Quick Reference)

### Authentication
- `POST /login` - User login
- `POST /signup` - User registration
- `GET /logout` - User logout
- `POST /change-password` - Update password

### Chat
- `GET /` - Chat interface
- `POST /get` - Send message and get AI response
- `POST /new-chat` - Create new conversation
- `GET /load-chat/<id>` - Load conversation history
- `POST /delete-chat/<id>` - Delete conversation
- `GET /get-conversations` - List all conversations

### Profile
- `GET /profile` - User profile page

---

## Monitoring and Logging

### Application Logging

Add logging to `app.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"User {current_user.id} sent message")
logger.error(f"RAG chain error: {e}")
```

### Metrics to Track
1. **User Metrics**:
   - Total users
   - Active users (daily/weekly)
   - New registrations

2. **Usage Metrics**:
   - Messages per day
   - Average conversation length
   - Response times

3. **AI Metrics**:
   - Token usage
   - API costs
   - Retrieval quality

4. **System Metrics**:
   - Database size
   - API latency
   - Error rates

### Health Check Endpoint
```python
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "pinecone": "connected",
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

## FAQ

### General Questions

**Q: What medical topics can the chatbot answer?**
A: The chatbot's knowledge is limited to the medical documents in the `Data/` directory. By default, it uses Medical_book.pdf. Add more PDFs for broader coverage.


**Q: Is this HIPAA compliant?**
A: No, this is a demo application. For HIPAA compliance, you need secure infrastructure, audit logging, encryption at rest, business associate agreements with vendors, and compliance review.

**Q: Can I use a different LLM?**
A: Yes. Change the model in `app.py`:
```python
llm = ChatOpenAI(
    model="anthropic/claude-3-opus",  # or any OpenRouter model
    openai_api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)
```

**Q: How much does it cost to run?**
A: 
- Pinecone: Free tier (1M vectors)
- OpenRouter: Free model (gpt-oss-120b) or paid models (~$0.001-0.01 per query)
- AWS: EC2 costs vary (~$10-50/month for t2.medium)

**Q: Can I use a local LLM?**
A: Yes, use Ollama or LocalAI:
```python
from langchain_community.llms import Ollama
llm = Ollama(model="llama2")
```

### Technical Questions

**Q: Why use RAG instead of fine-tuning?**
A: RAG is better for:
- Dynamic knowledge updates (add PDFs without retraining)
- Transparency (see source documents)
- Lower cost (no training required)
- Reduced hallucinations (grounded in source material)

**Q: How accurate are the responses?**
A: Accuracy depends on:
- Quality of source documents
- Retrieval effectiveness (k=3 documents)
- LLM capability
- Query clarity

**Q: Can I add more documents?**
A: Yes:
1. Add PDFs to `Data/` directory
2. Run `python store_index.py`
3. Vectors automatically added to Pinecone

**Q: What's the maximum conversation length?**
A: No hard limit, but consider:
- Long conversations increase database size
- UI may slow with 1000+ messages
- Implement pagination for better performance

**Q: Can multiple users chat simultaneously?**
A: Yes, Flask handles concurrent requests. For high traffic:
- Use production WSGI server (Gunicorn/uWSGI)
- Consider async Flask with async LangChain
- Add load balancer for horizontal scaling

---

## Contributing

### How to Contribute

1. **Fork the Repository**
```bash
git fork https://github.com/keshav-077/medical-chatbot-rag.git
```

2. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

3. **Make Changes**
- Write clean, documented code
- Follow PEP 8 style guide
- Add tests if applicable

4. **Commit Changes**
```bash
git add .
git commit -m "Add: Description of your changes"
```

5. **Push to Branch**
```bash
git push origin feature/your-feature-name
```

6. **Create Pull Request**
- Describe changes clearly
- Link related issues
- Wait for review

### Code Style Guidelines
- **Python**: Follow PEP 8
- **JavaScript**: Use consistent indentation (2 spaces)
- **Comments**: Explain "why", not "what"
- **Naming**: Descriptive variable names

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Keshav

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- **LangChain**: RAG framework and LLM orchestration
- **OpenAI/OpenRouter**: Language model API access
- **Pinecone**: Serverless vector database
- **HuggingFace**: Pre-trained embedding models
- **Flask**: Lightweight web framework
- **Community**: Open-source contributors and testers

---

## Contact & Support

### Author
**Keshav**
- GitHub: [@keshav-077](https://github.com/keshav-077)
- Project: [medical-chatbot-rag](https://github.com/keshav-077/medical-chatbot-rag)

### Getting Help

1. **GitHub Issues**: Report bugs or request features
   - [Create Issue](https://github.com/keshav-077/medical-chatbot-rag/issues)

2. **Discussions**: Ask questions or share ideas
   - [GitHub Discussions](https://github.com/keshav-077/medical-chatbot-rag/discussions)

3. **Documentation**: Check this document for detailed information

### Useful Resources

- [LangChain Documentation](https://python.langchain.com/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [OpenRouter API](https://openrouter.ai/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [HuggingFace Models](https://huggingface.co/models)

---

## Changelog

### Version 1.0.0 (Current)
- Initial release
- RAG-powered medical Q&A
- User authentication and profiles
- Multi-conversation support
- Responsive web interface
- Docker deployment support
- AWS deployment guide

### Planned Features (Roadmap)
- [ ] Streaming responses
- [ ] Voice input/output
- [ ] PDF export of conversations
- [ ] Admin dashboard
- [ ] Multi-language support
- [ ] Medical image analysis
- [ ] Mobile app (React Native)
- [ ] Conversation analytics
- [ ] Rate limiting
- [ ] HTTPS/SSL setup guide

---

## Appendix

### A. Environment Variables Reference

| Variable | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `PINECONE_API_KEY` | String | Yes | Pinecone authentication | `abc123...` |
| `OPENROUTER_API_KEY` | String | Yes | OpenRouter API access | `sk-or-...` |
| `SECRET_KEY` | String | Yes* | Flask session key | `hex-64-chars` |

\* Development fallback provided but insecure


### B. Dependencies Reference

#### Core Framework
- `flask`: Web framework
- `flask-sqlalchemy`: Database ORM
- `flask-login`: Authentication
- `flask-bcrypt`: Password hashing

#### AI/ML Stack
- `langchain`: RAG framework
- `langchain-openai`: LLM integration
- `langchain-pinecone`: Vector store
- `langchain-community`: Document loaders
- `sentence-transformers`: Embeddings
- `pinecone[grpc]`: Vector database client

#### Utilities
- `python-dotenv`: Environment variables
- `pypdf`: PDF processing
- `email-validator`: Email validation

### C. Database Schema SQL

```sql
-- User table
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Conversation table
CREATE TABLE conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Message table
CREATE TABLE message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_user BOOLEAN NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_conversation_user_id ON conversation(user_id);
CREATE INDEX idx_conversation_updated_at ON conversation(updated_at);
CREATE INDEX idx_message_conversation_id ON message(conversation_id);
```

### D. Sample API Responses

#### Login Success
```json
{
  "redirect": "/",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### Chat Response
```json
{
  "answer": "Diabetes is a chronic condition affecting blood sugar regulation. Type 1 occurs when the pancreas produces insufficient insulin. Type 2 involves insulin resistance where cells don't respond properly to insulin.",
  "conversation_id": 42
}
```

#### Conversations List
```json
{
  "conversations": [
    {
      "id": 42,
      "title": "What is diabetes?",
      "created_at": "2024-01-15 10:30",
      "updated_at": "2024-01-15 14:45",
      "message_count": 12
    },
    {
      "id": 41,
      "title": "Hypertension symptoms",
      "created_at": "2024-01-14 09:15",
      "updated_at": "2024-01-14 09:45",
      "message_count": 6
    }
  ]
}
```

#### Error Response
```json
{
  "error": "Conversation not found",
  "status": 404
}
```

### E. Deployment Checklist

#### Pre-Deployment
- [ ] Set strong SECRET_KEY
- [ ] Configure production database (PostgreSQL)
- [ ] Set up HTTPS/SSL certificate
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Back up strategy defined
- [ ] Environment variables secured (AWS Secrets Manager)
- [ ] Rate limiting configured
- [ ] Error tracking setup (Sentry)

#### Post-Deployment
- [ ] Test all endpoints
- [ ] Verify database connections
- [ ] Check API integrations (Pinecone, OpenRouter)
- [ ] Monitor error logs
- [ ] Load testing completed
- [ ] Security scan performed
- [ ] Documentation updated
- [ ] Team training completed

### F. Glossary

- **RAG (Retrieval-Augmented Generation)**: AI pattern combining information retrieval with text generation
- **Vector Database**: Database optimized for similarity search over high-dimensional vectors
- **Embedding**: Numerical representation of text in vector space
- **Cosine Similarity**: Measure of similarity between vectors
- **LLM (Large Language Model)**: AI model trained on vast text data for language understanding
- **Prompt Engineering**: Crafting inputs to guide LLM behavior
- **Context Window**: Maximum text length an LLM can process
- **Token**: Smallest unit of text processed by LLM (roughly 0.75 words)
- **ORM (Object-Relational Mapping)**: Database abstraction layer
- **WSGI (Web Server Gateway Interface)**: Python web server standard
- **XSS (Cross-Site Scripting)**: Security vulnerability from unsanitized inputs
- **CSRF (Cross-Site Request Forgery)**: Attack forcing authenticated users to execute unwanted actions

---

## Summary

This Medical Chatbot with RAG architecture provides an intelligent, context-aware question-answering system for medical queries. By combining vector search, document retrieval, and large language models, it delivers accurate, evidence-based responses grounded in medical literature.

**Key Strengths**:
- ✅ RAG architecture reduces hallucinations
- ✅ User authentication and multi-session support
- ✅ Responsive, modern UI
- ✅ Easy to extend and customize
- ✅ Docker and cloud deployment ready
- ✅ Security best practices implemented

**Ideal For**:
- Medical information systems
- Healthcare chatbot prototypes
- RAG architecture learning
- LangChain/Pinecone demonstrations

**Next Steps**:
1. Set up your environment following the Installation Guide
2. Configure API keys and run `store_index.py`
3. Start the application and test the chat
4. Customize prompts, UI, and add more medical documents
5. Deploy to production with security hardening

---

**⭐ If you find this project helpful, please star the repository!**

**📧 Questions? Open an issue on [GitHub](https://github.com/keshav-077/medical-chatbot-rag/issues)**

---

*Last Updated: 2024*  
*Documentation Version: 1.0.0*  
*Project Version: 1.0.0*
