"""Utilities for filling defaults and building Weaviate query parameters."""

from __future__ import annotations

from typing import List, Optional

from ..state import InvestorState

# ---------------------------------------------------------------------------
# Heuristics / defaults
DEFAULTS = {
    "ebitda_min": 0.0,
    "revenue_min": 0.0,
    "arr_growth_min": 0.0,
    "risk_profile": "medium",
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


def _build_where(q: dict) -> Optional[dict]:
    """Convert the structured query into a Weaviate ``where`` filter."""
    clauses = []

    if q["sector"]:
        clauses.append({"path": ["sector"], "operator": "Equal", "valueText": q["sector"]})

    if q["ebitda_min"] > 0:
        clauses.append({
            "path": ["ebitda_musd"],
            "operator": "GreaterThan",
            "valueNumber": q["ebitda_min"],
        })

    if q["revenue_min"] > 0:
        clauses.append({
            "path": ["market_cap_musd"],
            "operator": "GreaterThan",
            "valueNumber": q["revenue_min"],
        })

    if q["arr_growth_min"] > 0:
        clauses.append({
            "path": ["rev_growth_pct"],
            "operator": "GreaterThan",
            "valueNumber": q["arr_growth_min"],
        })

    if q["risk_profile"]:
        clauses.append({
            "path": ["risk_profile"],
            "operator": "Equal",
            "valueText": q["risk_profile"],
        })

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]

    return {"operator": "And", "operands": clauses}


def query_fix(state: InvestorState) -> InvestorState:
    """Fill defaults, infer sector and create Weaviate query helpers."""
    q = state.structured_query.copy()

    if q["sector"] is None:
        q["sector"] = _infer_sector_from_keywords(q.get("keywords"))

    for fld, default in DEFAULTS.items():
        if q.get(fld) is None:
            q[fld] = default

    state.where_filter = _build_where(q)

    concepts = []
    if q["keywords"]:
        concepts.extend(q["keywords"])
    if q["theme"]:
        concepts.append(q["theme"])
    if q["sector"]:
        concepts.append(q["sector"])

    state.near_text = {"concepts": concepts or ["high-potential company"]}
    state.structured_query = q

    return state
