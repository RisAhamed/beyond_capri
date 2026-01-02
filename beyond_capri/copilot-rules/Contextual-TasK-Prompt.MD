
### Phase 1: Foundation & Environment Setup

**Goal:** Initialize the project structure and establish the local/cloud separation.

> **Copilot Prompt:**
> "I am starting the 'Beyond CAPRI' project. Create a Python project structure with two main directories: `/local_env` (for the privacy gatekeeper) and `/cloud_env` (for the A2A reasoning team).
> **Tasks:**
> 1. Create a `requirements.txt` including: `langchain`, `langgraph`, `ollama`, `openai`, `pydantic`, and `mcp`.
> 2. Initialize a `config.yaml` to store model names (Ollama/Llama-3.1 for local, GPT-4o for cloud).
> 3. Create a `db_manager.py` in `/local_env` using SQLite to store pseudonym mapping tables with columns: `original_pii`, `pseudonym_id`, `category` (e.g., Name, Location), and `timestamp`.
> 4. Ensure all code follows the rule: No PII from `/local_env` should ever be hardcoded or logged in `/cloud_env`."
> 
> 

---

### Phase 2: Building the Local Gatekeeper (The Shield)

**Goal:** Implement the logic that detects PII and swaps it for "Context IDs."

> **Copilot Prompt:**
> "Help me build the `Gatekeeper` agent in `/local_env/gatekeeper.py`.
> **Mechanism:**
> 1. Use a local LLM (via Ollama) or a library like Microsoft Presidio to detect PII in a user string.
> 2. For every PII found, check `db_manager.py` for an existing pseudonym. If none exists, generate a new UUID-based ID (e.g., `Patient_Alpha_123`).
> 3. Implement a function `pseudonymize(user_input: str) -> str` that returns the string with PII replaced by IDs.
> 4. Implement a function `re_identify(cloud_output: str) -> str` that looks at the IDs in the cloud's response and swaps them back for real data from the local SQLite DB."
> 
> 

---

### Phase 3: Building the Cloud A2A Team (The Core)

**Goal:** Create the "Split-Brain" architecture to solve Contextual Collapse.

> **Copilot Prompt:**
> "In `/cloud_env/a2a_orchestrator.py`, use **LangGraph** to build a multi-agent team.
> **Agents to Define:**
> 1. **Coordinator Agent:** A high-level planner that receives the pseudonymized prompt. Its system prompt must instruct it to handle **logic only** and ignore the literal meaning of IDs.
> 2. **Worker Agent:** A 'context-blind' agent that interacts with tools. It should be prompted to match inputs against 'Context IDs' exactly, ignoring any semantic contradictions (e.g., if an ID represents a female but the data looks male, it must still treat it as a match).
> 
> 
> **Workflow:**
> Define a graph where the Coordinator analyzes the task, delegates a search to the Worker, and the Worker returns tool results based on ID-matching. Ensure the 'State' of the graph only contains pseudonymized data."

---

### Phase 4: MCP Tool Integration (The Bridge)

**Goal:** Securely connect the Cloud Worker to local data/tools without leaking PII.

> **Copilot Prompt:**
> "Implement the **Model Context Protocol (MCP)** in `/shared/mcp_server.py`.
> **Requirements:**
> 1. Build an MCP server that exposes a mock 'Patient Database' or 'Venmo API' as a tool.
> 2. The tool must accept 'Context IDs' as parameters.
> 3. Ensure the tool output is also pseudonymized. For example, if the Worker calls `get_patient_info(ID_Alpha)`, the tool should return a JSON where the name and sensitive fields are already swapped for pseudonyms.
> 4. Write an adapter in `/cloud_env/worker_agent.py` so the Worker can discover and call these MCP tools."
> 
> 

---

### Phase 5: Evaluation & Conflict Resolution

**Goal:** Replicate the CAPRI test cases to prove the 42% success rate is improved.

> **Copilot Prompt:**
> "Create an evaluation script `test_benchmark.py`.
> **Test Cases:**
> 1. **Referential Integrity Test:** Pass a prompt where a female patient is given a male pseudonym (the 'David' problem).
> 2. **Multi-Step Reasoning:** Test a financial transaction involving three different pseudonymized accounts.
> 
> 
> **Monitoring:**
> Implement a 'Conflict Detector' that logs when the Worker agent correctly follows an ID even when the semantic data looks 'wrong' (e.g., Gender mismatch). This will prove we have solved the Contextual Collapse identified in the base paper."

---

