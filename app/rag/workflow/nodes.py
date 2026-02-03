"""
LangGraph Nodes
Individual processing nodes for RAG workflow
"""

from typing import Dict, Any
import time
import re
from app.rag.retrieval.hybrid_retriever import HybridRetriever
from app.rag.retrieval.reranker import Reranker
from app.rag.llm.ollama_client import OllamaClient
from app.rag.llm.tool_executor import ToolExecutor
from app.rag.workflow.state import RAGState
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize components
hybrid_retriever = HybridRetriever()
reranker = Reranker()
ollama_client = OllamaClient()
tool_executor = ToolExecutor()


def retrieval_node(state: RAGState) -> Dict[str, Any]:
    """
    Retrieval node
    """
    logger.info("[Retrieval Node] Processing query: %s...", state["query"][:50])

    start_time = time.time()

    try:
        # Perform hybrid search (BM25 + Vector)
        results = hybrid_retriever.search(
            query=state["query"], user_id=state["user_id"], top_k=10
        )

        retrieval_time = (time.time() - start_time) * 1000

        logger.info(
            "[Retrieval Node] Retrieved %d documents in %.2fms",
            len(results),
            retrieval_time,
        )

        # Update state
        state["hybrid_results"] = results
        state["metadata"]["steps"].append("retrieval")
        state["metadata"]["retrieval_time_ms"] = retrieval_time
        state["metadata"]["documents_retrieved"] = len(results)

        return state

    except (ValueError, RuntimeError) as e:
        logger.error("[Retrieval Node] Retrieval Error: %s", e)
        state["error"] = f"Retrieval error: {str(e)}"
        return state
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("[Retrieval Node] Unexpected Error: %s", e)
        state["error"] = f"Unexpected retrieval error: {str(e)}"
        return state


def reranking_node(state: RAGState) -> Dict[str, Any]:
    """
    Reranking node - rerank retrieved documents for better relevance
    """
    logger.info("[Reranking Node] Reranking documents...")

    try:
        hybrid_results = state.get("hybrid_results", [])

        if not hybrid_results:
            logger.warning("[Reranking Node] No documents to rerank")
            state["reranked_results"] = []
            state["context_documents"] = []
            return state

        # Rerank documents
        reranked = reranker.rerank(
            query=state["query"], documents=hybrid_results, top_k=5
        )

        logger.info("[Reranking Node] Reranked to top %d documents", len(reranked))

        # Update state
        state["reranked_results"] = reranked
        state["context_documents"] = reranked
        state["metadata"]["steps"].append("reranking")
        state["metadata"]["documents_reranked"] = len(reranked)

        return state

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("[Reranking Node] Error: %s", e)
        # Fallback to hybrid results without reranking
        state["reranked_results"] = state.get("hybrid_results", [])[:5]
        state["context_documents"] = state["reranked_results"]
        return state


def tool_analysis_node(state: RAGState) -> Dict[str, Any]:
    """
    Tool analysis node - determine if tools are needed
    """
    logger.info("[Tool Analysis Node] Analyzing if tools needed...")

    query = state["query"].lower()

    # Simple heuristics for tool detection
    tool_keywords = {
        "date": ["today", "current date", "what date", "what day"],
        "calculate": ["calculate", "compute", "math", "sum", "multiply", "divide"],
    }

    tool_needed = False
    for tool_type, keywords in tool_keywords.items():
        if any(keyword in query for keyword in keywords):
            tool_needed = True
            logger.info("[Tool Analysis Node] Tool needed: %s", tool_type)
            break

    state["tool_needed"] = tool_needed
    state["metadata"]["steps"].append("tool_analysis")

    return state


def tool_execution_node(state: RAGState) -> Dict[str, Any]:
    """
    Tool execution node - execute tools if needed
    """
    logger.info("[Tool Execution Node] Executing tools...")

    try:
        query = state["query"].lower()

        # Determine which tool to execute
        if "date" in query or "today" in query:
            result = tool_executor.execute_tool("get_current_date")
            state["tool_result"] = f"Current date: {result}"

        elif "calculate" in query or "compute" in query:

            numbers = re.findall(r"\d+", query)
            if len(numbers) >= 2:
                expression = f"{numbers[0]}+{numbers[1]}"
                result = tool_executor.execute_tool(
                    "calculate", {"expression": expression}
                )
                state["tool_result"] = f"Calculation result: {result}"

        state["metadata"]["steps"].append("tool_execution")
        logger.info("[Tool Execution Node] Tool result: %s", state.get("tool_result"))

        return state

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("[Tool Execution Node] Error: %s", e)
        state["tool_result"] = f"Tool execution error: {str(e)}"
        return state


def generation_node(state: RAGState) -> Dict[str, Any]:
    """
    Generation node - generate final answer using LLM
    """
    logger.info("[Generation Node] Generating answer...")

    start_time = time.time()

    try:
        context_documents = state.get("context_documents", [])

        if not context_documents and not state.get("tool_result"):
            logger.warning("[Generation Node] No context available")
            state["answer"] = (
                "I couldn't find any relevant information in your documents to answer this question. Please upload relevant documents first."
            )
            return state

        # Generate answer with context
        result = ollama_client.generate_with_context(
            query=state["query"],
            context_documents=context_documents,
            conversation_history=None,
        )

        answer = result["answer"]

        # If tool was used, prepend tool result
        if state.get("tool_result"):
            answer = f"{state['tool_result']}\n\n{answer}"

        generation_time = (time.time() - start_time) * 1000

        logger.info("[Generation Node] Generated answer in %.2fms", generation_time)

        # Update state
        state["answer"] = answer
        state["metadata"]["steps"].append("generation")
        state["metadata"]["generation_time_ms"] = generation_time
        state["metadata"]["context_documents_used"] = len(context_documents)

        return state

    except (ValueError, RuntimeError) as e:
        logger.error("[Generation Node] Generation Error: %s", e)
        state["error"] = f"Generation error: {str(e)}"
        state["answer"] = (
            "I encountered a specific error while generating the answer. Please try again."
        )
        return state
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("[Generation Node] Unexpected Error: %s", e)
        state["error"] = f"Unexpected generation error: {str(e)}"
        state["answer"] = (
            "I encountered an unexpected error while generating the answer. Please try again."
        )
        return state


def error_node(state: RAGState) -> Dict[str, Any]:
    """
    Error node - handle errors
    """
    logger.error("[Error Node] Error occurred: %s", state.get("error"))

    state["answer"] = f"An error occurred: {state.get('error', 'Unknown error')}"
    state["metadata"]["steps"].append("error")

    return state
