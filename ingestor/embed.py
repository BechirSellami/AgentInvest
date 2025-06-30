import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

 # Retrieve configuration from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

# Initialize the OpenAI client
client = OpenAI(api_key=openai_api_key)

def embed(txt: str, client: OpenAI = client) -> list:
    response = client.embeddings.create(
        input=[txt],
        model=embedding_model,
        dimensions=1024,
    )
    embedding = response.data[0].embedding
    if not embedding:
        raise ValueError("Embedding response is empty.")
    if len(embedding) != 1024:
        raise ValueError(
            f"Unexpected embedding length: {len(embedding)}. Expected 1024."
        )
    return embedding