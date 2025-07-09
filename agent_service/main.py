# agent_service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

from agent_service.graph.state import InvestorState
from agent_service.graph.build_graph import build_engine
from agent_service.langfuse_logger import start_trace, log_span

app = FastAPI(title="Agent Service")
engine = build_engine()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def handle_query(req: QueryRequest):
    """Execute the agent against the provided query."""
    state = InvestorState(user_query=req.query)

    trace_id = start_trace(name="Investor query", user_id="user-1")
    start_time = datetime.datetime.now(datetime.timezone.utc)

    try:
        result = engine.invoke(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    end_time = datetime.datetime.now(datetime.timezone.utc)
    log_span(trace_id=trace_id, name="LangGraph.invoke", start_time=start_time, end_time=end_time)

    return result