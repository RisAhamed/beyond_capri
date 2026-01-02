import os
import time
import logging
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorStore")

class ContextVectorStore:
    """
    Manages the storage and retrieval of 'Semantic Anchors' in Pinecone.
    Uses local embeddings to ensure privacy before data leaves the environment.
    """

    def __init__(self):
        # 1. Initialize Local Embeddings
        # We use a small, efficient model. Dimension = 384.
        # Ensure your Pinecone index is created with dimension=384.
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # 2. Initialize Pinecone Client
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.PINECONE_INDEX_NAME
        
        # Connect to the index
        if self.index_name not in [i.name for i in self.pc.list_indexes()]:
            logger.warning(f"Index '{self.index_name}' not found. Please create it in Pinecone console with dim=384.")
        self.index = self.pc.Index(self.index_name)

    def store_anchor(self, pseudonym_id: str, context_text: str, metadata: Dict[str, Any] = None):
        """
        Stores a semantic anchor.
        
        Args:
            pseudonym_id (str): The safe ID (e.g., "Patient_x9").
            context_text (str): The non-sensitive traits (e.g., "Female, 45 years old, hypertension").
            metadata (dict): Structured data for filtering.
        """
        try:
            # Generate Vector Locally
            vector = self.embeddings.embed_query(context_text)
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata["text"] = context_text
            metadata["type"] = "semantic_anchor"
            
            # Upsert to Pinecone
            self.index.upsert(vectors=[
                {
                    "id": pseudonym_id, 
                    "values": vector, 
                    "metadata": metadata
                }
            ])
            logger.info(f"Stored semantic anchor for {pseudonym_id}")
            
        except Exception as e:
            logger.error(f"Failed to store anchor: {e}")
            raise e

    def retrieve_context(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieves context based on semantic similarity.
        Used by the Cloud Coordinator to understand the 'meaning' of a pseudonym.
        """
        try:
            vector = self.embeddings.embed_query(query_text)
            results = self.index.query(
                vector=vector, 
                top_k=top_k, 
                include_metadata=True
            )
            
            matches = []
            for match in results['matches']:
                if match['score'] > Config.SIMILARITY_THRESHOLD:
                    matches.append({
                        "id": match['id'],
                        "score": match['score'],
                        "content": match['metadata'].get('text', '')
                    })
            return matches
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []

# Singleton instance
vector_store = ContextVectorStore()