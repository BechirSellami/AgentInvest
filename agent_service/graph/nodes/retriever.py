"""Retrieve matching companies from Weaviate."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, List, Dict

from dotenv import load_dotenv
import weaviate
from weaviate.classes.query import MetadataQuery

from ..state import InvestorState

import logging
logger = logging.getLogger(__name__)

# @lru_cache(maxsize=1)
# def _get_client() -> weaviate.WeaviateClient:
#     """Return a cached Weaviate client"""
#     try:
#         return weaviate.connect_to_local()
#     except Exception as e:
#         raise RuntimeError(
#             f"Failed to connect to Weaviate. Ensure the Weaviate server is running and accessible.\n{e}"
#         )


def retriever(state: InvestorState) -> InvestorState:
    """Populate ``state`` with documents retrieved from Weaviate."""
    client = weaviate.connect_to_local()
    collection_name = os.getenv("WEAVIATE_COLLECTION")
    limit = int(os.getenv("RETRIEVAL_LIMIT", "10"))
    
    logger.info("Retriever received state: %s", state)

    collection = client.collections.get(collection_name)
    response = collection.query.near_vector(
        near_vector=state.near_vector,
        filters=state.where_filter,
        limit=limit,
        return_metadata=MetadataQuery(distance=True),
    )
    
    docs: List[Dict[str, Any]] = []
    for obj in response.objects:
        props = obj.properties or {}
        if obj.metadata:
            props["_distance"] = obj.metadata.distance
        docs.append(props)

    state.retrieved_docs = docs
    print(f"Retrieved {len(docs)} documents from Weaviate.")
    if not docs:
        state.error = "No documents found matching the query."
        return state
    return state