# from typing import Optional, Literal, List
# from pydantic import BaseModel, Field
# from agent_service.theme_taxonomy import THEMES
# from agent_service.sector_taxonomy import SECTOR_SUBSECTOR_MAP

# ThemeLiteral = Literal[*THEMES]  # Python 3.11 “PEP 675” style
# SectorLiteral = Literal[*SECTOR_SUBSECTOR_MAP.keys()]

# class StructuredQuery(BaseModel):
#     #sector: Optional[str]               = Field(None, description="Primary industry sector")
#     sector: Optional[SectorLiteral] = Field( # type: ignore
#         None, description="Primary industry sector")
#     #keywords: Optional[List[str]]       = Field(None, description="Salient free-text phrases")
#     keywords: List[str] = Field(
#         default_factory=list,
#         description="Free‑text descriptors **not captured** by other fields"
#     )
#     country: Optional[str]              = Field(None, description="Country of origin or operation")
#     ebitda_min: Optional[float]         = Field(None, description="Minimum EBITDA in USD millions")
#     revenue_min: Optional[float]        = Field(None, description="Minimum revenue in USD millions")
#     rev_growth_min: Optional[float]     = Field(None, description="Minimum ARR growth (%)")
#     market_cap_min: Optional[float]     = Field(None, description="Minimum market cap in USD millions")
#     budget: Optional[float]             = Field(None, description="Investor budget in USD millions")
#     theme: Optional[ThemeLiteral]       = Field( # type: ignore
#         None,
#         description="One of the predefined themes. Return null if none apply."
#     )

from typing import Optional, Literal, List
from pydantic import BaseModel, Field

from agent_service.theme_taxonomy import THEMES
from agent_service.sector_taxonomy import SECTOR_SUBSECTOR_MAP

# ─── canonical literals ────────────────────────────────────────────────────
ThemeLiteral  = Literal[*THEMES]                     # e.g. "Virtual Care & Digital Health"
SectorLiteral = Literal[*SECTOR_SUBSECTOR_MAP.keys()]  # e.g. "Healthcare"

class StructuredQuery(BaseModel):
    sector: Optional[SectorLiteral] = Field(
        None,
        description="Primary industry sector (choose from allowed list)."
    )

    keywords: List[str] = Field(
        default_factory=list,
        description="Free-text descriptors **not captured** by other fields."
    )

    # ➜ NEW: concise, stop-word-free phrase for BM25
    keyword_query: Optional[str] = Field(
        None,
        description="LLM-generated keyword phrase (lower-case, no stop-words) "
                    "used for BM25 search, e.g. 'ai driven software clean energy'."
    )

    country: Optional[str]     = Field(None, description="Country of origin or operation")
    ebitda_min: Optional[float]     = Field(None, description="Minimum EBITDA in USD millions")
    revenue_min: Optional[float]    = Field(None, description="Minimum revenue in USD millions")
    rev_growth_min: Optional[float] = Field(None, description="Minimum ARR growth (%)")
    market_cap_min: Optional[float] = Field(None, description="Minimum market cap in USD millions")
    budget: Optional[float]         = Field(None, description="Investor budget in USD millions")

    theme: Optional[ThemeLiteral] = Field(
        None,
        description="One canonical theme from the predefined list, or null."
    )
