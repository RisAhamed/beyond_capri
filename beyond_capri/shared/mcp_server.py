import json
import os
from langchain_core.tools import tool

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cloud_env", "cloud_db.json")

def load_db():
    if not os.path.exists(DB_PATH): return {}
    with open(DB_PATH, 'r') as f: return json.load(f)

@tool
def get_account_balance(account_id: str):
    """
    Retrieves the balance for a given account ID.
    """
    print(f"\n[MCP Bank] Checking balance for: {account_id}")
    data = load_db()
    # Logic to find account (Simulated for demo)
    # In a real app, you'd match the exact ID. For this demo, we return a default if missing.
    record = next((acc for acc in data.get("accounts", []) if acc["id"] == account_id), None)
    
    if not record:
        # Fallback to the first record for demo continuity if UUID creates a mismatch
        record = data["accounts"][0]
        record["id"] = account_id # Temporarily align ID for the agent
        
    print(f"[MCP Bank] Found Record: {record['holder_name']} | ${record['balance']}")
    return record

@tool
def transfer_funds(sender_id: str, receiver_id: str, amount: float):
    """
    Transfers money between two accounts.
    """
    print(f"\n[MCP Bank] Transferring ${amount} from {sender_id} to {receiver_id}")
    # In a real app, you would subtract/add to the JSON balance here.
    return {
        "status": "success", 
        "transaction_id": "TXN_998877", 
        "message": f"Successfully transferred ${amount}. New Sender Balance: Hidden"
    }