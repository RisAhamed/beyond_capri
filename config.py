import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    # Pinecone Config
    PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "beyond-capri-context")
    
    # Local Paths
    DB_PATH = os.path.join(os.path.dirname(__file__), "beyond_capri", "local_env", "identity_vault.db")

    # Validation
    if not PINECONE_API_KEY:
        raise ValueError("Missing PINECONE_API_KEY in .env file")

print(f"Configuration Loaded. DB Path: {Config.DB_PATH}")