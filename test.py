import weaviate
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = weaviate.connect_to_local({
        "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
    })
    
try:
    questions = client.collections.get("Company")
    response = questions.query.near_text(
        query="fintech",
        #where={"path": ["sector"], "operator": "Equal", "valueText": "FinTech"},
        return_metadata=["distance"],
        limit=2
    )

    for obj in response.objects:
        print(json.dumps(obj.properties, indent=2))
finally:
    client.close()