import re
import uuid
from beyond_capri.cloud_env.a2a_orchestrator import A2AOrchestrator
from beyond_capri.local_env.gatekeeper import Gatekeeper
from beyond_capri.local_env.db_manager import IdentityVault

def re_identify_response(text: str, vault: IdentityVault) -> str:
    """
    PHASE 4 MAGIC: Scans the text for UUIDs, looks them up in the Vault,
    and replaces the fake pseudonym context with Real Data.
    """
    print("\n[Re-ID Layer] Scanning output for UUIDs to restore real identities...")
    
    # Regex to find UUID-like strings (both 'Entity_...' and raw 8-char hex)
    # Adjust regex to match the UUID format your system generates
    matches = re.findall(r"(Entity_)?[a-f0-9]{8}", text)
    
    # Clean matches to get the full raw UUID string found in text
    # We re-run a simpler regex to capture the exact substrings to replace
    exact_matches = re.findall(r"Entity_[a-f0-9]{8}|[a-f0-9]{8}", text)
    
    final_text = text
    
    for match_str in exact_matches:
        # Try to find this ID in the database
        # Note: Sometimes the tool strips 'Entity_', so we check both variations
        real_identity = vault.get_real_identity(match_str)
        
        # If not found directly, try adding/removing prefix
        if not real_identity:
            if "Entity_" in match_str:
                real_identity = vault.get_real_identity(match_str.replace("Entity_", ""))
            else:
                real_identity = vault.get_real_identity(f"Entity_{match_str}")

        if real_identity:
            original_name = real_identity.get("original_text", "Unknown")
            print(f"   -> Found UUID '{match_str}'. Restoring to '{original_name}'")
            
            # 1. Replace the UUID with the Name
            final_text = final_text.replace(match_str, original_name)
            
            # 2. CLEANUP: Remove the fake "David Smith" artifacts if possible
            # (Simple heuristic: If we restored 'Sarah', replace 'David Smith' with 'Sarah')
            final_text = final_text.replace("David Smith", original_name)
            final_text = final_text.replace("Male", real_identity.get("full_context", "").split(",")[0])
            
    return final_text

def main():
    print("===============================================================")
    print("   BEYOND CAPRI: PRIVACY-PRESERVING A2A FRAMEWORK (LIVE)      ")
    print("===============================================================")
    
    # 1. Initialize Components
    gatekeeper = Gatekeeper()
    orchestrator = A2AOrchestrator()
    vault = IdentityVault()
    
    # 2. Get User Input
    print("\nENTER PROMPT (e.g., 'Book appointment for Sarah...'):")
    user_input = input("> ")
    if not user_input:
        user_input = "Please schedule a follow-up for Sarah Jones. She is a female patient."
    
    # --- PHASE 2: LOCAL SHIELD ---
    print(f"\n[1] LOCAL SHIELD: Detecting PII...")
    safe_prompt = gatekeeper.detect_and_sanitize(user_input)
    print(f"    Safe Prompt sent to Cloud: \"{safe_prompt}\"")
    
    # --- PHASE 3: CLOUD A2A REASONING ---
    print(f"\n[2] CLOUD TEAM: Reasoning & Execution...")
    try:
        result = orchestrator.run(safe_prompt)
        raw_cloud_response = result['final_response']
        print(f"\n[Raw Cloud Response (Internal)]:\n{raw_cloud_response}")
    except Exception as e:
        print(f"Cloud Error: {e}")
        return

    # --- PHASE 4: RE-IDENTIFICATION ---
    print(f"\n[3] LOCAL BRIDGE: Restoring Real Identity...")
    final_user_output = re_identify_response(raw_cloud_response, vault)
    
    print("\n" + "="*60)
    print("FINAL USER RESULT:")
    print("="*60)
    print(final_user_output)
    print("="*60)

if __name__ == "__main__":
    main()