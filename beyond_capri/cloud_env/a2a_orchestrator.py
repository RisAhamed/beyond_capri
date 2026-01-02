"""A2A orchestration for Coordinator/Worker split-brain.

Coordinator holds logical goals and context IDs only.
Worker is context-blind and operates on tags/IDs, never raw PII.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CoordinatorState:
    goal: str
    context_ids: Dict[str, str]  # logical tags -> context IDs


class Coordinator:
    def __init__(self):
        self.state: CoordinatorState | None = None

    def plan(self, goal: str, context_ids: Dict[str, str]) -> Dict[str, Any]:
        self.state = CoordinatorState(goal=goal, context_ids=context_ids)
        # In a real graph, emit a plan/message to Worker.
        return {"action": "query", "targets": list(context_ids.values())}

    def integrate(self, worker_result: Dict[str, Any]) -> Dict[str, Any]:
        # Combine worker output with coordinator context; avoid any raw PII.
        return {"result": worker_result, "context_ids": self.state.context_ids if self.state else {}}


class Worker:
    def execute(self, action: str, targets: list[str]) -> Dict[str, Any]:
        # Worker only matches IDs/tags; no semantic inspection of PII.
        if action != "query":
            return {"status": "noop"}
        # TODO: plug tool calls here (e.g., DB search) using MCP client.
        return {"status": "ok", "matches": ["P-100"], "checked_ids": targets}


def run_a2a(goal: str, context_ids: Dict[str, str]) -> Dict[str, Any]:
    coordinator = Coordinator()
    worker = Worker()

    plan = coordinator.plan(goal, context_ids)
    worker_output = worker.execute(plan.get("action", ""), plan.get("targets", []))
    return coordinator.integrate(worker_output)
