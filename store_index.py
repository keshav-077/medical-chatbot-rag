from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import Pinecone as PineconeVectorStore
from dotenv import load_dotenv
import os
import time


load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in .env file")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

print("Loading and processing medical documents...")
extracted_data = load_pdf_file(data='Data/')
text_chunks = text_split(extracted_data)
print(f"Extracted {len(text_chunks)} text chunks from documents")

print("Loading embeddings model...")
embeddings = download_hugging_face_embeddings()

print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "medicalbot"

# Check if index exists, if not create it
print("Checking for existing index...")
try:
    indexes = pc.list_indexes()
    existing_indexes = [idx.name for idx in indexes]
    
    if index_name not in existing_indexes:
        print(f"Creating new index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=384,  # sentence-transformers/all-MiniLM-L6-v2 dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"Index '{index_name}' created successfully!")
        print("Waiting for index to be ready...")
        time.sleep(15)
    else:
        print(f"Index '{index_name}' already exists")
        
except Exception as e:
    print(f"Note: {e}")
    print("Continuing with existing index...")

# Create vector store and add documents
print("\nStarting to create embeddings and upload to Pinecone...")
print("This may take a few minutes depending on the number of documents...")

try:
    # Try to use from_existing_index first
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    print("Connected to existing index")
    
    # Add documents in batches
    print("Adding documents to index...")
    docsearch.add_documents(text_chunks)
    print(f"✅ Successfully stored {len(text_chunks)} embeddings in Pinecone!")
    
except Exception as e:
    print(f"Error with from_existing_index: {e}")
    print("Trying alternative method...")
    
    # Alternative: Use from_documents
    try:
        docsearch = PineconeVectorStore.from_documents(
            documents=text_chunks,
            embedding=embeddings,
            index_name=index_name
        )
        print(f"✅ Successfully stored {len(text_chunks)} embeddings in Pinecone!")
    except Exception as e2:
        print(f"❌ Error storing embeddings: {e2}")
        print("\nTroubleshooting tips:")
        print("1. Verify your PINECONE_API_KEY in .env file")
        print("2. Check if you have quota limits on your Pinecone account")
        print("3. Ensure the index 'medicalbot' exists in your Pinecone dashboard")
        raise

print("\n✅ Vector database initialization complete!")
print("You can now run 'python app.py' to start the chatbot.")
