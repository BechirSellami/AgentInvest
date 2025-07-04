"""Utilities for filling defaults and building Weaviate query parameters."""

from __future__ import annotations

from weaviate.collections.classes.filters import Filter
from typing import List, Optional
import logging


from ..state import InvestorState
from ingestor.embed import embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristics / defaults
DEFAULTS = {
    "ebitda_min": 0.0,
    "revenue_min": 0.0,
    "rev_growth_min": 0.0,
    "market_cap_min": 0.0
}

INFER_SECTOR_KEYWORDS = {
    "cyber": "Cybersecurity",
    "climate": "Clean Energy",
    "net-zero": "Clean Energy",
    "edtech": "EdTech",
    "health": "HealthTech",
    "saas": "Enterprise SaaS",
}
# ---------------------------------------------------------------------------


def _infer_sector_from_keywords(keywords: Optional[List[str]]) -> Optional[str]:
    """Return a sector guess based on common keywords."""
    if not keywords:
        return None
    blob = " ".join(keywords).lower()
    for kw, sector in INFER_SECTOR_KEYWORDS.items():
        if kw in blob:
            return sector
    return None


def _build_where(q: dict) -> Optional[Filter]:
    """Convert structured query into a Weaviate `_Filters` object."""
    filters = []

    if q["sector"]:
        filters.append(Filter.by_property("sector").equal(q["sector"]))

    if q["country"]:
        filters.append(Filter.by_property("country").equal(q["country"]))
    
    if q["ebitda_min"] > 0:
        filters.append(Filter.by_property("ebitda_musd").greater_than(q["ebitda_min"]))

    if q["rev_growth_min"] > 0:
        filters.append(Filter.by_property("rev_growth_pct").greater_than(q["rev_growth_min"]))

    if q["market_cap_min"] > 0:
        filters.append(Filter.by_property("market_cap_musd").greater_than(q["market_cap_min"]))

    if not filters:
        return None
    elif len(filters) == 1:
        return filters[0]
    else:
        return Filter.all_of(filters)


def query_fix(state: InvestorState) -> InvestorState:
    """Fill defaults, infer sector and create Weaviate query helpers."""
    logger.info("Query_fix agent received structured_query: %s", state.structured_query)
    
    q = state.structured_query.copy()

    if q["sector"] is None:
        q["sector"] = _infer_sector_from_keywords(q.get("keywords"))

    for fld, default in DEFAULTS.items():
        if q.get(fld) is None:
            print(f"Replacing {fld} by default {default}")
            q[fld] = default

    state.where_filter = _build_where(q)

    concepts = []
    if q["keywords"]:
        concepts.extend(q["keywords"])
    if q["theme"]:
        concepts.append(q["theme"])
    if q["sector"]:
        concepts.append(q["sector"])
    if q["country"]:
        concepts.append(q["country"])    
    
    if not concepts:
        raise ValueError("No keywords or sector provided for query.")
    logger.info("Generated concepts for embedding: %s", concepts)

    # Generate near_text embedding from keywords and sector
    embedding = embed(" ".join(concepts)) if concepts else None
    state.near_vector = embedding
        
    state.structured_query = q

    return state
