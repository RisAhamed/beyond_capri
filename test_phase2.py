import time
from beyond_capri.local_env.gatekeeper import Gatekeeper
from beyond_capri.local_env.db_manager import IdentityVault
from beyond_capri.local_env.vector_store import AnchorStore

def run_phase2_test():
    print("=== STARTING PHASE 2: GATEKEEPER TEST ===\n")
    
    # 1. Setup
    gk = Gatekeeper()
    vault = IdentityVault()
    store = AnchorStore()

    # 2. Simulating User Input
    # This input has NAME, GENDER context ("her"), and MEDICAL context ("flu")
    user_input = "Please schedule a follow-up for Sarah Jones. She is recovering from the flu."
    print(f"INPUT: {user_input}\n")

    # 3. Run Gatekeeper
    print("--- Running Sanitization ---")
    safe_output = gk.detect_and_sanitize(user_input)
    print(f"\nSAFE OUTPUT TO CLOUD: \"{safe_output}\"\n")

    # 4. Verification
    # Extract the UUID from the safe output (Simple logic for testing)
    # We look for the string starting with 'Entity_'
    import re
    match = re.search(r"Entity_[a-f0-9]{8}", safe_output)
    
    if match:
        uuid_found = match.group(0)
        print(f"--- Verifying Data for {uuid_found} ---")
        
        # Check Local Vault (Should have "Sarah Jones")
        real_data = vault.get_real_identity(uuid_found)
        print(f"[Local Vault] Found: {real_data}")
        
        if real_data and "Sarah Jones" in real_data.get("original_text", ""):
             print("✅ SUCCESS: Real identity saved locally.")
        else:
             print("❌ FAILURE: Real identity lost.")

        # Check Cloud Pinecone (Should have "flu" but NOT "Sarah")
        # Note: Vector DB takes a second to index, so we wait briefly
        time.sleep(2) 
        context_anchor = store.fetch_anchor(uuid_found)
        print(f"[Cloud Anchor] Found: {context_anchor}")
        
        if context_anchor and "flu" in context_anchor:
            print("✅ SUCCESS: Context anchor saved to Cloud.")
        else:
            print("❌ FAILURE: Cloud context missing.")

    else:
        print("❌ FAILURE: No UUID generated in output.")

    print("\n=== PHASE 2 COMPLETE ===")

if __name__ == "__main__":
    run_phase2_test()