"""
Delete the old Pinecone index to recreate it with the correct dimension.

IMPORTANT: Only run this if you want to completely delete your existing
Pinecone index and start fresh with new embeddings.
"""

from pinecone.grpc import PineconeGRPC as Pinecone
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
if not PINECONE_API_KEY:
    print("❌ PINECONE_API_KEY not found in .env file")
    exit(1)

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "medicalbot"

try:
    # Check if index exists
    indexes = pc.list_indexes()
    existing_indexes = [idx.name for idx in indexes]
    
    if index_name in existing_indexes:
        index_info = pc.describe_index(index_name)
        print(f"Found index '{index_name}':")
        print(f"  Dimension: {index_info.dimension}")
        print(f"  Metric: {index_info.metric}")
        
        confirm = input(f"\n⚠️  Are you sure you want to DELETE the index '{index_name}'? (yes/no): ")
        if confirm.lower() == 'yes':
            pc.delete_index(index_name)
            print(f"\n✅ Index '{index_name}' deleted successfully!")
            print("You can now run 'python store_index.py' to create a new index.")
        else:
            print("\n❌ Deletion cancelled.")
    else:
        print(f"Index '{index_name}' does not exist. Nothing to delete.")
        
except Exception as e:
    print(f"❌ Error: {e}")
