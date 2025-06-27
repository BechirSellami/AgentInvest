
"""Clarifier node used to extract a structured query from user input."""
from __future__ import annotations

import os
from dotenv import load_dotenv
from openai import OpenAI
 
from ..state import InvestorState
from ..structured_query import StructuredQuery
 
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
 
client = OpenAI(api_key=OPENAI_API_KEY)
 
SYSTEM_PROMPT = (
    "You are an AI assistant that extracts a structured screening query for an "
    "investment-search engine. Use the JSON schema provided. If a field is truly "
    "absent or unclear, return null for that field. Do NOT invent numbers."
)
 
def clarifier(state: InvestorState) -> InvestorState:
    """Populate ``state`` with a structured query derived from the user text."""
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        tools=[{
            "type": "function",
            "function": {
                "name": "extract_query",
                "description": "Convert user query into a structured filter object.",
                "parameters": StructuredQuery.schema(),
            },
         }],
        tool_choice={"type": "function", "function": {"name": "extract_query"}},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": state.user_query},
        ],
     )
 

    tool_args = response.choices[0].message.tool_calls[0].function.arguments
    structured = StructuredQuery.model_validate_json(tool_args).model_dump()
 
    state.structured_query = structured
    state.need_clarification = (
        structured["sector"] is None and structured["keywords"] is None
    )
    state.budget = structured.get("budget")
 
    return state
