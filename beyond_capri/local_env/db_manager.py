"""Local pseudonym mapping manager.

This module stays entirely on-prem and never leaves the secure boundary.
It manages context IDs and their associated PII using a local SQLite DB.
"""
import sqlite3
import uuid
import logging
from typing import Optional, Tuple
from config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalDBManager")

class PIIMappingDB:
    """
    Manages the bidirectional mapping between Real PII and Pseudonyms.
    CRITICAL: This database must NEVER act as a source for the Cloud Agent.
    It is only accessed by the Local Gatekeeper.
    """

    def __init__(self, db_path: str = str(Config.LOCAL_DB_PATH)):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the SQLite table for PII mapping."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        # original_value: The sensitive PII (e.g., "Alice Smith")
        # pseudonym_id: The safe ID sent to cloud (e.g., "User_x9")
        # entity_type: The category (e.g., "PERSON", "EMAIL", "DIAGNOSIS")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pii_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_value TEXT NOT NULL,
                pseudonym_id TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(original_value, entity_type)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Local PII Database initialized at {self.db_path}")

    def get_or_create_pseudonym(self, original_value: str, entity_type: str) -> str:
        """
        Retrieves an existing pseudonym for a PII value, or creates a new one if it doesn't exist.
        Ensures consistency: 'Alice' is always 'User_x9' within a session context.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 1. Check if mapping exists
            cursor.execute('''
                SELECT pseudonym_id FROM pii_mapping 
                WHERE original_value = ? AND entity_type = ?
            ''', (original_value, entity_type))
            
            result = cursor.fetchone()
            
            if result:
                logger.info(f"Existing mapping found for {entity_type}")
                return result[0]
            
            # 2. If not, create new mapping
            # Generate a consistent format based on type, e.g., "Patient_UUID"
            short_uuid = str(uuid.uuid4())[:8]
            new_pseudonym = f"{entity_type}_{short_uuid}"
            
            cursor.execute('''
                INSERT INTO pii_mapping (original_value, pseudonym_id, entity_type)
                VALUES (?, ?, ?)
            ''', (original_value, new_pseudonym, entity_type))
            
            conn.commit()
            logger.info(f"New mapping created: {new_pseudonym} for {entity_type}")
            return new_pseudonym

        except Exception as e:
            logger.error(f"Error in get_or_create_pseudonym: {e}")
            raise e
        finally:
            conn.close()

    def get_real_value(self, pseudonym_id: str) -> Optional[str]:
        """
        Reverses the pseudonymization. 
        CRITICAL: Only use this when the Cloud Agent returns the final answer to the Local Environment.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT original_value FROM pii_mapping WHERE pseudonym_id = ?', (pseudonym_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()

# Singleton instance for easy import
db_manager = PIIMappingDB()