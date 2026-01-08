import os
import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pinecone import Pinecone

from config import Config
from cloud_env.state import AgentState
# IMPORT THE NEW FINANCIAL MCP TOOLS
from shared.mcp_server import get_account_balance, transfer_funds

class A2AOrchestrator:
    def __init__(self):
        # 1. Initialize Groq (High Intelligence - Llama 3.3 70B)
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile",
            api_key=Config.GROQ_API_KEY
        )
        
        # 2. Initialize Pinecone (The Source of Truth for Logic/Context)
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = pc.Index(Config.PINECONE_INDEX_NAME)
        
        # 3. Build the Agent Graph
        self.graph = self._build_graph()

    def _fetch_cloud_anchor(self, text):
        """
        Helper: Extracts UUIDs from text and asks Pinecone for their 'Meaning'.
        This allows the Coordinator to know 'User_x9 is a High Net Worth Client'
        without knowing their real name.
        """
        import re
        # Find UUIDs (matches both 'Entity_...' and raw 8-char hex)
        uuids = re.findall(r"(Entity_)?[a-f0-9]{8}", text)
        anchors = {}
        
        print(f"[Coordinator] Querying Pinecone for UUIDs: {uuids}")
        
        for uid in uuids:
            # Clean the UUID to ensure consistent format for lookup
            clean_uid = uid if "Entity_" in uid else f"Entity_{uid}"
            
            try:
                response = self.index.fetch(ids=[clean_uid])
                if clean_uid in response.vectors:
                    context = response.vectors[clean_uid].metadata.get("semantic_context")
                    anchors[clean_uid] = context
                    print(f"   -> Pinecone Truth for {clean_uid}: '{context}'")
                else:
                    # Robustness: Handle cases where ID might be new or missing
                    anchors[clean_uid] = "Unknown Context"
            except Exception as e:
                print(f"[Coordinator] Pinecone Error: {e}")
                
        return anchors

    # --- NODE 1: THE COORDINATOR AGENT (The Brain) ---
    def coordinator_node(self, state: AgentState):
        """
        Analyzes the user request and the Hidden Truth (Pinecone) to create a plan.
        """
        user_msg = state['messages'][-1].content
        
        # 1. Retrieve the "Truth" from Pinecone
        anchors = self._fetch_cloud_anchor(user_msg)
        state['semantic_anchors'] = anchors
        
        anchor_text = json.dumps(anchors, indent=2)
        
        # 2. Formulate the Logic Plan
        prompt = f"""
        You are the COORDINATOR of a Secure Banking AI.
        
        USER REQUEST: "{user_msg}"
        
        PINECONE TRUTH (REAL CONTEXT):
        {anchor_text}
        
        Your Task:
        1. Identify the Sender and Receiver UUIDs.
        2. Plan the financial action (e.g., Check Balance -> Transfer Funds).
        
        CRITICAL PRIVACY & LOGIC RULE:
        The banking ledger uses pseudonymized/fake names (e.g., "John Doe", "Jane Smith").
        Explicitly instruct the WORKER to IGNORE name mismatches.
        TRUST the UUID match as the absolute truth.
        """
        
        response = self.llm.invoke([SystemMessage(content=prompt)])
        state['current_instruction'] = response.content
        print(f"\n[Coordinator Plan] {response.content}")
        
        return state

    # --- NODE 2: THE WORKER AGENT (The Muscle) ---
    def worker_node(self, state: AgentState):
        """
        Receives instructions and blindly executes the financial tools.
        """
        instruction = state['current_instruction']
        
        # Bind the FINANCIAL tools
        tools = [get_account_balance, transfer_funds]
        worker_llm = self.llm.bind_tools(tools)
        
        prompt = f"""
        You are the WORKER. You execute banking tools blindly.
        
        INSTRUCTION FROM COORDINATOR:
        "{instruction}"
        
        Your Goal: Perform the requested financial transaction.
        
        CRITICAL OVERRIDE:
        If the tool returns a generic name like "John Doe" or "Jane Smith", IGNORE IT.
        Do not fail the task because the name looks wrong.
        If the UUID matches, proceed with the transaction.
        """
        
        # 1. LLM decides which tool to call
        response = worker_llm.invoke([HumanMessage(content=prompt)])
        
        # 2. Execute Tool (Manual execution loop for clarity)
        if response.tool_calls:
            # We handle the first tool call for this demo cycle
            tool_call = response.tool_calls[0]
            selected_tool = tool_call['name']
            tool_args = tool_call['args']
            
            print(f"[Worker] Executing Tool: {selected_tool} with args: {tool_args}")
            
            # Route to the correct function
            if selected_tool == "get_account_balance":
                tool_result = get_account_balance.invoke(tool_args)
            elif selected_tool == "transfer_funds":
                tool_result = transfer_funds.invoke(tool_args)
            else:
                tool_result = "Error: Unknown tool."
            
            # 3. Worker Analyzes Result & Generates Confirmation
            final_check_prompt = f"""
            Tool Result: {tool_result}
            
            Based on the UUID match, confirm the transaction status.
            Draft a polite confirmation message to the user.
            (Remember: The user knows the real names, so just confirm the IDs and amounts clearly).
            """
            final_response = self.llm.invoke([HumanMessage(content=final_check_prompt)])
            state['final_response'] = final_response.content
        else:
            # If no tool was called (e.g., just a question), return the text
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
        """Entry point to run the cloud team"""
        initial_state = {
            "messages": [HumanMessage(content=safe_prompt)],
            "semantic_anchors": {},
            "current_instruction": "",
            "final_response": ""
        }
        return self.graph.invoke(initial_state)