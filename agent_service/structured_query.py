from pydantic import BaseModel, Field
from typing import List, Optional

class StructuredQuery(BaseModel):
    sector: Optional[str]        = Field(None, description="Primary industry sector")
    keywords: Optional[List[str]]= Field(None, description="Salient free-text phrases")
    ebitda_min: Optional[float]  = Field(None, description="Minimum EBITDA in USD millions")
    revenue_min: Optional[float] = Field(None, description="Minimum revenue in USD millions")
    arr_growth_min: Optional[float] = Field(None, description="Minimum ARR growth (%)")
    risk_profile: Optional[str]  = Field(None, description="'low' | 'medium' | 'high'")
    budget: Optional[float]      = Field(None, description="Investor budget in USD millions")
    theme: Optional[str]         = Field(None, description="High-level theme such as 'net-zero'")
