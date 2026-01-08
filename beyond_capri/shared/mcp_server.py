import sqlite3
import os
from langchain_core.tools import tool
from config import Config

# Using the existing config path or a new one for Financial Data
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "local_env", "financial_data.db")

def init_financial_db():
    """Create the Real SQL Table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts 
                 (id TEXT PRIMARY KEY, holder_name TEXT, balance REAL, currency TEXT, status TEXT)''')
    
    # Seed with some dummy data if empty
    c.execute("SELECT count(*) FROM accounts")
    if c.fetchone()[0] == 0:
        # Note: We store "Bad Data" (John Doe) here to test the agent, just like before
        c.execute("INSERT INTO accounts VALUES ('Entity_sender', 'John Doe', 5000.0, 'USD', 'Active')")
        c.execute("INSERT INTO accounts VALUES ('Entity_receiver', 'Jane Smith', 100.0, 'USD', 'Active')")
        conn.commit()
    conn.close()

# Initialize on load
init_financial_db()

@tool
def get_account_balance(account_id: str):
    """Retrieves balance from REAL SQL DB."""
    print(f"\n[MCP SQL] Querying balance for: {account_id}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    c = conn.cursor()
    
    c.execute("SELECT * FROM accounts WHERE id=?", (account_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {"error": "Account not found", "id": account_id}

@tool
def transfer_funds(sender_id: str, receiver_id: str, amount: float):
    """Executes SQL Transaction."""
    print(f"\n[MCP SQL] Processing Transfer: ${amount}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Check Balance
    c.execute("SELECT balance FROM accounts WHERE id=?", (sender_id,))
    res = c.fetchone()
    if not res or res[0] < amount:
        conn.close()
        return {"status": "failed", "reason": "Insufficient funds"}
    
    # 2. Execute Transfer (Atomic)
    try:
        c.execute("UPDATE accounts SET balance = balance - ? WHERE id=?", (amount, sender_id))
        c.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (amount, receiver_id))
        conn.commit()
        status = "success"
    except Exception as e:
        status = f"error: {e}"
    
    conn.close()
    return {"status": status, "amount": amount}