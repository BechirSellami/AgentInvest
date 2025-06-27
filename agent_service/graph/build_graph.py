"""Full LangGraph engine including retrieval and scoring stages."""

from langgraph.graph import StateGraph

from .state import InvestorState
from .nodes import (
    clarifier,
    query_fix,
    retriever,
    enricher,
    screener,
    optimizer,
    explainer,
)


def build_engine():
    """Compile and return the full LangGraph engine."""
    graph = StateGraph(InvestorState)

    graph.add_node("clarifier", clarifier)
    graph.add_node("query_fix", query_fix)
    graph.add_node("retriever", retriever)
    graph.add_node("enricher", enricher)
    graph.add_node("screener", screener)
    graph.add_node("optimizer", optimizer)
    graph.add_node("explainer", explainer)

    graph.set_entry_point("clarifier")
    graph.add_conditional_edges(
        "clarifier",
        {
            "query_fix": lambda s: not s.need_clarification,
            "END": lambda s: s.need_clarification,
        },
    )

    graph.add_edge("query_fix", "retriever")
    graph.add_edge("retriever", "enricher")
    graph.add_edge("enricher", "screener")
    graph.add_edge("screener", "optimizer")
    graph.add_edge("optimizer", "explainer")
    graph.add_edge("explainer", "END")

    return graph.compile()


engine = build_engine()
