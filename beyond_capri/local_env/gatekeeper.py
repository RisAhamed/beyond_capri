import uuid
import json
import ollama
from beyond_capri.local_env.db_manager import IdentityVault
from beyond_capri.local_env.vector_store import AnchorStore

class Gatekeeper:
    def __init__(self):
        print("[Gatekeeper] Initializing Local Privacy Shield (Gemma 3 1B)...")
        self.vault = IdentityVault()
        self.anchor_store = AnchorStore()
        self.model = "gemma3:1b"

    def detect_and_sanitize(self, user_input: str):
        """
        Main function: Takes raw text, hides PII, stores secrets, returns safe text.
        """
        # 1. Ask Local LLM to find PII and Context
        print(f"[Gatekeeper] Scanning for PII in: '{user_input}'")
        analysis = self._extract_pii_metadata(user_input)
        
        if not analysis or "entities" not in analysis:
            print("[Gatekeeper] No PII detected or analysis failed.")
            return user_input

        # 2. Process each entity
        sanitized_text = user_input
        
        for entity in analysis["entities"]:
            original_text = entity.get("text")
            entity_type = entity.get("type")
            semantic_context = entity.get("context") # e.g. "Female patient with flu"

            if original_text and original_text in sanitized_text:
                # A. Generate a safe UUID
                safe_id = f"Entity_{str(uuid.uuid4())[:8]}" # e.g. Entity_a1b2c3d4
                
                # B. Vault the Real Identity (Local Only)
                self.vault.save_identity(safe_id, {
                    "original_text": original_text,
                    "type": entity_type,
                    "full_context": semantic_context
                })
                
                # C. Store Semantic Anchor (Cloud Pinecone)
                # We store the "Meaning" but NOT the "Name"
                # Logic: "Entity_x9 is a Female patient" (Safe to send to cloud)
                anchor_text = f"Entity Type: {entity_type}, Context: {semantic_context}"
                self.anchor_store.store_anchor(safe_id, anchor_text)
                
                # D. Replace in text
                sanitized_text = sanitized_text.replace(original_text, safe_id)
                print(f"   -> Masked '{original_text}' as '{safe_id}'")

        return sanitized_text

    def _extract_pii_metadata(self, text: str):
        """
        Uses Ollama (Gemma 3 1B) to extract structured PII data in JSON format.
        """
        system_prompt = """
        You are a Privacy Guard. Analyze the text and extract ALL Personally Identifiable Information (PII).
        PII includes: Names, Phone Numbers, Emails, Addresses, Usernames, IDs.
        
        For each PII found, determine its 'context' (e.g., gender, role, medical condition) based on the text.
        
        Return ONLY a JSON object with this format:
        {
            "entities": [
                {"text": "Amy", "type": "PERSON", "context": "Female, patient"},
                {"text": "@amy_v", "type": "HANDLE", "context": "Venmo username of Amy"}
            ]
        }
        """

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ], format='json') # Enforce JSON mode for reliability

            return json.loads(response['message']['content'])
        except Exception as e:
            print(f"[Gatekeeper] LLM Extraction Error: {e}")
            return None

# Simple test block
if __name__ == "__main__":
    gk = Gatekeeper()
    raw_text = "I need to send $50 to David Smith for the consultation."
    safe_text = gk.detect_and_sanitize(raw_text)
    print(f"\n[Result]\nOriginal: {raw_text}\nSafe:     {safe_text}")