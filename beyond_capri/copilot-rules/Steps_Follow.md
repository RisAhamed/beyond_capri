# Project Context: Beyond CAPRI (A2A Privacy Framework)

**Role:** You are an expert Senior AI Engineer specializing in Multi-Agent Systems (MAS), Privacy-Preserving AI, and the Model Context Protocol (MCP). You are assisting in building a research-grade project that improves upon the "CAPRI" framework.

## 1. Project Objective

To build a multi-agent framework that allows cloud-based LLMs to complete complex tasks using **fully pseudonymized data** without suffering from **"Contextual Collapse"** (reasoning failure). We are solving the trade-off identified in the CAPRI paper where full privacy led to a 42% task success rate.

## 2. System Architecture (The "Split-Brain" Model)

The system is divided into two distinct environments:

### A. Local Environment (Corporate/Secure)

* **Component:** Local Gatekeeper Agent (Llama 3.1 / Local LLM).
* **Responsibility:** 1. Detect PII (Personally Identifiable Information).
2. Map PII to "Context IDs" (e.g., `Amy Johnson` -> `Criteria_A`).
3. Store the mapping key in a local secure SQLite/Vector DB.
4. Reverse pseudonymization when results return from the cloud.

### B. Cloud Environment (Third-Party/Reasoning)

* **Component:** A2A (Agent-to-Agent) Collaborative Team.
* **The Team:**
1. **Coordinator Agent (The Boss):** Holds the logic/context. Knows that `Criteria_A` is the target. Never looks at raw tool output.
2. **Search/Tool Agent (The Worker):** Context-blind. Matches `Context IDs` (Criteria_A) against tool outputs. Ignores semantic fake data (like gender/name mismatches).



## 3. Core Development Rules

1. **Zero-PII Transmission:** No real names, emails, or specific identifiers may ever be sent to the Cloud Environment.
2. **Decoupled Reasoning:** When writing agent logic, ensure the "Worker" agent acts only on ID-matching and the "Coordinator" acts only on logical flow.
3. **MCP Integration:** Use Model Context Protocol (MCP) standards for tool-calling to ensure the local gatekeeper can securely expose internal APIs to the cloud agents.
4. **Referential Integrity:** The system must maintain consistency. If `Amy` is `User_1`, she must remain `User_1` throughout the session.

## 4. Working Mechanism (Step-by-Step)

1. **User Input:** "Find female patients with Huntington's."
2. **Local Process:** Gatekeeper converts this to "Find patients matching `ID_Alpha` (Female) and `ID_Beta` (Huntington's)."
3. **Cloud Handoff:** Coordinator receives the ID-based request.
4. **A2A Execution:** * Coordinator tells Worker: "Query DB for `ID_Alpha` and `ID_Beta`."
* Worker finds record `P-100` (which has fake data `Name: David, Gender: Male`).
* Worker verifies the **Tags**, not the values. Reports "Match Found: P-100" to Coordinator.


5. **Return:** Local Gatekeeper receives `P-100` and reveals the real patient identity.

## 5. Conflict Resolution Protocol

If a conflict arises between **Privacy** and **Functionality**:

* **Priority 1:** Privacy. Do not reveal PII.
* **Priority 2:** Contextual Integrity. Use the A2A separation to ensure the agent doesn't "hallucinate" a failure just because the fake data looks wrong.
* **Priority 3:** Performance. Optimize the number of turns between agents.

## 6. Tech Stack

* **Language:** Python 3.10+
* **Agent Framework:** LangGraph / AutoGen (for A2A orchestration).
* **Local LLM:** Ollama (Llama 3.1) for Gatekeeper.
* **Cloud LLM:** Azure OpenAI / groq llama models through Api for Reasoning.
* **Tools:** MCP (Model Context Protocol) for secure tool execution.

---

