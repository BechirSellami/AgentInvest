from pydantic import BaseModel

class InvestorState(BaseModel):
    user_query: str
    structured_query: dict | None = None   # {"sector":"HealthTech", ...}
    need_clarification: bool = False
    retrieved_docs: list[dict] = []
    scored_candidates: list[dict] = []     # +price +score
    budget: float | None = None
    portfolio: dict | None = None          # output of optimizer
    explanation_md: str | None = None
