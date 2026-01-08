from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    """
    The Global State shared between Coordinator and Worker.
    """
    # The conversation history
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # The Secret Knowledge (Semantic Anchors)
    # The Coordinator fills this. The Worker reads it but ignores conflicts.
    # Format: {'Entity_x9': 'Gender: Female, Condition: Flu'}
    semantic_anchors: Dict[str, str]
    
    # The current plan or instruction
    current_instruction: str
    
    # Final output to send back to local env
    final_response: str