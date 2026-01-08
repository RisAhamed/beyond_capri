from langchain_core.tools import tool
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from config import Config

# Initialize Cloud-Side Resources
pc = Pinecone(api_key=Config.PINECONE_API_KEY)
index = pc.Index(Config.PINECONE_INDEX_NAME)
model = SentenceTransformer('all-MiniLM-L6-v2')

@tool
def search_knowledge_base(query: str):
    """
    Searches the Cloud Knowledge Base (Document Policies).
    Use this to check transfer limits, account rules, or compliance policies.
    """
    print(f"\n[Cloud Tool] Searching Knowledge Base for: '{query}'")
    
    # Embed query
    vector = model.encode(query).tolist()
    
    try:
        # Search Pinecone for 'document_knowledge' only
        results = index.query(
            vector=vector,
            top_k=2,
            include_metadata=True,
            filter={"type": "document_knowledge"} 
        )
        
        # Extract text
        matches = [match['metadata']['original_text'] for match in results['matches']]
        
        if not matches:
            return "No relevant policies found."
            
        return "\n\n".join(matches)
        
    except Exception as e:
        return f"Search Error: {e}"