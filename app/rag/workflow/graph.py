"""Langgraph Graph"""

from typing import Literal
from langgraph.graph import StateGraph, END
from app.rag.workflow.state import RAGState
from app.rag.workflow.nodes import (
    retrieval_node,
    reranking_node,
    tool_analysis_node,
    tool_execution_node,
    generation_node,
    error_node,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def should_use_tool(state: RAGState) -> Literal["tool_execution", "generation"]:
    """Conditional edge decides should use tool or not"""
    if state.get("tool_needed"):
        return "tool_execution"
    return "generation"


def check_error(state: RAGState) -> Literal["error", "reranking"]:
    """Conditional edge decides should rerank or not"""
    if state.get("error"):
        return "error"
    return "reranking"


def build_rag_graph() -> StateGraph:
    """Build RAG graph"""
    workflow = StateGraph(RAGState)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("reranking", reranking_node)
    workflow.add_node("tool_analysis", tool_analysis_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("generation", generation_node)
    workflow.add_node("error", error_node)

    # set entry point
    workflow.set_entry_point("retrieval")

    # add edges
    workflow.add_conditional_edges(
        "retrieval", check_error, {"error": "error", "reranking": "reranking"}
    )
    workflow.add_edge("reranking", "tool_analysis")

    workflow.add_conditional_edges(
        "tool_analysis",
        should_use_tool,
        {"tool_execution": "tool_execution", "generation": "generation"},
    )

    workflow.add_edge("tool_execution", "generation")
    workflow.add_edge("generation", END)
    workflow.add_edge("error", END)

    return workflow


rag_graph = build_rag_graph().compile()
