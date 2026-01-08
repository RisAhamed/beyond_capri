import uuid
from beyond_capri.local_env.db_manager import IdentityVault
from beyond_capri.local_env.vector_store import AnchorStore

def run_phase1_test():
    print("=== STARTING PHASE 1 SYSTEM CHECK ===\n")

    # 1. Generate Dummy Data
    test_uuid = f"user_{str(uuid.uuid4())[:8]}"
    real_pii = {"name": "Alice Johnson", "email": "alice@example.com"}
    semantic_anchor = "Gender: Female, Role: Patient, Condition: High Priority"
    
    print(f"Test UUID: {test_uuid}")
    print(f"Real Data: {real_pii}")
    print(f"Context:   {semantic_anchor}\n")

    # 2. Test Local Vault (SQLite)
    print("--- Testing Local SQLite Vault ---")
    vault = IdentityVault()
    vault.save_identity(test_uuid, real_pii)
    
    retrieved_data = vault.get_real_identity(test_uuid)
    if retrieved_data == real_pii:
        print("SUCCESS: Data saved and retrieved from Local Vault correctly.")
    else:
        print("FAILURE: Data mismatch in Local Vault.")
    print("\n")

    # 3. Test Cloud Vector Store (Pinecone)
    print("--- Testing Cloud Pinecone Store ---")
    store = AnchorStore()
    store.store_anchor(test_uuid, semantic_anchor)
    
    # Wait a moment for eventual consistency in vector DB
    import time
    time.sleep(2)
    
    retrieved_context = store.fetch_anchor(test_uuid)
    if retrieved_context == semantic_anchor:
        print("SUCCESS: Context anchor saved and fetched from Pinecone correctly.")
    else:
        print(f"FAILURE: Context mismatch. Got: {retrieved_context}")
    
    print("\n=== PHASE 1 CHECK COMPLETE ===")

if __name__ == "__main__":
    run_phase1_test()