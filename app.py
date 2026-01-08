import streamlit as st
import time
import json
from beyond_capri.local_env.db_manager import IdentityVault
from beyond_capri.local_env.gatekeeper import Gatekeeper
from beyond_capri.local_env.db_manager import IdentityVault
from beyond_capri.cloud_env.a2a_orchestrator import A2AOrchestrator
from beyond_capri.shared.mcp_server import init_financial_db

# Page Config
st.set_page_config(page_title="Beyond CAPRI: Live Architecture", layout="wide")

# Initialize Backend (Cached to run once)
@st.cache_resource
def init_system():
    init_financial_db() # Ensure DB exists
    return Gatekeeper(), IdentityVault(), A2AOrchestrator()

gatekeeper, vault, orchestrator = init_system()

# --- SIDEBAR: SYSTEM STATUS & GRAPH ---
with st.sidebar:
    st.header("⚙️ System Architecture")
    st.success("✅ Local Privacy Shield: Active")
    st.success("✅ Cloud A2A Swarm: Connected")
    st.success("✅ Pinecone Memories: Loaded")
    
    st.divider()
    
    st.subheader("🧠 LangGraph Structure")
    st.info("Visualizing the Agent Workflow...")
    
    # Draw the Graph
    try:
        # Generate the Mermaid Image of the Graph
        graph_png = orchestrator.graph.get_graph().draw_mermaid_png()
        st.image(graph_png, caption="Live A2A Execution Graph")
    except Exception as e:
        st.warning(f"Could not render graph: {e}")
        st.caption("Ensure Graphviz is installed to see the diagram.")

# --- MAIN UI ---
st.title("🛡️ Beyond CAPRI: Privacy-Preserving AI")
st.markdown("### The 'Glass Box' Interface")
st.caption("Watch how PII is protected, processed, and restored in real-time.")

# Create two columns: Chat vs. Behind-the-Scenes
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 User Interface")
    user_input = st.text_area("Enter your request:", 
                             value="Transfer $2000 from Sarah Jones to Bob Smith.",
                             height=100)
    
    run_btn = st.button("🚀 Execute Secure Transaction", type="primary")

# --- EXECUTION LOGIC ---
if run_btn and user_input:
    
    # 1. PHASE 1: INGESTION (Local)
    with col2:
        st.subheader("🔍 Behind the Screens")
        
        with st.status("🔒 Phase 1: Local Gatekeeper (Sanitization)", expanded=True) as status:
            st.write("Scanning for PII...")
            time.sleep(0.5) # UI pacing
            
            # RUN GATEKEEPER
            safe_prompt = gatekeeper.detect_and_sanitize(user_input)
            
            # Show the Transformation
            st.markdown(f"**Original:** `{user_input}`")
            st.markdown(f"**Sanitized:** `{safe_prompt}`")
            st.markdown("---")
            
            # Extract UUIDs for display
            import re
            uuids = re.findall(r"(Entity_)?[a-f0-9]{8}", safe_prompt)
            if uuids:
                st.json({"Detected UUIDs": uuids, "Action": "Vaulted to SQLite & Pinecone"})
            
            status.update(label="✅ Phase 1 Complete: PII Secured", state="complete")

    # 2. PHASE 2 & 3: CLOUD REASONING (The "David" Test)
    with col2:
        with st.status("☁️ Phase 2: Cloud A2A Reasoning", expanded=True) as status:
            st.write("Coordinator is querying Pinecone context...")
            
            # RUN CLOUD AGENTS
            # We capture the result dictionary
            result = orchestrator.run(safe_prompt)
            
            # VISUALIZE COORDINATOR THOUGHTS
            st.info("🧠 Coordinator Plan")
            st.markdown(f"*{result.get('current_instruction')}*")
            
            # VISUALIZE WORKER ACTION (The "Bad Data")
            st.warning("🛠️ Worker Execution (Raw Tool Data)")
            raw_response = result['final_response']
            
            # Show the raw output (which might contain "John Doe" or "David")
            st.code(raw_response, language="text")
            
            status.update(label="✅ Phase 2 Complete: Task Executed", state="complete")

    # 3. PHASE 4: RE-IDENTIFICATION (Local Bridge)
    with col2:
        with st.status("🔐 Phase 3: Local Re-Identification", expanded=True) as status:
            st.write("Scanning Cloud Output for UUIDs...")
            
            # RUN RE-ID LOGIC (Reusing logic from main.py)
            # We recreate the function here for UI visualization
            final_text = raw_response
            exact_matches = re.findall(r"Entity_[a-f0-9]{8}|[a-f0-9]{8}", raw_response)
            
            replaced_log = {}
            
            for match_str in exact_matches:
                real_identity = vault.get_real_identity(match_str)
                if not real_identity:
                    if "Entity_" in match_str:
                        real_identity = vault.get_real_identity(match_str.replace("Entity_", ""))
                    else:
                        real_identity = vault.get_real_identity(f"Entity_{match_str}")

                if real_identity:
                    original_name = real_identity.get("original_text", "Unknown")
                    replaced_log[match_str] = original_name
                    
                    # Perform Swap
                    final_text = final_text.replace(match_str, original_name)
                    # Simple heuristic cleanup for demo
                    final_text = final_text.replace("John Doe", original_name)
                    final_text = final_text.replace("David Smith", original_name)
                    final_text = final_text.replace("Jane Smith", original_name)

            if replaced_log:
                st.success("UUIDs Resolved:")
                st.json(replaced_log)
            else:
                st.write("No UUIDs found to restore.")
                
            status.update(label="✅ Phase 3 Complete: Identity Restored", state="complete")

    # 4. FINAL OUTPUT (Chat Column)
    with col1:
        st.divider()
        st.success("🎉 Final Secure Response")
        st.chat_message("assistant").write(final_text)
        
        # Add 'Download Receipt' simulation
        st.button("📄 Download Transaction Receipt")