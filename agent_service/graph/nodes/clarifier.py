"""Clarifier node used to extract a structured query from user input."""

from __future__ import annotations

import os
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI
import httpx

from ..state import InvestorState
from ..structured_query import StructuredQuery
from agent_service.theme_taxonomy import THEMES
from agent_service.sector_taxonomy import SECTOR_SUBSECTOR_MAP

# Build theme doc
THEME_DOC = "\n".join(f"- {t}" for t in THEMES)

# Build sector doc
SECTOR_DOC = ", ".join(f"{k}" for k in SECTOR_SUBSECTOR_MAP.keys())
SECTOR_SUBSECTOR_MAP = "\n".join(f"- {k} → {', '.join(v)}" for k, v in SECTOR_SUBSECTOR_MAP.items())


# Generate a JSON Schema string directly from the Pydantic model
JSON_SCHEMA = StructuredQuery.schema_json(indent=2)


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Return a cached OpenAI client loaded from the environment."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key, http_client=httpx.Client())

# SYSTEM_PROMPT = (
#     "You are an AI assistant that extracts a *StructuredQuery* object "
#     "for an investment search engine.\n\n"
#     "• Use the exact JSON schema supplied below.\n"
#     "For every field:\n"
#     "- If the user explicitly mentions a value, extract it.\n"
#     "- If the value is absent or unclear, output null **except** for keywords (always output a list, empty list `[]` if none).\n\n"
#     "• For the field `sector` choose **exactly one** from the allowed list or null if none apply.\n"
#     "• Fill `keywords` with any descriptive words or phrases that do **not** belong to sector, country or numeric filters.\n"
#     "• For the field `theme` choose **exactly one** from the allowed list or null if none apply.\n"
#     "• Output only valid JSON, with no additional keys or comments.\n" 
#     "• Do not invent numbers.\n\n"
#     "### Allowed sectors\n"
#     f"{{SECTOR_DOC}}\n\n"
#     "### Sector–Theme mapping\n"
#     f"{{SECTOR_SUBSECTOR_MAP}}"
#     "### Allowed themes\n"
#     f"{{THEME_DOC}}\n\n"
#     "### JSON schema\n"
#     f"{{JSON_SCHEMA}}"
# )

SYSTEM_PROMPT = (
    "You are an AI assistant that converts a user's request into a *StructuredQuery* "
    "object for an investment-search engine.\n\n"

    "────────────────────────────────────────\n"
    "🔑  Extraction rules\n"
    "────────────────────────────────────────\n"
    "• Use **exactly** the JSON schema provided below.\n"
    "• For each field:\n"
    "  – If the user states a value explicitly, extract it.\n"
    "  – If absent or unclear, output null — **except** for `keywords` "
    "    (always return a list, empty `[]` if none).\n"
    "• For `sector` choose **one** value from the allowed list or null.\n"
    "• For `theme` choose **one** value from the allowed list or null.\n"
    "• Do **not** invent numbers; leave numeric fields null unless mentioned.\n"
    "• Output only valid JSON, no comments or extra keys.\n\n"

    "────────────────────────────────────────\n"
    "🔍  keyword_query  (NEW FIELD)\n"
    "────────────────────────────────────────\n"
    "Add a string field called `keyword_query`:\n"
    "• Rephrase the user's intent into a concise keyword-style phrase.\n"
    "• Lower-case, remove stop-words, punctuation, and connector words.\n"
    "• Keep important multi-word expressions together (e.g. “clean energy”).\n"
    "• Example transformations:\n"
    "    - “Find AI-enabled healthcare companies with over $1B EBITDA”\n"
    "        → \"ai enabled healthcare\"\n"
    "    - “Utilities companies with strong AI-driven software for clean energy”\n"
    "        → \"ai driven software clean energy\"\n\n"

    "────────────────────────────────────────\n"
    "📋  Few-shot examples\n"
    "────────────────────────────────────────\n"
    "**User 1**\n"
    "Find AI-enabled healthcare companies with over $1B EBITDA\n\n"
    "**Assistant (JSON)**\n"
    "{\n"
    "  \"sector\": \"Healthcare\",\n"
    "  \"keywords\": [\"AI-enabled\"],\n"
    "  \"country\": null,\n"
    "  \"ebitda_min\": 1000.0,\n"
    "  \"revenue_min\": null,\n"
    "  \"rev_growth_min\": null,\n"
    "  \"market_cap_min\": null,\n"
    "  \"budget\": null,\n"
    "  \"theme\": \"Virtual Care & Digital Health\",\n"
    "  \"keyword_query\": \"ai enabled healthcare\"\n"
    "}\n\n"
    "**User 2**\n"
    "Utilities companies with strong AI-driven software for clean energy\n\n"
    "**Assistant (JSON)**\n"
    "{\n"
    "  \"sector\": \"Utilities\",\n"
    "  \"keywords\": [\"AI-driven software\", \"clean energy\"],\n"
    "  \"country\": null,\n"
    "  \"ebitda_min\": null,\n"
    "  \"revenue_min\": null,\n"
    "  \"rev_growth_min\": null,\n"
    "  \"market_cap_min\": null,\n"
    "  \"budget\": null,\n"
    "  \"theme\": \"ESG & Sustainability Analytics\",\n"
    "  \"keyword_query\": \"ai driven software clean energy\"\n"
    "}\n\n"

    "────────────────────────────────────────\n"
    "✅  Reference data\n"
    "────────────────────────────────────────\n"
    "### Allowed sectors\n"
    "{SECTOR_DOC}\n\n"
    "### Sector–Subsector mapping\n"
    "{SECTOR_SUBSECTOR_MAP}\n\n"
    "### Allowed themes\n"
    "{THEME_DOC}\n\n"
    "### JSON schema\n"
    "{JSON_SCHEMA}"
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
        #structured["keywords"] is None \
        structured["theme"] is None
    )
    state.budget = structured.get("budget")
    
    return state
