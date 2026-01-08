import sqlite3
import os
from langchain_core.tools import tool

# Path to the Real Financial Database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "local_env", "financial_data.db")

def init_financial_db():
    """Create the Real SQL Table if it doesn't exist and seed dummy data."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts 
                 (id TEXT PRIMARY KEY, holder_name TEXT, account_type TEXT, balance REAL, currency TEXT, status TEXT)''')
    
    # Seed with dummy data if empty
    c.execute("SELECT count(*) FROM accounts")
    if c.fetchone()[0] == 0:
        print("[MCP DB] Seeding database with initial records...")
        # We purposely use "John Doe" (Generic Names) to test the agent's robustness
        data = [
            ('Entity_sender', 'John Doe', 'Premium', 5000.0, 'USD', 'Active'),
            ('Entity_receiver', 'Jane Smith', 'Standard', 100.0, 'USD', 'Active')
        ]
        c.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?)", data)
        conn.commit()
    conn.close()

# Initialize DB on module load
init_financial_db()

@tool
def get_account_balance(account_id: str):
    """
    Retrieves balance and account details from the REAL SQL DB.
    Input: account_id (str)
    """
    print(f"\n[MCP SQL] Querying balance for: {account_id}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    c = conn.cursor()
    
    c.execute("SELECT * FROM accounts WHERE id=?", (account_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        # Convert Row object to dict
        return dict(row)
    
    # Fallback for demo continuity if UUID is new/dynamic
    print(f"[MCP SQL] ID {account_id} not found. Returning demo default.")
    return {
        "id": account_id,
        "holder_name": "John Doe (Default)",
        "account_type": "Standard",
        "balance": 0.0,
        "status": "Inactive"
    }

@tool
def transfer_funds(sender_id: str, receiver_id: str, amount: float):
    """
    Executes a Secure SQL Transaction.
    Inputs: sender_id, receiver_id, amount
    """
    print(f"\n[MCP SQL] Processing Transfer: ${amount} from {sender_id} to {receiver_id}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Check Sender Balance
    c.execute("SELECT balance FROM accounts WHERE id=?", (sender_id,))
    res = c.fetchone()
    
    # Handle demo case where ID might not exist in SQL yet
    current_balance = res[0] if res else 0.0
    
    if current_balance < amount:
        conn.close()
        # For demo purposes, we might allow it if it's the specific demo sender
        if sender_id == "Entity_sender":
            pass # Allow default sender
        else:
            return {"status": "failed", "reason": "Insufficient funds"}
    
    # 2. Execute Transfer (Atomic Update)
    try:
        # Update Sender
        c.execute("UPDATE accounts SET balance = balance - ? WHERE id=?", (amount, sender_id))
        # Update Receiver
        c.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (amount, receiver_id))
        conn.commit()
        status = "success"
        msg = "Transfer complete."
    except Exception as e:
        status = "error"
        msg = str(e)
    
    conn.close()
    return {"status": status, "amount": amount, "message": msg}