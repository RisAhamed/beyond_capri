import sqlite3
import json
from config import Config

class IdentityVault:
    def __init__(self, db_path=Config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with the identity_map table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS identity_map (
                uuid TEXT PRIMARY KEY,
                original_pii TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_identity(self, uuid: str, pii_data: dict):
        """
        Save the mapping between a UUID and the real PII data.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store PII as a JSON string
        pii_json = json.dumps(pii_data)
        
        try:
            cursor.execute('INSERT OR REPLACE INTO identity_map (uuid, original_pii) VALUES (?, ?)', 
                           (uuid, pii_json))
            conn.commit()
            print(f"[Vault] Securely stored identity for UUID: {uuid}")
        except Exception as e:
            print(f"[Vault] Error saving identity: {e}")
        finally:
            conn.close()

    def get_real_identity(self, uuid: str) -> dict:
        """
        Retrieve the real PII data for a given UUID.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT original_pii FROM identity_map WHERE uuid = ?', (uuid,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return json.loads(result[0])
        return None

# Simple test to run if file is executed directly
if __name__ == "__main__":
    vault = IdentityVault()
    vault.save_identity("test-uuid-123", {"name": "Alice", "condition": "Flu"})
    print(vault.get_real_identity("test-uuid-123"))