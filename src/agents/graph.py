"""
LangGraph agent graphs.

Provides two compiled graphs:
- `rag_agent` — RAG chatbot for resident handbook Q&A (Groq/Qwen + ChromaDB)
- `agent`    — Original example agent (backward-compatible)
"""

from langgraph.graph import END, StateGraph

from src.agents.nodes.example_node import analyze_node, respond_node
from src.agents.nodes.rag_nodes import (
    fallback_node,
    format_node,
    generate_node,
    retrieve_node,
)
from src.agents.state import AgentState

# ---------------------------------------------------------------------------
# Original example graph (backward-compatible)
# ---------------------------------------------------------------------------

def should_continue(state: AgentState) -> str:
    """Route based on whether an error occurred during analysis."""
    if state.get("error"):
        return END
    return "respond"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("analyze", analyze_node)
    graph.add_node("respond", respond_node)

    # Add edges
    graph.set_entry_point("analyze")
    graph.add_conditional_edges("analyze", should_continue)
    graph.add_edge("respond", END)

    return graph.compile()


agent = build_graph()


# ---------------------------------------------------------------------------
# RAG Chatbot graph
# ---------------------------------------------------------------------------

def should_generate(state: AgentState) -> str:
    """Route based on whether retrieval found relevant chunks."""
    if state.get("error"):
        return "fallback"
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return "fallback"
    return "generate"


def build_rag_graph() -> StateGraph:
    """Build the RAG chatbot graph.

    Flow:
        START → retrieve → should_generate?
                          ├─ (has chunks) → generate → format → END
                          └─ (no chunks)  → fallback → END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("format", format_node)
    graph.add_node("fallback", fallback_node)

    # Add edges
    graph.set_entry_point("retrieve")
    graph.add_conditional_edges("retrieve", should_generate)
    graph.add_edge("generate", "format")
    graph.add_edge("format", END)
    graph.add_edge("fallback", END)

    return graph.compile()


rag_agent = build_rag_graph()
