from typing import Optional, Any
from pydantic import BaseModel


class InvestorState(BaseModel):
    user_query: str
    structured_query: dict | None = None   # {"sector":"HealthTech", ...}
    need_clarification: bool = False
    retrieved_docs: list[dict] = []
    scored_candidates: list[dict] = []     # +price +score
    budget: float | None = None
    portfolio: dict | None = None          # TODO: output of optimizer
    explanation_md: str | None = None      # TODO: output of optimizer
    where_filter: Optional[Any] = None
    near_vector: Optional[list] = None
    error: Optional[Any] = None
