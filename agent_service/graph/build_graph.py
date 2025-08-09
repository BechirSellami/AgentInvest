"""Construct a minimal LangGraph engine for query clarification."""

from langgraph.graph import StateGraph, END
from langfuse.langchain import CallbackHandler

from .state import InvestorState
from .nodes.clarifier import clarifier
from .nodes.query_fix import query_fix
from .nodes.retriever import retriever

# Initialize Langfuse
from langfuse import get_client

langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler() 
 
# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")


def build_engine():
    """Compile and return the partial LangGraph engine."""
    graph = StateGraph(InvestorState)

    graph.add_node("Parser", clarifier)
    graph.add_node("Enricher", query_fix)
    graph.add_node("Retriever", retriever)
    
    graph.set_entry_point("Parser")
    graph.add_conditional_edges(
        "Parser",
        lambda s: "Enricher" if not s.need_clarification else END
    )
    graph.add_edge("Enricher", "Retriever")
    graph.add_edge("Retriever", END)

    return graph.compile().with_config({"callbacks": [langfuse_handler]})


engine = build_engine()
