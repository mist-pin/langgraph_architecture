#!/usr/bin/env python3
"""
FastAPI Server for the Stateful OnboardKit Onboarding Agent
"""

import uuid
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from fastapi import FastAPI, HTTPException, UploadFile, File
from .graph import graph
from .utils import debug_print


# ===============================================
# ====================setup======================
# ===============================================
app = FastAPI(title="OnboardKit Onboarding Agent API", version="4.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
session_auth_data = {}
sessions: Dict[str, Dict[str, Any]] = {}


# ===============================================
# ====================models=====================
# ===============================================
class SessionCreateRequest(BaseModel):
    """Defines the expected request body for creating a new session. Simplified for starter kit."""
    auth_token: str
    user_id: int
    email: str
    full_name: Optional[str] = ""
    company_id: Optional[int] = 0
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    company_name: Optional[str] = ""


class SessionCreateResponse(BaseModel):
    session_id: str


# ===============================================
# ====================api========================
# ===============================================
@app.post("/session", response_model=SessionCreateResponse)
async def create_session(auth_data: SessionCreateRequest):
    """
    Creates a new session and stores auth data for initialization.
    """
    session_id = str(uuid.uuid4())
    # Store auth data for this session
    session_auth_data[session_id] = auth_data
    return SessionCreateResponse(session_id=session_id)

@app.get("/chat/{session_id}", response_model=Dict[str, Any])
async def get_chat_history(session_id: str):
    """
    Retrieves the chat history for a given session.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Filter out ToolMessages from the history as they are not for the end user
    messages = [
        msg.model_dump() 
        for msg in sessions[session_id].get("messages", []) 
        if not isinstance(msg, AIMessage) or not getattr(msg, "tool_calls", None)
    ]

    return {"messages": messages, "state": sessions[session_id]}

@app.post("/chat/{session_id}")
async def stream_chat(session_id: str, user_input: str):
    """
    Handles a user message and streams the AI response.
    """
    if session_id not in session_auth_data:
        raise HTTPException(status_code=404, detail="Session not found. Please create a new session.")

    # Initialize session state if it doesn't exist
    if session_id not in sessions:
        auth_data = session_auth_data[session_id]
        # Initialize state from auth data
        initial_state = {
            "auth_token": auth_data.auth_token,
            "user_id": auth_data.user_id,
            "company_id": auth_data.company_id,
            "email": auth_data.email,
            "first_name": auth_data.first_name,
            "last_name": auth_data.last_name,
            "full_name": auth_data.full_name,
            "company_name": auth_data.company_name,
            "init": True,
            "welcome_message": False,
        }
        sessions[session_id] = graph.get_initial_state(initial_state)

    # Prepend HumanMessage
    sessions[session_id]["messages"].append(HumanMessage(content=user_input))
    
    # The actual execution happens here
    async def chat_stream_generator(session_state):
        try:
            # We use an aiosession for langgraph streaming
            async for s in graph.astream(session_state, config={"configurable": {"session_id": session_id}}):
                final_state = s.get("__end__", s)
                
                # Check for new LLM response message
                if "messages" in final_state and final_state["messages"]:
                    new_messages = [
                        msg for msg in final_state["messages"] 
                        if not isinstance(msg, HumanMessage)
                        and (msg not in session_state.get("messages", []))
                    ]
                    
                    if new_messages:
                        # Only stream the content of the new AI message (the last one)
                        last_ai_message = new_messages[-1]
                        if hasattr(last_ai_message, "content") and last_ai_message.content:
                            # Stream the message content
                            yield json.dumps({"type": "stream", "content": last_ai_message.content}) + "\n"
                            
                    # Update the session state with the latest state from the graph
                    sessions[session_id] = final_state
                
                # Update session state with the latest state
                sessions[session_id].update(final_state)

            # After the stream is complete, update the session and send a final status
            yield json.dumps({"type": "status", "status": "complete"}) + "\n"

        except Exception as e:
            debug_print(f"Graph execution error: {type(e).__name__}: {e}")
            error_message = f"An error occurred during processing: {str(e)}"
            yield json.dumps({"type": "error", "message": error_message}) + "\n"
            
            # Reset messages to the last user message and the error to allow retries
            sessions[session_id]["messages"] = sessions[session_id]["messages"][:-1] + [AIMessage(content=error_message)]
            sessions[session_id]["last_error"] = error_message

    return StreamingResponse(chat_stream_generator(sessions[session_id]), media_type="application/x-ndjson")


# Removed the /upload/{session_id} endpoint as all file processing tools are deleted.
@app.post("/upload/{session_id}")
async def upload_file(session_id: str, file: UploadFile):
    """File upload is not supported in this minimal starter kit."""
    raise HTTPException(status_code=400, detail="File upload is not supported in this starter kit.")