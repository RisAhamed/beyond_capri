import os
import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pinecone import Pinecone

from config import Config
from beyond_capri.cloud_env.state import AgentState

# IMPORT ALL TOOLS (SQL + RAG)
from beyond_capri.shared.mcp_server import get_account_balance, transfer_funds
from beyond_capri.cloud_env.tools import search_knowledge_base

class A2AOrchestrator:
    def __init__(self):
        # 1. Initialize Groq (High Intelligence)
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile",
            api_key=Config.GROQ_API_KEY
        )
        
        # 2. Initialize Pinecone
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = pc.Index(Config.PINECONE_INDEX_NAME)
        
        self.graph = self._build_graph()

    def _fetch_cloud_anchor(self, text):
        """Helper: Extracts Identity Anchors."""
        import re
        uuids = re.findall(r"(Entity_)?[a-f0-9]{8}", text)
        anchors = {}
        print(f"[Coordinator] Querying Pinecone for UUIDs: {uuids}")
        for uid in uuids:
            clean_uid = uid if "Entity_" in uid else f"Entity_{uid}"
            try:
                response = self.index.fetch(ids=[clean_uid])
                if clean_uid in response.vectors:
                    context = response.vectors[clean_uid].metadata.get("semantic_context")
                    anchors[clean_uid] = context
            except Exception as e:
                print(f"[Coordinator] Pinecone Error: {e}")
        return anchors

    # --- NODE 1: COORDINATOR ---
    def coordinator_node(self, state: AgentState):
        user_msg = state['messages'][-1].content
        anchors = self._fetch_cloud_anchor(user_msg)
        state['semantic_anchors'] = anchors
        
        anchor_text = json.dumps(anchors, indent=2)
        
        prompt = f"""
        You are the COORDINATOR of a Secure Banking AI.
        
        USER REQUEST: "{user_msg}"
        IDENTITY CONTEXT: {anchor_text}
        
        Your Capabilities:
        1. CHECK POLICIES: Use 'search_knowledge_base' if the request involves limits or rules.
        2. CHECK FUNDS: Use 'get_account_balance'.
        3. TRANSFER: Use 'transfer_funds'.
        
        Plan the steps for the Worker.
        
        PRIVACY RULE: The database uses generic names (John Doe). IGNORE name mismatches. TRUST THE UUIDs.
        """
        
        response = self.llm.invoke([SystemMessage(content=prompt)])
        state['current_instruction'] = response.content
        print(f"\n[Coordinator Plan] {response.content}")
        return state

    # --- NODE 2: WORKER ---
    def worker_node(self, state: AgentState):
        instruction = state['current_instruction']
        
        # Bind ALL tools
        tools = [get_account_balance, transfer_funds, search_knowledge_base]
        worker_llm = self.llm.bind_tools(tools)
        
        prompt = f"""
        You are the WORKER.
        INSTRUCTION: "{instruction}"
        
        Execute the necessary tools.
        If you see "John Doe" or "Jane Smith" in the tool output, IGNORE the name conflict.
        Trust the UUID match.
        """
        
        # 1. LLM decides tool call
        response = worker_llm.invoke([HumanMessage(content=prompt)])
        
        # 2. Execution Loop
        if response.tool_calls:
            # For demo, we handle the first tool call. 
            # In production, loop through all calls.
            tool_call = response.tool_calls[0]
            t_name = tool_call['name']
            t_args = tool_call['args']
            
            print(f"[Worker] Calling Tool: {t_name}")
            
            if t_name == "get_account_balance":
                res = get_account_balance.invoke(t_args)
            elif t_name == "transfer_funds":
                res = transfer_funds.invoke(t_args)
            elif t_name == "search_knowledge_base":
                res = search_knowledge_base.invoke(t_args)
            else:
                res = "Unknown Tool"
                
            # 3. Final Answer
            final_prompt = f"Tool Result: {res}. Write a confirmation message for the user."
            final_response = self.llm.invoke([HumanMessage(content=final_prompt)])
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