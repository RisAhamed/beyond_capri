from langchain_core.tools import tool

@tool
def search_patient_database(patient_id: str):
    """
    Searches the hospital database for a patient by their ID.
    Returns the patient record.
    """
    print(f"\n[Cloud Tool] Worker is searching DB for: {patient_id}")
    
    # --- SIMULATION OF "CONTEXTUAL COLLAPSE" ---
    # In a real scenario, the tool might return pseudonymized data that 
    # accidentally conflicts with the real gender (e.g. "David" for a female).
    
    # We simulate this failure point intentionally:
    mock_record = {
        "id": patient_id,
        "name": "David Smith",   # <--- MALE NAME
        "gender": "Male",        # <--- CONTRADICTION (Real user is Female Sarah)
        "age": 45,
        "status": "Active"
    }
    
    print(f"[Cloud Tool] Returning Record: {mock_record}")
    return mock_record  