"""
Configuration file for Rackspace Knowledge Chatbot
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
VECTOR_DB_DIR = PROJECT_ROOT / "vector_db"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories
for dir_path in [DATA_DIR, MODELS_DIR, VECTOR_DB_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Model configuration
BASE_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Small, efficient model for M3 Mac
# Alternative: "microsoft/phi-2" (2.7B parameters)
FINE_TUNED_MODEL_PATH = MODELS_DIR / "rackspace_finetuned"

# Embedding model for RAG
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Fast and efficient

# Vector database configuration
VECTOR_DB_NAME = "rackspace_knowledge"
COLLECTION_NAME = "rackspace_docs"
CHUNK_SIZE = 512  # Size of text chunks for embedding
CHUNK_OVERLAP = 50  # Overlap between chunks
TOP_K_RETRIEVAL = 5  # Number of relevant documents to retrieve

# Fine-tuning configuration
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
BATCH_SIZE = 4  # Optimized for 16GB RAM
GRADIENT_ACCUMULATION_STEPS = 4
NUM_EPOCHS = 3
MAX_LENGTH = 512
WARMUP_STEPS = 100

# Generation configuration
MAX_NEW_TOKENS = 256
TEMPERATURE = 0.7
TOP_P = 0.9
DO_SAMPLE = True

# Chat history configuration
MAX_HISTORY_LENGTH = 5  # Number of conversation turns to maintain

# Data collection URLs - Comprehensive coverage of ALL Rackspace domains
RACKSPACE_URLS = [
    # Main website - complete sections
    "https://www.rackspace.com/",
    "https://www.rackspace.com/cloud",
    "https://www.rackspace.com/cloud-services",
    "https://www.rackspace.com/managed-services",
    "https://www.rackspace.com/professional-services",
    "https://www.rackspace.com/security",
    "https://www.rackspace.com/data-services",
    "https://www.rackspace.com/solutions",
    "https://www.rackspace.com/applications",
    "https://www.rackspace.com/multicloud",
    "https://www.rackspace.com/company",
    "https://www.rackspace.com/blog",
    "https://www.rackspace.com/resources",
    "https://www.rackspace.com/industries",
    "https://www.rackspace.com/partners",
    
    # Documentation sites - comprehensive technical docs
    "https://docs.rackspace.com/",
    "https://docs.rackspace.com/docs",
    "https://docs-ospc.rackspace.com/",
    
    # Developer resources
    "https://developer.rackspace.com/",
    "https://developer.rackspace.com/docs",
    
    # Product-specific
    "https://www.rackspace.com/aws",
    "https://www.rackspace.com/microsoft-azure",
    "https://www.rackspace.com/google-cloud",
    "https://www.rackspace.com/vmware",
    "https://www.rackspace.com/openstack",
    
    # SPOT marketplace
    "https://spot.rackspace.com/",
    "https://spot.rackspace.com/innovations",
]

# Allowed domains for crawling (BFS will stay within these)
ALLOWED_DOMAINS = [
    "rackspace.com",
    "docs.rackspace.com",
    "docs-ospc.rackspace.com",
    "spot.rackspace.com",
    "www.rackspace.com",
    "developer.rackspace.com",
]

# Enhanced crawling configuration for comprehensive data collection
MAX_CRAWL_DEPTH = 4  # Go deeper for better coverage
MAX_PAGES_PER_DOMAIN = 200  # More pages per domain
CRAWL_DELAY = 0.5  # Faster crawling (still polite)
REQUEST_TIMEOUT = 20  # Longer timeout for complex pages
MIN_CONTENT_LENGTH = 200  # Minimum text length to be useful

# Device configuration (for M3 Mac)
DEVICE = "mps"  # Metal Performance Shaders for Apple Silicon
USE_MPS = True
