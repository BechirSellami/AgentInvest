from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graph.state import InvestorState
from graph.build_partial_graph import engine

app = FastAPI(title="Agent Service")

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def handle_query(req: QueryRequest):
    state = InvestorState(user_query=req.query)
    try:
        result = engine.invoke(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result.model_dump()