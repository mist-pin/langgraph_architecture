# OnboardKit AI Agent Starter Kit

A state-driven, intelligent AI agent starter kit for knowledge-base Q&A. Built with **LangGraph** and **FastAPI**.

---

## 🚀 Overview

The **OnboardKit** Agent is a minimal, stateful AI assistant template designed to answer user questions from a private knowledge base. It is an ideal starting point for a LangGraph-based RAG (Retrieval-Augmented Generation) application, demonstrating a clean implementation with:

1.  **Stateful Session Management** (using LangGraph's checkpointer).
2.  **Tool-Use Capabilities** (demonstrated with the **`document_knowledge`** tool).
3.  **FastAPI Streaming API** for real-time interaction.

This kit is ready to be extended with new tools and complex workflows.

---

## 🏗️ Architecture

### Backend (Python)
-   **LangGraph** - State management and workflow orchestration.
-   **FastAPI** - REST API with Server-Sent Events (SSE) streaming.
-   **LangChain** - LLM integration and single-tool management.
-   **MemorySaver** - In-memory session state persistence (for the starter kit).

### Frontend (Integration Notes)
The backend is designed to be consumed by a frontend application using **Server-Sent Events** for real-time AI response streaming.

---

## 🛠️ Setup

### Prerequisites
-   Python 3.9+
-   OpenAI API key

### Environment Configuration

The application uses environment variables for configuration. Create a **`.env`** file in the root directory with the following variables:

```bash
# Knowledge Base API for Q&A functionality (Replaced EZSCM_ with STARTERKIT_)
STARTERKIT_KNOWLEDGE_BASE_URL=http://localhost:7322/raas/chat

# Required: API Key
OPENAI_API_KEY="your-openai-api-key"

# Optional: Development Server Flag (for debug logs and hot reload)
DEVELOPMENT_SERVER=TRUE