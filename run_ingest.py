"""
Wrapper script to run document ingestion from the project root.
This ensures proper module resolution for beyond_capri package.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run
from beyond_capri.local_env.ingest_docs import ingest_documents

if __name__ == "__main__":
    ingest_documents()
