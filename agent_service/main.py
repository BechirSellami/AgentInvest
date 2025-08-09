# agent_service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import datetime
#from langfuse.langchain import CallbackHandler

from agent_service.graph.state import InvestorState
from agent_service.graph.build_graph import build_engine

# Initialize FastAPI and Agents graph
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result