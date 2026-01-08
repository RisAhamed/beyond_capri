import time
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from config import Config

class AnchorStore:
    def __init__(self):
        # Initialize Pinecone Client
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.PINECONE_INDEX_NAME
        
        # Initialize Local Embedding Model
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
                    dimension=384, 
                    metric='cosine',
                    spec=ServerlessSpec(cloud='aws', region='us-east-1')
                )
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                print(f"[Pinecone] Index '{self.index_name}' created successfully.")
            except Exception as e:
                print(f"[Pinecone] Error creating index: {e}")
        else:
            print(f"[Pinecone] Connected to existing index: '{self.index_name}'")

    def store_anchor(self, uuid: str, semantic_text: str):
        """Stores Identity Anchors (e.g., 'User_x9 is Female')"""
        vector = self.model.encode(semantic_text).tolist()
        try:
            self.index.upsert(
                vectors=[{
                    "id": uuid,
                    "values": vector,
                    "metadata": {"semantic_context": semantic_text, "type": "identity"}
                }]
            )
            print(f"[Pinecone] Identity Anchor stored for UUID: {uuid}")
        except Exception as e:
            print(f"[Pinecone] Error upserting anchor: {e}")

    def fetch_anchor(self, uuid: str):
        """Used to retrieve Identity Context"""
        try:
            result = self.index.fetch(ids=[uuid])
            if uuid in result.vectors:
                return result.vectors[uuid].metadata.get("semantic_context")
            return None
        except Exception as e:
            print(f"[Pinecone] Fetch error: {e}")
            return None

    # --- NEW RAG CAPABILITIES ---
    def store_document_chunk(self, doc_id: str, clean_text: str, metadata: dict):
        """
        Uploads a SANITIZED document chunk to Cloud Pinecone for RAG.
        """
        vector = self.model.encode(clean_text).tolist()
        
        # Mark as 'document_knowledge' so we don't confuse it with people
        metadata["type"] = "document_knowledge"
        metadata["original_text"] = clean_text 
        
        try:
            self.index.upsert(
                vectors=[{
                    "id": doc_id,
                    "values": vector,
                    "metadata": metadata
                }]
            )
            print(f"[Pinecone] Document chunk '{doc_id}' stored successfully.")
        except Exception as e:
            print(f"[Pinecone] Document upload error: {e}")