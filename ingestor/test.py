import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env if available
load_dotenv()

# Retrieve configuration from environment
endpoint = os.getenv("AZURE_OPENAI_ACCOUNT")
#os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
api_version = "2024-02-01"

# Azure OpenAI API key
azure_openai_key = os.getenv("AZURE_OPENAI_KEY")

# Initialize the AzureOpenAI client correctly
client = AzureOpenAI(
    api_key=azure_openai_key,
    api_version=api_version,
    azure_endpoint=endpoint,
)

# Example request
response = client.embeddings.create(
    input=["first phrase", "second phrase", "third phrase"],
    model="text-embedding-3-large",
)

if __name__ == "__main__":
    for item in response.data:
        length = len(item.embedding)
        print(
            f"data[{item.index}]: length={length}, "
            f"[{item.embedding[0]}, {item.embedding[1]}, "
            f"..., {item.embedding[length-2]}, {item.embedding[length-1]}]"
        )
    print(response.usage)