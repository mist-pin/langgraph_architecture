"""Streamlined utility functions and helpers for the OnboardKit agent starter kit."""

import httpx
import json
import os
import uuid
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
import aiohttp
from .config import Configuration
from .state import State
from .tools import TOOLS


# ===============================================
# ====================debug======================
# ===============================================
def debug_print(*args, **kwargs):
    if os.getenv("DEVELOPMENT_SERVER", "FALSE") == "TRUE":
        print("===============================================")
        print(*args, **kwargs)
        print("===============================================")


# --- API Configuration ---
# Renamed to generic environment variables
API_BASE = os.getenv("STARTERKIT_API_BASE", "https://api.example.com/api/v1")
KNOWLEDGE_BASE_URL = os.getenv("STARTERKIT_KNOWLEDGE_BASE_URL", "https://knowledge.example.com/api/v1")


# --- API Client ---
class APIClient:
    """A minimal asynchronous client for making API requests."""

    @staticmethod
    async def make_request(
        url: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
        use_form_data: bool = False,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """Generic asynchronous API request."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                request_kwargs = {"headers": headers}
                if data:
                    if use_form_data:
                        request_kwargs["data"] = data
                    else:
                        request_kwargs["json"] = data
                
                response = await client.request(method, url, **request_kwargs)
                response.raise_for_status()

                try:
                    response_json = response.json()
                    return _create_success_response(response_json, {}, "API call successful")
                except json.JSONDecodeError:
                    return _create_error_response(f"API call successful but response is not valid JSON. Status: {response.status_code}", status_code=response.status_code)

            except httpx.HTTPStatusError as e:
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message") or error_json.get("error") or f"HTTP Error: {e.response.status_code}"
                except:
                    error_message = f"HTTP Error: {e.response.status_code} - {e.response.text[:100]}"
                return _create_error_response(error_message, status_code=e.response.status_code)
                
            except httpx.RequestError as e:
                return _create_error_response(f"Request Error: Could not connect to API or request timed out: {e.__class__.__name__}", status_code=0)
            except Exception as e:
                return _create_error_response(f"An unexpected error occurred during API request: {e.__class__.__name__}", status_code=0)


# --- Agent Core Helpers ---

async def generate_llm_response(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Generates a response from the LLM based on the current state.
    This function wraps the LLM call with tool binding.
    """
    # Create LLM and bind tools
    llm = Configuration.from_runnable_config(config).create_llm()
    llm_with_tools = llm.bind_tools(TOOLS)
    
    # Format current state for prompt injection
    current_state_vars = {
        k: v for k, v in state.items() if k in State.__annotations__ or k in ["last_error"]
    }
    
    from .prompts import SYSTEM_PROMPT
    # Fallback/placeholder values for missing keys in state for prompt formatting
    prompt_kwargs = {
        "auth_token": "", "user_id": 0, "company_id": 0, "email": "", "first_name": "", 
        "last_name": "", "full_name": "", "company_name": "", "init": False, 
        "welcome_message": False, "last_error": "", "personalized_name": state.get("full_name") or "valued user",
        "knowledge_base_search_performed": False,
        **current_state_vars
    }
    
    system_prompt = SYSTEM_PROMPT.format(**prompt_kwargs)
    
    # Prepare messages
    messages = [
        ("system", system_prompt),
        *state.get("messages", [])
    ]
    
    debug_print("LLM Input Messages (last 2 only):", messages[-2:])

    # Invoke LLM
    try:
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response], "last_error": ""}
    except Exception as e:
        error_msg = f"LLM generation failed: {e.__class__.__name__}: {str(e)}"
        debug_print(error_msg)
        return {"messages": [AIMessage(content=error_msg)], "last_error": error_msg}


def build_result(llm_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes the raw LLM output and tool results, aggregating state updates.
    """
    messages = llm_output.get("messages", [])
    if not messages:
        return {}
        
    last_msg = messages[-1]
    state_updates = {}
    
    # Logic to extract state updates from ToolMessage content
    if messages and isinstance(messages[-1], ToolMessage) and messages[-1].content:
        try:
            tool_output = json.loads(messages[-1].content)
            state_updates.update(tool_output.get("state_updates", {}))
        except json.JSONDecodeError:
            debug_print("Tool output was not valid JSON.")
            
    # If the LLM has just finished a thought/response, and the welcome message flag is off, set it.
    if isinstance(last_msg, AIMessage) and not last_msg.tool_calls and not llm_output.get("welcome_message", False):
        state_updates["welcome_message"] = True
    
    return {"messages": messages, **state_updates}


# --- Response Helpers ---

def _create_success_response(data: Dict[str, Any], state_updates: Dict[str, Any], message: str) -> Dict[str, Any]:
    """Helper to create a successful tool response."""
    response = {
        "success": True,
        "message": message,
        "data": data,
        "state_updates": state_updates
    }
    return response

def _create_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    """Helper to create a failed tool response."""
    return {
        "success": False,
        "message": f"Operation failed: {error_message}",
        "error": error_message,
        "status_code": status_code,
        "state_updates": {"last_error": error_message}
    }

# Removed all other utility functions (UI helpers, Data Fetchers, Form Handlers)