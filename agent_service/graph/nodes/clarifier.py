# Standard library imports
import os
from dotenv import load_dotenv

# Third-party library imports
from openai import OpenAI

# Local application imports
from state import InvestorState, StructuredQuery

load_dotenv()

 # Retrieve configuration from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

# Initialize the OpenAI client
client = OpenAI(api_key=openai_api_key)

SYSTEM_PROMPT = """
You are an AI assistant that extracts a structured screening query for an
investment-search engine. Use the JSON schema provided. If a field is truly
absent or unclear, return null for that field. Do NOT invent numbers.
"""

def clarifier(state: InvestorState) -> InvestorState:
    # 1 — Send user prompt + function schema to GPT-4-o
    response = client.chat.completions.create(
        model      = "gpt-4o",
        temperature= 0,
        tools=[{
            "type": "function",
            "function": {
                "name": "extract_query",
                "description": "Convert user query into a structured filter object.",
                "parameters": StructuredQuery.schema()  # ← automatic JSON schema
            }
        }],
        tool_choice={"type":"function","function":{"name":"extract_query"}},
        messages=[
            {"role":"system", "content": SYSTEM_PROMPT},
            {"role":"user",   "content": state.user_query}
        ]
    )

    # 2 — Read the function-call argument (already JSON) and validate with Pydantic
    tool_args = response.choices[0].message.tool_calls[0].function.arguments
    structured = StructuredQuery.model_validate_json(tool_args).model_dump()

    # 3 — If critical fields missing, flag for a follow-up question
    need_clarification = structured["sector"] is None and structured["keywords"] is None

    # 4 — Write back to state
    state.structured_query   = structured
    state.need_clarification = need_clarification
    state.budget             = structured.get("budget")   # convenience
    
    return state
