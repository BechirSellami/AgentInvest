import os
import pandas as pd
from yfinance import Ticker
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from embed import embed
from pprint import pprint

load_dotenv()
# Environment setup
AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_SERVICE"]
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Initialize Azure Search client
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name="companies-index",
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2024-02-01"
)

def sanitize_key(key: str) -> str:
    return key.replace(".", "_")


def build_doc(ticker: str, name):
    yf = Ticker(ticker)
    info = yf.info
    about = info.get("longBusinessSummary", "")

    return {
        "ticker": sanitize_key(ticker),
        "name": name,
        "sector": info.get("sector", "Unknown"),
        "country": info.get("country", "Unknown"),
        "ebitda_musd": round(info.get("ebitda", 0)/1e6, 1),
        "rev_growth_pct": round(info.get("revenueGrowth", 0), 2),
        "market_cap_musd": round(info.get("marketCap", 0)/1e6, 1),
        "description": about,
        "text_vector": None,  # Will be set with embedding (see below)
        "@search.action": "mergeOrUpload"
    }

if __name__ == "__main__":
    # Load dataset and clean ticker symbols
    df = pd.read_csv("./data/sample_companies.csv")
    df['ticker'] = df['ticker'].apply(lambda x : x.split(":")[1])
    
    # Build documents from DataFrame
    docs = [build_doc(row["ticker"], row["company"]) for _ , row in df.iterrows()]
    docs = [d for d in docs if d]  # Filter out None
    
    # Create embeddings for descriptions
    for d in docs:
        if not d['description']:
            print(f"Skipping {d['ticker']} - no description available.")
        else:
            d['text_vector'] = embed(d['description'])
    docs = [d for d in docs if d['text_vector']]  # Filter out None vectors
    
    # Upload results to Azure Search Index
    if docs:
        try:
            result = search_client.upload_documents(documents=docs)
            print("Upload result:", result)
        except Exception as e:
            print("Azure Search upload failed:", e)
    else:
        print("No valid documents to upload.")