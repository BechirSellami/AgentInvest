import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

 # Retrieve configuration from environment
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
if not endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

api_version = "2024-02-01"

# Azure OpenAI API key
azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
if not azure_openai_key:
    raise ValueError("AZURE_OPENAI_KEY environment variable is not set.")

embedding_deployment = "text-embedding-2525"

# Initialize the AzureOpenAI client correctly
client = AzureOpenAI(
    api_key=azure_openai_key,
    api_version=api_version,
    azure_endpoint=endpoint
)

def embed(txt, client=client):
    response = client.embeddings.create(
                input=[txt],
                model=embedding_deployment,
                dimensions=1024
            )
    embedding = response.data[0].embedding
    if not embedding:
        raise ValueError("Embedding response is empty.")
    if len(embedding) != 1024:
        raise ValueError(f"Unexpected embedding length: {len(embedding)}. Expected 1024.")
        
    return embedding