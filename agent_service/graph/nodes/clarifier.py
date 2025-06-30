"""Clarifier node used to extract a structured query from user input."""

from __future__ import annotations

import os
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI
import httpx

from ..state import InvestorState
from ..structured_query import StructuredQuery


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Return a cached OpenAI client loaded from the environment."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key, http_client=httpx.Client())


SYSTEM_PROMPT = (
    "You are an AI assistant that extracts a structured screening query for an "
    "investment-search engine. Use the JSON schema provided. If a field is truly "
    "absent or unclear, return null for that field. Do NOT invent numbers."
)


def clarifier(state: InvestorState) -> InvestorState:
    """Populate ``state`` with a structured query derived from the user text."""
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "extract_query",
                    "description": "Convert user query into a structured filter object.",
                    "parameters": StructuredQuery.schema(),
                },
            }
        ],
        tool_choice={"type": "function", "function": {"name": "extract_query"}},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": state.user_query},
        ],
    )

    tool_args = response.choices[0].message.tool_calls[0].function.arguments
    structured = StructuredQuery.model_validate_json(tool_args).model_dump()

    state.structured_query = structured
    # The user needs to provide at least one of sector or keywords. Otherwise, we need clarification.
    state.need_clarification = (
        structured["sector"] is None \
        and structured["keywords"] is None \
        and structured["ebitda_min"] is None \
        and structured["revenue_min"] is None \
        and structured["arr_growth_min"] is None
        and structured["risk_profile"] is None \
        and structured["theme"] is None
    )
    state.budget = structured.get("budget")
    
    return state
