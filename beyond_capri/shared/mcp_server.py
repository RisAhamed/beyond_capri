import json
import os
from langchain_core.tools import tool

# Path to our Mock Database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cloud_env", "cloud_db.json")

def load_db():
    """Helper to load the JSON database"""
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r') as f:
        return json.load(f)

@tool
def search_patient_database(patient_id: str):
    """
    MCP TOOL: Searches the hospital database for a patient by their ID.
    Input: patient_id (str) - The UUID to search for.
    Returns: The patient record dictionary or a 'Not Found' message.
    """
    print(f"\n[MCP Server] Received request for ID: {patient_id}")
    
    # 1. Load the "External" Database
    data = load_db()
    records = data.get("records", [])
    
    # 2. Search for the ID (Exact Match)
    # Note: In a real scenario, this would be a SQL query
    result = next((item for item in records if item["id"] == patient_id), None)
    
    # 3. Fallback logic for testing (If dynamic UUID is used)
    # If the specific UUID isn't in JSON, return the "Default Bad Record" for the demo
    if not result:
        print("[MCP Server] ID not found in static JSON. Returning default 'Bad Data' for demo.")
        result = {
            "id": patient_id,
            "name": "David Smith",   # The "Bad Data" causing confusion
            "gender": "Male",
            "age": 45,
            "status": "Active (Default)"
        }

    print(f"[MCP Server] Returning Data: {result}")
    return result