import os
import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from pinecone import Pinecone

from config import Config
from beyond_capri.cloud_env.state import AgentState
from beyond_capri.cloud_env.tools import search_patient_database

class A2AOrchestrator:
    def __init__(self):
        # 1. Initialize Cloud LLM (Groq - Llama 3.3 70B for high intelligence)
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile",
            api_key=Config.GROQ_API_KEY
        )
        
        # 2. Initialize Cloud-Side Pinecone Connection
        # Note: In a real system, this is a separate instance from the local one.
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = pc.Index(Config.PINECONE_INDEX_NAME)
        
        # 3. Setup the Graph
        self.graph = self._build_graph()

    def _fetch_cloud_anchor(self, text):
        """
        Helper: Extracts UUIDs from text and asks Pinecone for their 'Meaning'.
        """
        import re
        # Find all strings like "Entity_..."
        uuids = re.findall(r"Entity_[a-f0-9]{8}", text)
        anchors = {}
        
        print(f"[Coordinator] Detected UUIDs: {uuids}")
        
        for uid in uuids:
            try:
                # Direct Cloud Query to Pinecone
                response = self.index.fetch(ids=[uid])
                if uid in response.vectors:
                    context = response.vectors[uid].metadata.get("semantic_context")
                    anchors[uid] = context
                    print(f"[Coordinator] Retrieved Anchor for {uid}: '{context}'")
            except Exception as e:
                print(f"[Coordinator] Pinecone Error: {e}")
                
        return anchors

    # --- NODE 1: THE COORDINATOR AGENT ---
    def coordinator_node(self, state: AgentState):
        """
        Analyzes the request, fetches Hidden Context, and creates a plan.
        """
        user_msg = state['messages'][-1].content
        
        # 1. Retrieve the "Truth" from Pinecone
        anchors = self._fetch_cloud_anchor(user_msg)
        state['semantic_anchors'] = anchors
        
        # 2. Formulate the Logic Plan
        anchor_text = json.dumps(anchors, indent=2)
        
        prompt = f"""
        You are the COORDINATOR of a Privacy-Preserving AI Team.
        
        USER REQUEST: "{user_msg}"
        
        HIDDEN TRUTH (SEMANTIC ANCHORS):
        {anchor_text}
        
        Your Job:
        1. Analyze the User Request.
        2. Compare it with the Hidden Truth.
        3. Instruct the WORKER to execute the task.
        
        CRITICAL RULE:
        The Worker is "Blind". It might see fake names (like "David") for these IDs.
        WARN the Worker to ignore name/gender mismatches and trust the UUID matches ONLY.
        
        Output ONLY the instruction for the Worker.
        """
        
        response = self.llm.invoke([SystemMessage(content=prompt)])
        state['current_instruction'] = response.content
        print(f"\n[Coordinator Plan] {response.content}")
        
        return state

    # --- NODE 2: THE WORKER AGENT ---
    def worker_node(self, state: AgentState):
        """
        Receives instruction, calls tools, and reports success based on UUIDs.
        """
        instruction = state['current_instruction']
        
        # Bind the tool to the worker
        tools = [search_patient_database]
        worker_llm = self.llm.bind_tools(tools)
        
        prompt = f"""
        You are the WORKER. You execute tools blindly.
        
        INSTRUCTION FROM COORDINATOR:
        "{instruction}"
        
        Your Goal: Find the patient record.
        
        CRITICAL OVERRIDE:
        If the tool returns a name or gender that conflicts with your logic, IGNORE THE CONFLICT.
        If the UUID matches, it is a success.
        
        Return a final summary starting with "SUCCESS:" if found.
        """
        
        # 1. Worker Decides to Call Tool
        response = worker_llm.invoke([HumanMessage(content=prompt)])
        
        # 2. If tool call is requested, execute it manually (simulation)
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_result = search_patient_database.invoke(tool_call['args'])
            
            # 3. Worker Analyzes Result
            final_check_prompt = f"""
            Tool Result: {tool_result}
            
            Based on the UUID match, is this the correct record? 
            (Ignore name/gender mismatches if UUID is correct).
            
            Write a final response for the user confirming the booking.
            """
            final_response = self.llm.invoke([HumanMessage(content=final_check_prompt)])
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
        """Entry point to run the cloud team"""
        initial_state = {
            "messages": [HumanMessage(content=safe_prompt)],
            "semantic_anchors": {},
            "current_instruction": "",
            "final_response": ""
        }
        return self.graph.invoke(initial_state)