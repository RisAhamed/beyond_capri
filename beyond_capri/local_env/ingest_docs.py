import os
import uuid
from beyond_capri.local_env.gatekeeper import Gatekeeper
from beyond_capri.local_env.vector_store import AnchorStore

# Define where your raw documents live
DOCS_DIR = os.path.join(os.path.dirname(__file__), "raw_documents")

def ingest_documents():
    print("=== STARTING SECURE DOCUMENT INGESTION ===")
    
    # 1. Initialize Components
    gk = Gatekeeper()
    store = AnchorStore()
    
    # Ensure directory exists
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"Created folder: {DOCS_DIR}. Please put .txt files there and run again.")
        return

    # 2. Iterate through files
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            file_path = os.path.join(DOCS_DIR, filename)
            print(f"\nProcessing File: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # 3. CRITICAL: Sanitize BEFORE Uploading
            # This ensures Cloud Pinecone never sees real names in your docs
            print("   -> Sanitizing content...")
            safe_content = gk.detect_and_sanitize(raw_content)
            
            # 4. Chunking (Simple split for demo)
            # In production, use LangChain's RecursiveCharacterTextSplitter
            chunks = [safe_content[i:i+500] for i in range(0, len(safe_content), 500)]
            
            # 5. Upload to Cloud
            print(f"   -> Uploading {len(chunks)} chunks to Cloud...")
            for i, chunk in enumerate(chunks):
                chunk_id = f"doc_{filename}_{i}_{str(uuid.uuid4())[:4]}"
                store.store_document_chunk(
                    doc_id=chunk_id, 
                    clean_text=chunk,
                    metadata={"source": filename, "chunk_index": i}
                )
    
    print("\n=== INGESTION COMPLETE ===")

if __name__ == "__main__":
    ingest_documents()