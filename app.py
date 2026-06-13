from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from markupsafe import escape as html_escape
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import Pinecone as PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from src.prompt import *
import os
import re
from datetime import datetime
from models import db, bcrypt, User, Conversation, Message

app = Flask(__name__)

load_dotenv()

# Configuration
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    import warnings
    warnings.warn("SECRET_KEY not set in .env — using insecure dev default. Set SECRET_KEY for production!", stacklevel=2)
    secret_key = 'dev-secret-key-change-in-production'
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Environment variables
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Initialize embeddings and vector store
embeddings = download_hugging_face_embeddings()

index_name = "medicalbot"

# Connect to Pinecone and create vector store
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

llm = ChatOpenAI(
    model="openai/gpt-oss-120b:free",
    openai_api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.4,
    max_tokens=500,
    default_headers={
        "HTTP-Referer": "http://localhost:8080",
        "X-Title": "Medical Chatbot RAG",
    },
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Create a simple RAG chain using LCEL
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Routes
@app.route("/")
@login_required
def index():
    return render_template('chat.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
    
    return render_template('login.html')

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Server-side validation
        email_re = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        
        if not name or len(name) < 2:
            flash('Name must be at least 2 characters.', 'danger')
            return redirect(url_for('signup'))
        
        if not re.match(email_re, email):
            flash('Please enter a valid email address.', 'danger')
            return redirect(url_for('signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'danger')
            return redirect(url_for('signup'))
        
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_new_password = request.form.get("confirm_new_password")

    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_new_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('profile'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route("/get", methods=["POST"])
@login_required
def chat():
    msg = request.form["msg"]
    conversation_id = request.form.get("conversation_id")
    
    print(f"User input: {msg}")
    
    # Get or create conversation
    if conversation_id:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
    else:
        # Create new conversation
        conversation = Conversation(user_id=current_user.id, title="New Conversation")
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
    
    # Save user message (escape HTML to prevent stored XSS)
    safe_msg = str(html_escape(msg))
    user_message = Message(
        conversation_id=conversation_id,
        content=safe_msg,
        is_user=True
    )
    db.session.add(user_message)
    
    try:
        # Use original msg for RAG (unescaped for better LLM comprehension)
        response = rag_chain.invoke(msg)
        print(f"Response: {response}")
        
        # Save assistant message (escape HTML)
        safe_response = str(html_escape(response))
        assistant_message = Message(
            conversation_id=conversation_id,
            content=safe_response,
            is_user=False
        )
        db.session.add(assistant_message)
        
        # Update conversation timestamp and title if it's the first message
        conversation.updated_at = datetime.utcnow()
        if conversation.title == "New Conversation" and len(msg.strip()) > 0:
            # Use first 50 characters of user message as title
            conversation.title = msg.strip()[:50] + ("..." if len(msg.strip()) > 50 else "")
        
        db.session.commit()
        
        return jsonify({
            "answer": response,
            "conversation_id": conversation_id
        })
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/new-chat", methods=["POST"])
@login_required
def new_chat():
    conversation = Conversation(user_id=current_user.id, title="New Conversation")
    db.session.add(conversation)
    db.session.commit()
    return jsonify({"conversation_id": conversation.id})

@app.route("/load-chat/<int:conversation_id>")
@login_required
def load_chat(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    
    chat_history = []
    for msg in messages:
        chat_history.append({
            "content": msg.content,
            "is_user": msg.is_user,
            "timestamp": msg.timestamp.strftime("%H:%M")
        })
    
    return jsonify({
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": conversation.updated_at.strftime("%Y-%m-%d %H:%M")
        },
        "messages": chat_history
    })

@app.route("/delete-chat/<int:conversation_id>", methods=["POST"])
@login_required
def delete_chat(conversation_id):
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({"success": True})

@app.route("/get-conversations")
@login_required
def get_conversations():
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    
    conv_list = []
    for conv in conversations:
        conv_list.append({
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": conv.updated_at.strftime("%Y-%m-%d %H:%M"),
            "message_count": len(conv.messages)
        })
    
    return jsonify({"conversations": conv_list})

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)