from langgraph.graph import StateGraph
from graph.state import InvestorState
from graph.nodes import (clarifier, query_fix)
# , retriever, enricher, screener, optimizer, explainer)

graph = StateGraph(InvestorState)

graph.add_node("clarifier", clarifier)
graph.add_node("query_fix", query_fix)

graph.set_entry_point("clarifier")
graph.add_edge("clarifier", "query_fix",
               condition=lambda s: not s.need_clarification)
graph.add_edge("clarifier", "END",
               condition=lambda s: s.need_clarification) # (If you want loop-backs for clarifications, connect END to a Streamlit form that re-feeds the state into clarifier.)

engine = graph.compile()
