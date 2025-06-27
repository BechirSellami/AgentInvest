"""Construct a minimal LangGraph engine for query clarification."""

from langgraph.graph import StateGraph

from .state import InvestorState
from .nodes import clarifier, query_fix


def build_engine():
    """Compile and return the partial LangGraph engine."""
    graph = StateGraph(InvestorState)

    graph.add_node("clarifier", clarifier)
    graph.add_node("query_fix", query_fix)

    graph.set_entry_point("clarifier")
    graph.add_edge("clarifier", "query_fix",
                   condition=lambda s: not s.need_clarification)
    graph.add_edge(
        "clarifier",
        "END",
        condition=lambda s: s.need_clarification,
    )

    return graph.compile()


engine = build_engine()
