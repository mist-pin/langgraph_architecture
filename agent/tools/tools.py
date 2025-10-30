"""Streamlined tools for the AI Agent Starter Kit."""

import json
import re
import urllib.parse
from typing import Dict, Any
from langchain_core.tools import tool
import httpx # Need to import httpx for APIClient
from .utils import _create_error_response, APIClient, KNOWLEDGE_BASE_URL, _create_success_response, debug_print


# --- Tool: Document Knowledge (The only one kept) ---
@tool
async def document_knowledge(query: str, auth_token: str, company_id: int) -> Dict[str, Any]:
    """
    Performs a semantic search on the private knowledge base to answer user questions.
    Only use this tool when the answer is not available in the current state.
    
    Args:
        query: A concise, high-quality search query to retrieve relevant documents.
        auth_token: The user's authentication token.
        company_id: The user's company ID.
        
    Returns:
        JSON string with search results and state updates.
    """
    debug_print("document_knowledge input query:", query)
    
    if not KNOWLEDGE_BASE_URL:
        return _create_error_response("Knowledge base URL is not configured. Check environment variables.")
        
    # Format the query for URL
    encoded_query = urllib.parse.quote(query)
    
    result = await APIClient.make_request(
        f"{KNOWLEDGE_BASE_URL}/knowledge/search?companyId={company_id}&query={encoded_query}", 
        method="GET", 
        auth_token=auth_token
    )
    
    debug_print("document_knowledge api output:", result)
    
    if result.get("success"):
        # Process the result and format it into a cohesive answer string for the LLM
        documents = result.get("data", {}).get("data", [])
        
        # Concatenate snippets into a single context string
        context = "\n---\n".join([doc.get("content", "") for doc in documents if doc.get("content")])
        
        # Prepare the response with the context and state update
        state_updates = {"knowledge_base_search_performed": True}
        response_data = {"knowledge_context": context}
        
        return _create_success_response(response_data, state_updates, "Knowledge search complete.")

    # Return error on failure
    return result


# --- Tool Export ---
TOOLS = [
    document_knowledge,
]
# Removed all other tools (send_ui, profile_entry, banking_entry, marketplace_entry, inventory, workflow, etc.)