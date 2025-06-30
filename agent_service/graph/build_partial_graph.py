"""Construct a minimal LangGraph engine for query clarification."""

from langgraph.graph import StateGraph, END

from .state import InvestorState
from .nodes.clarifier import clarifier
from .nodes.query_fix import query_fix
from .nodes.retriever import retriever


def build_engine():
    """Compile and return the partial LangGraph engine."""
    graph = StateGraph(InvestorState)

    graph.add_node("clarifier", clarifier)
    graph.add_node("query_fix", query_fix)
    graph.add_node("retriever", retriever)
    
    graph.set_entry_point("clarifier")
    graph.add_conditional_edges(
    "clarifier",
    {
        "query_fix": lambda s: not s.need_clarification,
        END: lambda s: s.need_clarification,
    },
    )
    graph.add_edge("query_fix", "retriever")
    graph.add_edge("retriever", END)

    return graph.compile()


engine = build_engine()
