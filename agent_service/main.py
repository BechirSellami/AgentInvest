"""FastAPI entrypoint for the AgentInvest service."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent_service.graph.state import InvestorState
from agent_service.graph.build_partial_graph import build_engine

app = FastAPI(title="Agent Service")
engine = build_engine()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def handle_query(req: QueryRequest):
    """Execute the agent against the provided query."""
    state = InvestorState(user_query=req.query)
    try:
        result = engine.invoke(state)
        print(result)
    except Exception as exc:  # pragma: no cover - simple pass-through
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result