"""
Test script to verify the installation and setup
Run this after setup to ensure everything is working correctly
"""
import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...")
    try:
        import flask
        print("  ✓ Flask")
        import langchain
        print("  ✓ LangChain")
        import pinecone
        print(f"  ✓ Pinecone (version: {pinecone.__version__})")
        import langchain_pinecone
        print("  ✓ LangChain-Pinecone")
        import langchain_huggingface
        print("  ✓ LangChain-HuggingFace")
        import sentence_transformers
        print("  ✓ Sentence Transformers")
        from dotenv import load_dotenv
        print("  ✓ Python-dotenv")
        import google.protobuf
        print("  ✓ Protobuf (gRPC support)")
        print("\n✅ All required packages are installed!\n")
        return True
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_env_file():
    """Test if .env file exists and has required keys"""
    print("Testing .env configuration...")
    if not os.path.exists('.env'):
        print("  ❌ .env file not found!")
        print("  Copy .env.example to .env and add your API keys")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = ['PINECONE_API_KEY', 'OPENROUTER_API_KEY', 'SECRET_KEY']
    missing_keys = []
    
    for key in required_keys:
        value = os.environ.get(key)
        if not value or value.startswith('your-'):
            missing_keys.append(key)
        else:
            print(f"  ✓ {key} is set")
    
    if missing_keys:
        print(f"\n  ❌ Missing or invalid keys: {', '.join(missing_keys)}")
        print("  Please update your .env file with actual API keys")
        return False
    
    print("\n✅ Environment variables configured!\n")
    return True

def test_data_directory():
    """Test if Data directory and medical PDF exist"""
    print("Testing data directory...")
    if not os.path.exists('Data'):
        print("  ❌ Data directory not found!")
        return False
    
    pdf_files = [f for f in os.listdir('Data') if f.endswith('.pdf')]
    if not pdf_files:
        print("  ❌ No PDF files found in Data directory!")
        return False
    
    print(f"  ✓ Found {len(pdf_files)} PDF file(s) in Data/")
    for pdf in pdf_files:
        print(f"    - {pdf}")
    
    print("\n✅ Data directory is ready!\n")
    return True

def test_pinecone_version():
    """Check if Pinecone version is compatible"""
    print("Testing Pinecone version compatibility...")
    import pinecone
    
    version = pinecone.__version__
    major_version = int(version.split('.')[0])
    
    if major_version >= 9:
        print(f"  ⚠️  Warning: Pinecone version {version} may have compatibility issues")
        print("  Recommended: pinecone>=7.0.0,<8.0.0")
        print("  Run: pip install 'pinecone>=7.0.0,<8.0.0'")
        return False
    elif major_version == 7:
        print(f"  ✓ Pinecone version {version} is compatible")
        print("\n✅ Pinecone version is correct!\n")
        return True
    else:
        print(f"  ⚠️  Warning: Pinecone version {version} is untested")
        return False

def test_pinecone_connection():
    """Test connection to Pinecone"""
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
        else:
            print("  ⚠️  'medicalbot' index not found. Run: python store_index.py")
        
        print("\n✅ Pinecone connection successful!\n")
        return True
    except Exception as e:
        print(f"  ❌ Pinecone connection failed: {e}")
        print("  Check your PINECONE_API_KEY in .env file")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Medical Chatbot RAG - Setup Verification")
    print("=" * 60)
    print()
    
    tests = [
        ("Package Imports", test_imports),
        ("Environment Configuration", test_env_file),
        ("Data Directory", test_data_directory),
        ("Pinecone Version", test_pinecone_version),
        ("Pinecone Connection", test_pinecone_connection),
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
        print("  1. If you haven't initialized the database: python store_index.py")
        print("  2. Run the application: python app.py")
        print("  3. Open browser: http://localhost:8080")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nFor help, see: SETUP_GUIDE.md")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
