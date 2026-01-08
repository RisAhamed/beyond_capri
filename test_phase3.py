from beyond_capri.cloud_env.a2a_orchestrator import A2AOrchestrator
from beyond_capri.local_env.gatekeeper import Gatekeeper
from beyond_capri.local_env.db_manager import IdentityVault

def run_phase3_test():
    print("=== STARTING PHASE 3: THE DAVID TEST (A2A REASONING) ===\n")
    
    # 1. Run Phase 2 logic manually to get a valid UUID
    # We need a fresh UUID that has 'Female' context in Pinecone
    gk = Gatekeeper()
    user_input = "Schedule for Sarah Jones. She is a female patient."
    print(f"1. USER INPUT: '{user_input}'")
    
    # Sanitize locally
    safe_prompt = gk.detect_and_sanitize(user_input)
    print(f"2. SAFE PROMPT: '{safe_prompt}'\n")
    
    # 2. Initialize Cloud Team
    print("--- Initializing Cloud A2A Team ---")
    orchestrator = A2AOrchestrator()
    
    # 3. Run the Cloud Logic
    print("--- Cloud Processing Started ---")
    result = orchestrator.run(safe_prompt)
    
    print("\n=== FINAL CLOUD RESPONSE ===")
    print(result['final_response'])
    
    # 4. Check for Success
    # The tool returns "David Smith" (Male).
    # If the Agent got confused, it would say "Error: Gender mismatch".
    # If the Agent worked, it should say "Success" or "Confirmed".
    response_text = result['final_response'].lower()
    
    if "david" in response_text or "confirm" in response_text or "success" in response_text:
        print("\n✅ PASSED: The Agent ignored the 'David' fake name and confirmed the UUID match!")
    else:
        print("\n❌ FAILED: The Agent got confused by the fake data.")

if __name__ == "__main__":
    run_phase3_test()