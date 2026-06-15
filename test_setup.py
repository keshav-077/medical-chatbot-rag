"""
Test script to verify the installation and setup (v2.0.0)
Run this after setup to ensure everything is working correctly.

Usage:
    python test_setup.py
"""

import sys
import os


def test_imports():
    """Test if all required packages can be imported."""
    print("Testing imports...")
    errors = []

    try:
        import flask
        print("  ✓ Flask")
    except ImportError as e:
        errors.append(f"Flask: {e}")

    try:
        import langchain
        print("  ✓ LangChain")
    except ImportError as e:
        errors.append(f"LangChain: {e}")

    try:
        import pinecone
        print(f"  ✓ Pinecone (version: {pinecone.__version__})")
    except ImportError as e:
        errors.append(f"Pinecone: {e}")

    try:
        import langchain_pinecone
        print("  ✓ LangChain-Pinecone")
    except ImportError as e:
        errors.append(f"LangChain-Pinecone: {e}")

    try:
        import langchain_openai
        print("  ✓ LangChain-OpenAI")
    except ImportError as e:
        errors.append(f"LangChain-OpenAI: {e}")

    try:
        import langchain_groq
        print("  ✓ LangChain-Groq")
    except ImportError as e:
        errors.append(f"LangChain-Groq: {e}")

    try:
        from langchain_community.embeddings import JinaEmbeddings
        print("  ✓ LangChain-Community (JinaEmbeddings)")
    except ImportError as e:
        errors.append(f"LangChain-Community JinaEmbeddings: {e}")

    try:
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        print("  ✓ LangChain-HuggingFace (HuggingFaceEndpointEmbeddings)")
    except ImportError as e:
        errors.append(f"LangChain-HuggingFace: {e}")

    try:
        from flask_limiter import Limiter
        print("  ✓ Flask-Limiter")
    except ImportError as e:
        errors.append(f"Flask-Limiter: {e}")

    try:
        import psycopg2
        print("  ✓ psycopg2-binary (PostgreSQL driver)")
    except ImportError as e:
        errors.append(f"psycopg2-binary: {e}")

    try:
        from dotenv import load_dotenv
        print("  ✓ Python-dotenv")
    except ImportError as e:
        errors.append(f"Python-dotenv: {e}")

    # Verify NO heavy dependencies
    print("\n  Checking for unwanted heavy dependencies...")
    try:
        import sentence_transformers
        print("  ⚠️  sentence-transformers is installed (should be removed!)")
        errors.append("sentence-transformers should NOT be installed")
    except ImportError:
        print("  ✓ sentence-transformers NOT installed (correct!)")

    try:
        import torch
        print("  ⚠️  torch is installed (should be removed!)")
        errors.append("torch should NOT be installed")
    except ImportError:
        print("  ✓ torch NOT installed (correct!)")

    if errors:
        print(f"\n❌ {len(errors)} import error(s):")
        for err in errors:
            print(f"  - {err}")
        print("Run: pip install -r requirements.txt")
        return False

    print("\n✅ All required packages are installed!\n")
    return True


def test_env_file():
    """Test if .env file exists and has required keys."""
    print("Testing .env configuration...")
    if not os.path.exists('.env'):
        print("  ❌ .env file not found!")
        print("  Copy .env.example to .env and add your API keys")
        return False

    from dotenv import load_dotenv
    load_dotenv()

    # Required keys
    required_keys = ['PINECONE_API_KEY', 'OPENROUTER_API_KEY', 'SECRET_KEY']
    missing_keys = []

    for key in required_keys:
        value = os.environ.get(key)
        if not value or value.startswith('your-'):
            missing_keys.append(key)
        else:
            print(f"  ✓ {key} is set")

    # Embedding keys (at least one required)
    jina_key = os.environ.get('JINA_API_KEY')
    hf_key = os.environ.get('HUGGINGFACE_API_KEY')

    if jina_key and not jina_key.startswith('your-'):
        print(f"  ✓ JINA_API_KEY is set (primary embeddings)")
    elif hf_key and not hf_key.startswith('your-'):
        print(f"  ✓ HUGGINGFACE_API_KEY is set (backup embeddings)")
    else:
        missing_keys.append('JINA_API_KEY or HUGGINGFACE_API_KEY')
        print("  ❌ No embedding API key set (need JINA_API_KEY or HUGGINGFACE_API_KEY)")

    # Optional keys
    groq_key = os.environ.get('GROQ_API_KEY')
    if groq_key and not groq_key.startswith('your-'):
        print(f"  ✓ GROQ_API_KEY is set (backup LLM)")
    else:
        print(f"  ⚠️  GROQ_API_KEY not set (optional, backup LLM)")

    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print(f"  ✓ DATABASE_URL is set (production database)")
    else:
        print(f"  ⚠️  DATABASE_URL not set (will use SQLite for local dev)")

    if missing_keys:
        print(f"\n  ❌ Missing or invalid keys: {', '.join(missing_keys)}")
        print("  Please update your .env file with actual API keys")
        return False

    print("\n✅ Environment variables configured!\n")
    return True


def test_data_directory():
    """Test if Data directory and medical PDF exist."""
    print("Testing data directory...")
    if not os.path.exists('Data'):
        print("  ⚠️  Data directory not found (needed only for re-indexing)")
        print("  Create 'Data/' and add medical PDFs if you need to re-index")
        return True  # Not fatal — only needed for store_index.py

    pdf_files = [f for f in os.listdir('Data') if f.endswith('.pdf')]
    if not pdf_files:
        print("  ⚠️  No PDF files found in Data directory")
        return True  # Not fatal

    print(f"  ✓ Found {len(pdf_files)} PDF file(s) in Data/")
    for pdf in pdf_files:
        print(f"    - {pdf}")

    print("\n✅ Data directory is ready!\n")
    return True


def test_pinecone_version():
    """Check if Pinecone version is compatible."""
    print("Testing Pinecone version compatibility...")
    import pinecone

    version = pinecone.__version__
    major_version = int(version.split('.')[0])

    if major_version >= 9:
        print(f"  ⚠️  Warning: Pinecone version {version} may have compatibility issues")
        print("  Recommended: pinecone>=7.0.0,<8.0.0")
        return False
    elif major_version == 7:
        print(f"  ✓ Pinecone version {version} is compatible")
        print("\n✅ Pinecone version is correct!\n")
        return True
    else:
        print(f"  ⚠️  Warning: Pinecone version {version} is untested")
        return False


def test_pinecone_connection():
    """Test connection to Pinecone."""
    print("Testing Pinecone connection...")
    try:
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.environ.get('PINECONE_API_KEY')
        if not api_key or api_key.startswith('your-'):
            print("  ⚠️  Skipping connection test (API key not set)")
            return True

        from pinecone.grpc import PineconeGRPC as Pinecone
        pc = Pinecone(api_key=api_key)

        indexes = list(pc.list_indexes())
        print(f"  ✓ Connected to Pinecone successfully")
        print(f"  ✓ Found {len(indexes)} index(es)")

        # Check for medicalbot index
        index_names = [idx.name for idx in indexes]
        if 'medicalbot' in index_names:
            print("  ✓ 'medicalbot' index exists")

            # Check dimension
            try:
                index_info = pc.describe_index('medicalbot')
                if hasattr(index_info, 'dimension'):
                    dim = index_info.dimension
                    if dim == 768:
                        print(f"  ✓ Index dimension is {dim} (correct for Jina AI)")
                    elif dim == 384:
                        print(f"  ⚠️  Index dimension is {dim} (old sentence-transformers)")
                        print("     You need to delete and recreate the index with dimension=768")
                        print("     Then re-run: python store_index.py")
                    else:
                        print(f"  ⚠️  Index dimension is {dim} (unexpected)")
            except Exception:
                pass
        else:
            print("  ⚠️  'medicalbot' index not found. Run: python store_index.py")

        print("\n✅ Pinecone connection successful!\n")
        return True
    except Exception as e:
        print(f"  ❌ Pinecone connection failed: {e}")
        print("  Check your PINECONE_API_KEY in .env file")
        return False


def test_embedding_providers():
    """Test if embedding providers can be initialized."""
    print("Testing embedding providers...")
    from dotenv import load_dotenv
    load_dotenv()

    jina_ok = False
    hf_ok = False

    if os.environ.get('JINA_API_KEY') and not os.environ.get('JINA_API_KEY', '').startswith('your-'):
        try:
            from src.embeddings import JinaEmbeddingProvider
            provider = JinaEmbeddingProvider()
            print(f"  ✓ Jina AI embeddings: {provider.dimensions} dimensions")
            jina_ok = True
        except Exception as e:
            print(f"  ❌ Jina AI failed: {e}")
    else:
        print("  ⚠️  JINA_API_KEY not set (skipping)")

    if os.environ.get('HUGGINGFACE_API_KEY') and not os.environ.get('HUGGINGFACE_API_KEY', '').startswith('your-'):
        try:
            from src.embeddings import HuggingFaceEmbeddingProvider
            provider = HuggingFaceEmbeddingProvider()
            print(f"  ✓ HuggingFace Inference: {provider.dimensions} dimensions")
            hf_ok = True
        except Exception as e:
            print(f"  ❌ HuggingFace failed: {e}")
    else:
        print("  ⚠️  HUGGINGFACE_API_KEY not set (skipping)")

    if jina_ok or hf_ok:
        print("\n✅ At least one embedding provider is working!\n")
        return True
    else:
        print("\n❌ No embedding providers available!")
        print("  Set JINA_API_KEY or HUGGINGFACE_API_KEY in .env\n")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Medical Chatbot RAG v2.0.0 — Setup Verification")
    print("=" * 60)
    print()

    tests = [
        ("Package Imports", test_imports),
        ("Environment Configuration", test_env_file),
        ("Data Directory", test_data_directory),
        ("Pinecone Version", test_pinecone_version),
        ("Pinecone Connection", test_pinecone_connection),
        ("Embedding Providers", test_embedding_providers),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {e}\n")
            results.append((test_name, False))

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(result for _, result in results)

    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. If index is 384d: delete it and re-run: python store_index.py")
        print("  2. Run the application: python app.py")
        print("  3. Open browser: http://localhost:8080")
        print("  4. For Vercel deploy: vercel deploy")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nFor help, see: SETUP_GUIDE.md")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
