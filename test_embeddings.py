"""
Test the embedding providers to see what dimensions they actually return.
"""

from src.embeddings import get_embedding_manager
from dotenv import load_dotenv

load_dotenv()

print("Initializing embedding manager...")
manager = get_embedding_manager()

print(f"\nActive provider: {manager.active_provider.name}")
print(f"Expected dimensions: {manager.active_provider.dimensions}")

# Get the embeddings instance
embeddings = manager.get_embeddings()

# Test with a sample text
test_text = "This is a test sentence to check embedding dimensions."
print(f"\nTest text: '{test_text}'")

print("\nGenerating embedding...")
try:
    embedding_vector = embeddings.embed_query(test_text)
    actual_dimension = len(embedding_vector)
    
    print(f"✅ Embedding generated successfully!")
    print(f"Actual dimension: {actual_dimension}")
    print(f"Expected dimension: {manager.active_provider.dimensions}")
    
    if actual_dimension != manager.active_provider.dimensions:
        print(f"\n⚠️  WARNING: Dimension mismatch!")
        print(f"   Update the provider's dimension to {actual_dimension}")
    else:
        print(f"\n✅ Dimensions match!")
        
except Exception as e:
    print(f"❌ Error generating embedding: {e}")
    
    # Try fallback provider if available
    if len(manager.providers) > 1:
        print(f"\nTrying fallback provider...")
        manager.active_provider = manager.providers[1]
        print(f"Fallback provider: {manager.active_provider.name}")
        print(f"Expected dimensions: {manager.active_provider.dimensions}")
        
        embeddings = manager.get_embeddings()
        try:
            embedding_vector = embeddings.embed_query(test_text)
            actual_dimension = len(embedding_vector)
            
            print(f"✅ Embedding generated successfully with fallback!")
            print(f"Actual dimension: {actual_dimension}")
            print(f"Expected dimension: {manager.active_provider.dimensions}")
            
            if actual_dimension != manager.active_provider.dimensions:
                print(f"\n⚠️  WARNING: Dimension mismatch!")
                print(f"   Update the provider's dimension to {actual_dimension}")
            else:
                print(f"\n✅ Dimensions match!")
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
