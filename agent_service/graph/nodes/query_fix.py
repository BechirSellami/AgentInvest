"""
Query-Fix node
─────────────────────────────────
• Imputes sensible defaults into StructuredQuery.
• Produces:
      state.where_filter:   GraphQL 'where' dict
      state.near_text:      {'concepts':[...]} for .with_near_text()
"""

from typing import List, Optional
from state import InvestorState

# ──────────────────────────────────────────────────────────────────────────────
# Heuristics / defaults
DEFAULTS = {
    "ebitda_min":      0.0,
    "revenue_min":     0.0,
    "arr_growth_min":  0.0,
    "risk_profile":    "medium"
}
INFER_SECTOR_KEYWORDS = {
    "cyber":    "Cybersecurity",
    "climate":  "Clean Energy",
    "net-zero": "Clean Energy",
    "edtech":   "EdTech",
    "health":   "HealthTech",
    "saas":     "Enterprise SaaS"
}
# ──────────────────────────────────────────────────────────────────────────────


def _infer_sector_from_keywords(keywords: Optional[List[str]]) -> Optional[str]:
    if not keywords:
        return None
    blob = " ".join(keywords).lower()
    for kw, sector in INFER_SECTOR_KEYWORDS.items():
        if kw in blob:
            return sector
    return None


def _build_where(q: dict) -> dict | None:
    """
    Turn the fully-populated StructuredQuery into a Weaviate GraphQL 'where'.
    Returns None when no filter clauses were created.
    """
    clauses = []

    if q["sector"]:
        clauses.append({"path": ["sector"],
                        "operator": "Equal",
                        "valueText": q["sector"]})

    if q["ebitda_min"] > 0:
        clauses.append({"path": ["ebitda_musd"],
                        "operator": "GreaterThan",
                        "valueNumber": q["ebitda_min"]})

    if q["revenue_min"] > 0:
        clauses.append({"path": ["market_cap_musd"],
                        "operator": "GreaterThan",
                        "valueNumber": q["revenue_min"]})

    if q["arr_growth_min"] > 0:
        clauses.append({"path": ["rev_growth_pct"],
                        "operator": "GreaterThan",
                        "valueNumber": q["arr_growth_min"]})

    if q["risk_profile"]:
        clauses.append({"path": ["risk_profile"],
                        "operator": "Equal",
                        "valueText": q["risk_profile"]})

    if not clauses:            # no numeric/sector constraints
        return None
    if len(clauses) == 1:      # single filter → return it verbatim
        return clauses[0]

    return {                   # multiple clauses → AND them
        "operator": "And",
        "operands": clauses
    }


def query_fix(state: InvestorState) -> InvestorState:
    """
    Fills in defaults, infers sector when missing,
    and crafts Weaviate 'where' & 'nearText' dicts.
    """
    q = state.structured_query.copy()

    # ── Infer sector ──────────────────────────────────────────────────────────
    if q["sector"] is None:
        q["sector"] = _infer_sector_from_keywords(q.get("keywords"))

    # ── Apply defaults ───────────────────────────────────────────────────────
    for fld, default in DEFAULTS.items():
        if q.get(fld) is None:
            q[fld] = default

    # ── Build Weaviate filter & semantic query ───────────────────────────────
    state.where_filter = _build_where(q)

    concepts = []
    if q["keywords"]:
        concepts.extend(q["keywords"])
    if q["theme"]:
        concepts.append(q["theme"])
    if q["sector"]:
        concepts.append(q["sector"])

    state.near_text = {"concepts": concepts or ["high-potential company"]}

    # ── Persist back to global state ─────────────────────────────────────────
    state.structured_query = q
    
    return state
