"""Streamlined, state-driven graph for the OnboardKit agent starter kit."""

from typing import Any, Dict, Literal
from langchain_core.messages import ToolMessage, BaseMessage, AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .state import State
from .tools import TOOLS # Only document_knowledge remains
from .utils import (
    generate_llm_response, build_result, debug_print
)


async def react_agent(state: State) -> Dict[str, Any]:
    """Simplified LLM call with state management."""
    debug_print("react_agent state: ", state)

    llm_output = await generate_llm_response(state)
    
    # Process the LLM's raw output (response message or tool call)
    return build_result(llm_output)


def route_tools(state: State) -> Literal["react_agent", "__end__"]:
    """Routes to tools if LLM requested them, otherwise to end."""
    last_msg = state.get("messages", [])[-1] if state.get("messages") else None
    
    # Check if the last message contains tool calls
    if last_msg and getattr(last_msg, "tool_calls", []):
        debug_print("Routing to TOOLS")
        return "tools"
    
    debug_print("Routing to END")
    return "__end__"


# The main graph definition
workflow = StateGraph(State)

# Nodes:
# 1. react_agent: LLM calls, decides on response or tool use
# 2. tools: Executes the document_knowledge tool call
workflow.add_node("react_agent", react_agent)
workflow.add_node("tools", ToolNode(TOOLS))

# Edges/Routing:
# 1. Entry point: Always start with the agent to get a response (including the welcome message)
workflow.set_entry_point("react_agent") 

# 2. From react_agent: Route to tools if tool calls are present, otherwise end
workflow.add_conditional_edges("react_agent", route_tools)

# 3. From tools: Always return to react_agent to process the tool results
workflow.add_edge("tools", "react_agent")


# Compile and persist
graph = workflow.compile(checkpointer=MemorySaver())