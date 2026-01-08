import os
import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from pinecone import Pinecone
from config import Config
from beyond_capri.cloud_env.state import AgentState
from beyond_capri.shared.mcp_server import search_patient_database

class A2AOrchestrator:
    def __init__(self):
        # 1. Initialize Groq (High Intelligence)
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile",
            api_key=Config.GROQ_API_KEY
        )
        
        # 2. Initialize Pinecone (The Source of Truth)
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = pc.Index(Config.PINECONE_INDEX_NAME)
        
        self.graph = self._build_graph()

    def _fetch_cloud_anchor(self, text):
        """Helper: Asks Pinecone for the 'Real Meaning' of the UUIDs."""
        import re
        uuids = re.findall(r"(Entity_)?[a-f0-9]{8}", text)
        anchors = {}
        
        print(f"[Coordinator] Querying Pinecone for UUIDs: {uuids}")
        
        for uid in uuids:
            # Clean the UUID to ensure match
            clean_uid = uid if "Entity_" in uid else f"Entity_{uid}"
            
            try:
                response = self.index.fetch(ids=[clean_uid])
                if clean_uid in response.vectors:
                    context = response.vectors[clean_uid].metadata.get("semantic_context")
                    anchors[clean_uid] = context
                    print(f"   -> Pinecone Truth for {clean_uid}: '{context}'")
                else:
                    # Fallback if specific ID not found (for robustness)
                    anchors[clean_uid] = "Unknown Context"
            except Exception as e:
                print(f"[Coordinator] Pinecone Error: {e}")
                
        return anchors

    # --- NODE 1: COORDINATOR (The Brain) ---
    def coordinator_node(self, state: AgentState):
        user_msg = state['messages'][-1].content
        
        # 1. GET TRUTH FROM PINECONE
        anchors = self._fetch_cloud_anchor(user_msg)
        state['semantic_anchors'] = anchors
        
        anchor_text = json.dumps(anchors, indent=2)
        
        # 2. CREATE PLAN
        prompt = f"""
        You are the COORDINATOR.
        
        USER REQUEST: "{user_msg}"
        
        PINECONE TRUTH (REAL CONTEXT):
        {anchor_text}
        
        Task:
        Instruct the WORKER to search the database.
        
        CRITICAL INSTRUCTION:
        The database contains BROKEN DATA (e.g., Male names for Female patients).
        Tell the Worker explicitly: "Ignore Name/Gender mismatches. Trust the UUID match."
        """
        
        response = self.llm.invoke([SystemMessage(content=prompt)])
        state['current_instruction'] = response.content
        print(f"\n[Coordinator Plan] {response.content}")
        return state

    # --- NODE 2: WORKER (The Muscle) ---
    def worker_node(self, state: AgentState):
        instruction = state['current_instruction']
        
        # Bind the REAL MCP Tool
        tools = [search_patient_database]
        worker_llm = self.llm.bind_tools(tools)
        
        prompt = f"""
        You are the WORKER.
        INSTRUCTION: "{instruction}"
        
        Goal: Call the tool 'search_patient_database'.
        
        Rule: If the tool result has a weird name (like "David"), IGNORE IT. 
        If the UUID matches, report SUCCESS.
        """
        
        # 1. LLM decides to call tool
        response = worker_llm.invoke([HumanMessage(content=prompt)])
        
        # 2. Execute Tool (Manual binding for clear flow)
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            # EXECUTE THE MCP TOOL
            tool_result = search_patient_database.invoke(tool_call['args'])
            
            # 3. Analyze Result
            final_check = f"""
            Tool Result: {tool_result}
            
            Does the ID match? If yes, confirm the booking.
            Write a polite confirmation message to the user.
            """
            final_response = self.llm.invoke([HumanMessage(content=final_check)])
            state['final_response'] = final_response.content
        else:
            state['final_response'] = response.content
            
        return state

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("coordinator", self.coordinator_node)
        workflow.add_node("worker", self.worker_node)
        workflow.set_entry_point("coordinator")
        workflow.add_edge("coordinator", "worker")
        workflow.add_edge("worker", END)
        return workflow.compile()

    def run(self, safe_prompt: str):
        initial_state = {
            "messages": [HumanMessage(content=safe_prompt)],
            "semantic_anchors": {},
            "current_instruction": "",
            "final_response": ""
        }
        return self.graph.invoke(initial_state)