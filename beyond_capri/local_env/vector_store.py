import time
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from config import Config

class AnchorStore:
    def __init__(self):
        # Initialize Pinecone Client
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.PINECONE_INDEX_NAME
        
        # Initialize Local Embedding Model (Small, fast model for converting text to vectors)
        # We use this locally to create the vector before sending to Cloud
        print("[Pinecone] Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Check if index exists, if not create it (Serverless)."""
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"[Pinecone] Index '{self.index_name}' not found. Creating...")
            try:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384, # Dimension for all-MiniLM-L6-v2
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                print(f"[Pinecone] Index '{self.index_name}' created successfully.")
            except Exception as e:
                print(f"[Pinecone] Error creating index: {e}")
        else:
            print(f"[Pinecone] Connected to existing index: '{self.index_name}'")

    def store_anchor(self, uuid: str, semantic_text: str):
        """
        Embeds the semantic context (e.g. 'Gender: Female') and pushes to Pinecone.
        """
        # 1. Create Vector (Embed the text)
        vector = self.model.encode(semantic_text).tolist()
        
        # 2. Upsert to Pinecone
        try:
            self.index.upsert(
                vectors=[
                    {
                        "id": uuid,
                        "values": vector,
                        "metadata": {"semantic_context": semantic_text}
                    }
                ]
            )
            print(f"[Pinecone] Semantic anchor stored for UUID: {uuid}")
        except Exception as e:
            print(f"[Pinecone] Error upserting anchor: {e}")

    def fetch_anchor(self, uuid: str):
        """
        Used by Cloud Coordinator to retrieve context.
        """
        try:
            result = self.index.fetch(ids=[uuid])
            if uuid in result.vectors:
                return result.vectors[uuid].metadata.get("semantic_context")
            return None
        except Exception as e:
            print(f"[Pinecone] Fetch error: {e}")
            return None
    
    def store_document_chunk(self, doc_id: str, clean_text: str, metadata: dict):
        """
        Uploads a SANITIZED document chunk to Cloud Pinecone.
        Usage: For RAG (Retrieval Augmented Generation).
        """
        # Embed the SAFE text
        vector = self.model.encode(clean_text).tolist()
        
        # Add a flag to distinguish Documents from Identity Anchors
        metadata["type"] = "document_knowledge"
        metadata["original_text"] = clean_text  # In production, this is the Safe Text
        
        try:
            self.index.upsert(
                vectors=[
                    {
                        "id": doc_id,
                        "values": vector,
                        "metadata": metadata
                    }
                ]
            )
            print(f"[Pinecone] Document chunk '{doc_id}' stored successfully.")
        except Exception as e:
            print(f"[Pinecone] Document upload error: {e}")

    def similarity_search(self, query_text: str, top_k=3):
        """
        Used by the Cloud Agent to find relevant document info.
        """
        vector = self.model.encode(query_text).tolist()
        try:
            results = self.index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter={"type": "document_knowledge"} # Only search docs, not people anchors
            )
            return [match['metadata']['original_text'] for match in results['matches']]
        except Exception as e:
            print(f"[Pinecone] Search error: {e}")
            return []

# Simple test
if __name__ == "__main__":
    store = AnchorStore()
    store.store_anchor("test-uuid-123", "Gender: Female, Condition: Huntington's")