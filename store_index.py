"""
Store Index — Embed medical documents and upload to Pinecone.

This script:
1. Loads PDF files from the Data/ directory
2. Splits them into text chunks
3. Generates embeddings using the API-based embedding system (Jina/HF)
4. Creates or connects to a Pinecone index (768 dimensions)
5. Uploads all embeddings to Pinecone

IMPORTANT: The index dimension is 768 (matching Jina AI embeddings).
If you previously used sentence-transformers (384 dims), you MUST
delete the old index first — Pinecone cannot change index dimensions.

Usage:
    python store_index.py
"""

from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import Pinecone as PineconeVectorStore
from dotenv import load_dotenv
import os
import time
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in .env file")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

print("Loading and processing medical documents...")
extracted_data = load_pdf_file(data='Data/')
text_chunks = text_split(extracted_data)
print(f"Extracted {len(text_chunks)} text chunks from documents")

print("Loading embeddings (API-based, NO local downloads)...")
embedding_manager = download_hugging_face_embeddings()

# Try to use Jina first, but if rate limited, use HuggingFace
try:
    embeddings = embedding_manager.get_embeddings()
    print(f"Using embedding provider: {embedding_manager.active_provider.name}")
    
    # Quick test to see if we can generate an embedding
    test_result = embeddings.embed_query("test")
    print(f"✅ Provider is working (dimension: {len(test_result)})")
except Exception as e:
    if "rate limit" in str(e).lower():
        print(f"⚠️ Rate limit hit on {embedding_manager.active_provider.name}, switching to fallback...")
        if embedding_manager.fallback_to_next():
            embeddings = embedding_manager.get_embeddings()
            print(f"Using fallback provider: {embedding_manager.active_provider.name}")
        else:
            raise RuntimeError("All embedding providers failed")
    else:
        raise

print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "medicalbot"

# Get the embedding dimension from the active provider
EMBEDDING_DIMENSION = embedding_manager.active_provider.dimensions
print(f"Using embedding dimension: {EMBEDDING_DIMENSION}")

# Check if index exists, if not create it
print("Checking for existing index...")
try:
    indexes = pc.list_indexes()
    existing_indexes = [idx.name for idx in indexes]

    if index_name not in existing_indexes:
        print(f"Creating new index '{index_name}' with {EMBEDDING_DIMENSION} dimensions...")
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIMENSION,
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
        # Verify dimension matches
        index_info = pc.describe_index(index_name)
        if hasattr(index_info, 'dimension') and index_info.dimension != EMBEDDING_DIMENSION:
            print(f"⚠️  WARNING: Index dimension is {index_info.dimension}, but embeddings are {EMBEDDING_DIMENSION}")
            print(f"   You may need to delete and recreate the index.")
            print(f"   Run: pc.delete_index('{index_name}') in a Python shell")
            raise ValueError(
                f"Dimension mismatch: index={index_info.dimension}, embeddings={EMBEDDING_DIMENSION}"
            )

except Exception as e:
    print(f"Note: {e}")
    print("Continuing with existing index...")

# Create vector store and add documents
print("\nStarting to create embeddings and upload to Pinecone...")
print("This may take a few minutes depending on the number of documents...")
print(f"Processing {len(text_chunks)} text chunks...")

# Process in smaller batches to avoid rate limits
BATCH_SIZE = 100  # Process 100 chunks at a time
total_batches = (len(text_chunks) + BATCH_SIZE - 1) // BATCH_SIZE

try:
    # Try to use from_existing_index first
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    print("Connected to existing index")

    # Add documents in smaller batches with progress tracking
    print(f"Uploading in {total_batches} batches of ~{BATCH_SIZE} documents...")
    for i in range(0, len(text_chunks), BATCH_SIZE):
        batch = text_chunks[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        
        try:
            docsearch.add_documents(batch)
            print(f"✅ Batch {batch_num}/{total_batches} uploaded ({len(batch)} documents)")
        except Exception as batch_error:
            error_msg = str(batch_error)
            if "rate limit" in error_msg.lower():
                print(f"⚠️ Rate limit hit on batch {batch_num}, waiting 60 seconds...")
                time.sleep(60)
                # Retry the batch
                print(f"Retrying batch {batch_num}...")
                docsearch.add_documents(batch)
                print(f"✅ Batch {batch_num}/{total_batches} uploaded (after retry)")
            else:
                raise
        
        # Small delay between batches to avoid rate limits
        if i + BATCH_SIZE < len(text_chunks):
            time.sleep(2)
    
    print(f"✅ Successfully stored {len(text_chunks)} embeddings in Pinecone!")

except Exception as e:
    error_msg = str(e)
    print(f"Error: {e}")
    
    # Check if it's a rate limit error and try fallback
    if "rate limit" in error_msg.lower():
        print("⚠️ Rate limit hit, trying fallback provider...")
        if embedding_manager.fallback_to_next():
            embeddings = embedding_manager.get_embeddings()
            print(f"Switched to: {embedding_manager.active_provider.name}")
            
            # NOTE: If dimensions changed, we need to recreate the index
            new_dimension = embedding_manager.active_provider.dimensions
            if new_dimension != EMBEDDING_DIMENSION:
                print(f"⚠️ Dimension changed from {EMBEDDING_DIMENSION} to {new_dimension}")
                print(f"Deleting old index and recreating...")
                pc.delete_index(index_name)
                time.sleep(5)
                pc.create_index(
                    name=index_name,
                    dimension=new_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                print("Waiting for new index to be ready...")
                time.sleep(15)
                EMBEDDING_DIMENSION = new_dimension
            
            # Retry with fallback embeddings in batches
            print("Retrying with fallback provider in batches...")
            docsearch = PineconeVectorStore.from_existing_index(
                index_name=index_name,
                embedding=embeddings
            )
            
            for i in range(0, len(text_chunks), BATCH_SIZE):
                batch = text_chunks[i:i+BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                
                try:
                    docsearch.add_documents(batch)
                    print(f"✅ Batch {batch_num}/{total_batches} uploaded ({len(batch)} documents)")
                except Exception as retry_error:
                    if "504" in str(retry_error) or "timeout" in str(retry_error).lower():
                        print(f"⚠️ Timeout on batch {batch_num}, waiting 30 seconds...")
                        time.sleep(30)
                        docsearch.add_documents(batch)
                        print(f"✅ Batch {batch_num}/{total_batches} uploaded (after retry)")
                    else:
                        raise
                
                if i + BATCH_SIZE < len(text_chunks):
                    time.sleep(3)
            
            print(f"✅ Successfully stored {len(text_chunks)} embeddings in Pinecone!")
        else:
            print("❌ No fallback provider available")
            raise
    else:
        print("\nTroubleshooting tips:")
        print("1. Verify your PINECONE_API_KEY in .env file")
        print("2. Check if you have quota limits on your Pinecone account")
        print(f"3. Ensure the index '{index_name}' has dimension={EMBEDDING_DIMENSION}")
        print("4. Wait a minute for rate limits to reset and try again")
        raise

print("\n✅ Vector database initialization complete!")
print("You can now run 'python app.py' to start the chatbot.")
