"""Retrieve matching companies from Weaviate."""

from __future__ import annotations

# ── stdlib ────────────────────────────────────────────────────────────────
import os
import logging
from functools import lru_cache
from typing import Any, Dict, List

# ── third-party ───────────────────────────────────────────────────────────
from dotenv import load_dotenv
import weaviate
from weaviate.classes.query import MetadataQuery, HybridFusion

# ── local ─────────────────────────────────────────────────────────────────
from ..state import InvestorState

# ── logging / env ─────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
load_dotenv()

WEAVIATE_URL    = os.getenv("WEAVIATE_URL", "weaviate")
COLLECTION_NAME = os.getenv("WEAVIATE_COLLECTION")
RETRIEVAL_LIMIT = int(os.getenv("RETRIEVAL_LIMIT", "10"))


@lru_cache(maxsize=1)
def _get_client() -> weaviate.WeaviateClient:
    try:
        return weaviate.connect_to_local(WEAVIATE_URL)
    except Exception as exc:
        raise RuntimeError("Could not connect to Weaviate.\n" + str(exc)) from exc


def retriever(state: InvestorState) -> InvestorState:
    """Populate `state.retrieved_docs` with companies returned by Weaviate."""
    logger.info("Retriever received structured query: %s", state.structured_query)

    collection = _get_client().collections.get(COLLECTION_NAME)

    # ------------------------------------------------------------------ #
    # Build BM-25 keyword string                                         #
    # ------------------------------------------------------------------ #
    keyword_query: str = (
        getattr(state, "keyword_query", "") or
        " ".join(state.structured_query.get("keywords", []))
    ).strip()
    
    logger.info(f"Keyword_query: {keyword_query}")

    meta = MetadataQuery(distance=True, score=True)

    # ------------------------------------------------------------------ #
    # Execute query (hybrid or pure vector)                              #
    # ------------------------------------------------------------------ #
    if keyword_query:
        response = collection.query.hybrid(
            query=keyword_query,
            vector=state.near_vector,
            alpha=0.7,
            query_properties=["summary"],
            fusion_type=HybridFusion.RELATIVE_SCORE,
            limit=RETRIEVAL_LIMIT,
            filters=state.where_filter,        # ← filter goes here
            return_metadata=meta
        )
    else:
        response = collection.query.near_vector(
            near_vector=state.near_vector,
            limit=RETRIEVAL_LIMIT,
            filters=state.where_filter,        # ← filter goes here
            return_metadata=meta
        )

    # ------------------------------------------------------------------ #
    # Marshal results                                                    #
    # ------------------------------------------------------------------ #
    docs: List[Dict[str, Any]] = []
    for obj in response.objects:
        props = obj.properties or {}

        # distance for pure-vector, score for hybrid
        if obj.metadata:
            if obj.metadata.score is not None and obj.metadata.score > 0.01:
                props["_relevance"] = obj.metadata.score          # 0-1 already
                docs.append(props)

    state.retrieved_docs = docs
    logger.info("Retrieved %d documents from Weaviate.", len(docs))

    if not docs:
        state.error = "No documents found matching the query."

    return state
