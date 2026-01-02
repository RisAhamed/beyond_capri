import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Central configuration for Beyond CAPRI.
    Strictly separates Cloud (Groq/Pinecone) and Local (Ollama/SQLite) configurations.
    """
    
    # --- PROJECT PATHS ---
    BASE_DIR = Path(__file__).resolve().parent
    LOCAL_DB_PATH = BASE_DIR / "local_env" / "pii_store.db"

    # --- CLOUD CREDENTIALS (GROQ & PINECONE) ---
    # strictly for reasoning and context retrieval, NO PII allowed here.
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "beyond-capri-context")

    # --- MODEL SETTINGS ---
    # Cloud Model: Ultra-fast reasoning, context-blind execution
    CLOUD_MODEL_NAME = "llama-3.3-70b-versatile"
    
    # Local Model: PII detection and Gatekeeper
    LOCAL_MODEL_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LOCAL_MODEL_NAME = "llama3.1:8b"

    # --- SYSTEM CONSTANTS ---
    # Semantic similarity threshold for verifying context anchors
    SIMILARITY_THRESHOLD = 0.8
    
    @staticmethod
    def validate():
        """Ensure critical API keys are present before starting."""
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing in .env")
        if not Config.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is missing in .env")

# Validation check on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Warning: {e}")