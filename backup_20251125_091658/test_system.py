"""
Test script to verify all components are working
Run this after setup to check if everything is configured correctly
"""
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required packages are installed"""
    print("\n" + "="*80)
    print("Testing Package Imports")
    print("="*80)
    
    required_packages = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('sentence_transformers', 'Sentence Transformers'),
        ('chromadb', 'ChromaDB'),
        ('gradio', 'Gradio'),
        ('datasets', 'Datasets'),
        ('peft', 'PEFT'),
    ]
    
    failed = []
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT INSTALLED")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All packages installed correctly")
        return True


def test_device():
    """Test device availability"""
    print("\n" + "="*80)
    print("Testing Device Configuration")
    print("="*80)
    
    try:
        import torch
        
        print(f"PyTorch version: {torch.__version__}")
        
        if torch.backends.mps.is_available():
            print("✓ MPS (Apple Silicon) available")
            device = "mps"
        elif torch.cuda.is_available():
            print("✓ CUDA available")
            device = "cuda"
        else:
            print("⚠ Using CPU (MPS/CUDA not available)")
            device = "cpu"
        
        print(f"Default device: {device}")
        return True
    except Exception as e:
        print(f"❌ Error testing device: {e}")
        return False


def test_directories():
    """Test if required directories exist"""
    print("\n" + "="*80)
    print("Testing Directory Structure")
    print("="*80)
    
    from config import DATA_DIR, MODELS_DIR, VECTOR_DB_DIR, LOGS_DIR
    
    dirs = {
        'Data': DATA_DIR,
        'Models': MODELS_DIR,
        'Vector DB': VECTOR_DB_DIR,
        'Logs': LOGS_DIR
    }
    
    for name, path in dirs.items():
        if path.exists():
            print(f"✓ {name} directory: {path}")
        else:
            print(f"⚠ {name} directory missing (will be created): {path}")
    
    return True


def test_data_files():
    """Test if data files exist"""
    print("\n" + "="*80)
    print("Testing Data Files")
    print("="*80)
    
    from config import DATA_DIR
    
    files = {
        'Knowledge Base': DATA_DIR / 'rackspace_knowledge.json',
        'Training Data': DATA_DIR / 'training_data.jsonl',
    }
    
    missing = []
    for name, path in files.items():
        if path.exists():
            size = path.stat().st_size / 1024  # KB
            print(f"✓ {name}: {path.name} ({size:.1f} KB)")
        else:
            print(f"✗ {name}: Not found")
            missing.append(name)
    
    if missing:
        print(f"\n⚠ Missing files: {', '.join(missing)}")
        print("Run the build pipeline:")
        print("  python data_collection.py")
        print("  python prepare_dataset.py")
        return False
    else:
        print("\n✅ All data files present")
        return True


def test_vector_db():
    """Test vector database"""
    print("\n" + "="*80)
    print("Testing Vector Database")
    print("="*80)
    
    try:
        from vector_db import VectorDBManager
        
        db = VectorDBManager()
        stats = db.get_stats()
        
        print(f"✓ Vector database initialized")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Embedding model: {stats['embedding_model']}")
        
        if stats['total_chunks'] == 0:
            print("\n⚠ Vector database is empty")
            print("Run: python vector_db.py")
            return False
        else:
            # Test retrieval
            results = db.search("What is Rackspace?", top_k=1)
            if results:
                print(f"✓ Retrieval test successful")
                print(f"  Found {len(results)} relevant documents")
                print("\n✅ Vector database working correctly")
                return True
            else:
                print("⚠ Retrieval test returned no results")
                return False
                
    except Exception as e:
        print(f"❌ Error testing vector database: {e}")
        print("Run: python vector_db.py")
        return False


def test_model():
    """Test model loading"""
    print("\n" + "="*80)
    print("Testing Model Loading")
    print("="*80)
    
    try:
        from config import FINE_TUNED_MODEL_PATH, BASE_MODEL_NAME
        from transformers import AutoTokenizer
        
        if FINE_TUNED_MODEL_PATH.exists():
            print(f"✓ Fine-tuned model found at: {FINE_TUNED_MODEL_PATH}")
            model_path = str(FINE_TUNED_MODEL_PATH)
        else:
            print(f"⚠ Fine-tuned model not found")
            print(f"  Will use base model: {BASE_MODEL_NAME}")
            model_path = BASE_MODEL_NAME
        
        print(f"  Loading tokenizer from: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        print(f"✓ Tokenizer loaded successfully")
        print(f"  Vocabulary size: {len(tokenizer)}")
        
        print("\n✅ Model can be loaded")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 RACKSPACE CHATBOT - SYSTEM TEST")
    print("="*80)
    
    tests = [
        ("Package Imports", test_imports),
        ("Device Configuration", test_device),
        ("Directory Structure", test_directories),
        ("Data Files", test_data_files),
        ("Vector Database", test_vector_db),
        ("Model Loading", test_model),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("\nYour chatbot is ready to use!")
        print("Run: python app.py")
        print("="*80)
        return True
    else:
        print("\n" + "="*80)
        print("⚠ SOME TESTS FAILED")
        print("="*80)
        print("\nPlease address the issues above before running the chatbot.")
        print("\nCommon solutions:")
        print("1. Missing packages: pip install -r requirements.txt")
        print("2. Missing data: ./build_pipeline.sh")
        print("3. Missing vector DB: python vector_db.py")
        print("="*80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
