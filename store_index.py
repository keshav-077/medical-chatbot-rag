from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as PineconeClient
from pinecone import ServerlessSpec
from langchain_pinecone import Pinecone as PineconeVectorStore
from dotenv import load_dotenv
import os
import time


load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY


extracted_data=load_pdf_file(data='Data/')
text_chunks=text_split(extracted_data)
embeddings = download_hugging_face_embeddings()


pc = PineconeClient(api_key=PINECONE_API_KEY)

index_name = "medicalbot"

# Check if index exists, if not create it
existing_indexes = [index.name for index in pc.list_indexes()]
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=384, 
        metric="cosine", 
        spec=ServerlessSpec(
            cloud="aws", 
            region="us-east-1"
        ) 
    )
    print(f"Created index: {index_name}")
    # Wait for index to be ready
    time.sleep(10)
else:
    print(f"Index {index_name} already exists")

# Get the index
index = pc.Index(index_name)

# Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings, 
)

print("Embeddings stored successfully!")
