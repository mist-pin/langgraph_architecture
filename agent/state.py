"""The TypedDict state for the OnboardKit agent starter kit."""

from typing import Any, List, Sequence, TypedDict, Annotated, Union, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Removed ui_message_reducer as UI is no longer a core component

# --- State Definition ---

class State(TypedDict, total=False):
    """Streamlined state management for the OnboardKit agent starter kit."""
    
    # --- Core System ---
    messages: Annotated[Sequence[BaseMessage], add_messages]
    last_error: str
    # Removed UI state field
    
    # --- Session & Authentication ---
    auth_token: str
    user_id: int
    company_id: int
    
    # --- Agent Progress (Minimal) ---
    init: bool 
    welcome_message: bool
    
    # --- User Profile Data (Minimal) ---
    email: str
    first_name: str
    last_name: str
    full_name: str
    company_name: str
    
    # --- Tool State (Only knowledge base remains) ---
    knowledge_base_search_performed: bool

    # Removed all other onboarding/banking/file processing/template fields