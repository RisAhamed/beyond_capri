import json
import logging
from typing import Tuple, Dict
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from config import Config
from local_env.db_manager import db_manager
from local_env.vector_store import vector_store

logger = logging.getLogger("Gatekeeper")

class PrivacyGatekeeper:
    """
    The Local Shield.
    1. Analyzes input text for PII using local Ollama.
    2. Swaps PII for Pseudonyms via DB Manager.
    3. Extracts non-PII semantic traits and sends them to Pinecone.
    """

    def __init__(self):
        self.llm = Ollama(
            base_url=Config.LOCAL_MODEL_URL,
            model=Config.LOCAL_MODEL_NAME,
            temperature=0  # Deterministic for extraction
        )
        
        # Prompt to extract PII and Context separately
        self.extraction_prompt = PromptTemplate.from_template("""
            You are a Privacy Officer. Analyze the following text.
            
            Task 1: Identify all Personally Identifiable Information (PII) such as Names, Emails, Phone Numbers.
            Task 2: Identify the "Semantic Context" (medical conditions, intent, gender, age) that is NOT PII but is crucial for reasoning.
            
            Input Text: "{text}"
            
            Output strictly valid JSON with this format:
            {{
                "pii_detected": [
                    {{"value": "Alice Smith", "type": "PERSON"}},
                    {{"value": "alice@example.com", "type": "EMAIL"}}
                ],
                "semantic_context": "Female patient, mid-40s, asking about hypertension treatment options."
            }}
        """)

    def sanitize(self, raw_text: str) -> Tuple[str, Dict[str, str]]:
        """
        Main entry point. Takes raw text, returns safe text and a mapping report.
        """
        logger.info("Scanning text for PII...")
        
        # 1. Ask Ollama to identify PII vs Context
        chain = self.extraction_prompt | self.llm
        try:
            response_str = chain.invoke({"text": raw_text})
            # Clean up potential markdown formatting from LLM
            response_str = response_str.replace("```json", "").replace("```", "").strip()
            analysis = json.loads(response_str)
        except json.JSONDecodeError:
            logger.error("Ollama failed to return valid JSON. Fallback needed.")
            # In production, you would add retry logic here.
            return raw_text, {}

        # 2. Process PII
        safe_text = raw_text
        pseudonym_map = {}
        
        # We need a primary ID for the context anchor (usually the first PERSON found)
        primary_pseudonym_id = None
        
        if "pii_detected" in analysis:
            for item in analysis["pii_detected"]:
                real_val = item["value"]
                entity_type = item["type"]
                
                # Get or Create Pseudonym
                pseudonym = db_manager.get_or_create_pseudonym(real_val, entity_type)
                
                # Replace in text
                safe_text = safe_text.replace(real_val, pseudonym)
                pseudonym_map[pseudonym] = real_val
                
                if entity_type == "PERSON" and not primary_pseudonym_id:
                    primary_pseudonym_id = pseudonym

        # 3. Store Semantic Context in Pinecone
        # Only if we have a primary entity to attach the context to
        if primary_pseudonym_id and "semantic_context" in analysis:
            context_text = analysis["semantic_context"]
            vector_store.store_anchor(
                pseudonym_id=primary_pseudonym_id,
                context_text=context_text,
                metadata={"original_type": "PERSON"}
            )
            logger.info(f"Context anchor created for {primary_pseudonym_id}")

        logger.info(f"Sanitization Complete. Safe Text: {safe_text}")
        return safe_text, pseudonym_map

# Singleton
gatekeeper = PrivacyGatekeeper()