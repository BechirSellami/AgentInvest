import os
import pandas as pd
from yfinance import Ticker
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from dotenv import load_dotenv
from embed import embed
import json

load_dotenv()
# Environment setup
AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_SERVICE"]
WEAVIATE_URL = "localhost:8080"

# Connect to Weaviate depending on credentials

client = weaviate.connect_to_local()
    
COLLECTION_NAME = "Company"

if not client.collections.exists(COLLECTION_NAME):
    client.collections.create(
        name=COLLECTION_NAME,
        properties=[
            Property(name="ticker", data_type=DataType.TEXT),
            Property(name="name", data_type=DataType.TEXT),
            Property(name="sector", data_type=DataType.TEXT),
            Property(name="country", data_type=DataType.TEXT),
            Property(name="ebitda_musd", data_type=DataType.NUMBER),
            Property(name="rev_growth_pct", data_type=DataType.NUMBER),
            Property(name="market_cap_musd", data_type=DataType.NUMBER),
            Property(name="description", data_type=DataType.TEXT),
        ],
        vectorizer_config=Configure.Vectorizer.none(),
        vector_index_config=Configure.VectorIndex.hnsw(),
    )

collection = client.collections.get(COLLECTION_NAME)

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
        "_vector": None  # Will be set with embedding (see below)
    }

if __name__ == "__main__":
    # Save docs for later use (avoids recreating the data)
    filename="my_docs.json"
    if not os.path.exists(filename):
        # Load dataset and clean ticker symbols
        df = pd.read_csv("./ingestor/data/sample_companies.csv")
        df['ticker'] = df['ticker'].apply(lambda x : x.split(":")[1])
        
        # Build documents from DataFrame
        docs = [build_doc(row["ticker"], row["company"]) for _, row in df.iterrows()]
        docs = [d for d in docs if d]  # Filter out None
        
        # Create embeddings for descriptions
        valid_docs = []
        vectors = []
        for d in docs:
            if not d['description']:
                print(f"Skipping {d['ticker']} - no description available.")
                continue
            else:
                vector = embed(d['description'])
                d['_vector'] = vector
                valid_docs.append(d)
                vectors.append(vector)      
        docs = valid_docs
        # Save documents to file
        with open(filename, 'w') as f:
            json.dump(docs, f, indent=4)
        print(f"Saved {len(docs)} documents to {filename}")
    else:
        # Load docs from disk
        with open(filename, 'r') as f:
            docs = json.load(f)
    
    # Upload results to Weaviate
    if docs:
        try:
            collection.data.insert_many(docs)
            print(f"Inserted {len(docs)} documents into Weaviate")
        except Exception as e:
             print("Weaviate upload failed:", e)
    else:
        print("No valid documents to upload.")
    
    # close connection to weaviate
    client.close()