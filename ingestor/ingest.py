# Collect data from Yahoo Finance and push to Azure AI Search index
import os
import pandas as pd
from yfinance import Ticker
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
import logging
# Set up logging   
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load data from csv and Yahoo Finance
df = pd.read_csv("./data/sample_companies.csv")

# Clean tickers
df['ticker'] = df['ticker'].apply(lambda x : x.split(":")[1])

def build_doc(ticker: str, df_row):
    yf = Ticker(ticker)
    info = yf.info
    about = info.get("longBusinessSummary", "")
    sub_sector = df_row['sector']
    #prod  = " ".join(about.split(".")[:2])  # crude product snippet

    return {
        "ticker": ticker,
        "name": info["shortName"],
        "sector": info.get("sector", "Unknown"),
        "sub_sector": sub_sector,
        "country": info.get("country", "Unknown"),
        "ebitda_musd": round(info.get("ebitda", 0)/1e6, 1),
        "rev_growth_pct": round(info.get("revenueGrowth", 0), 2),
        "market_cap_musd": round(info.get("marketCap", 0)/1e6, 1),
        #"share_price": yf.history("1d")["Close"][-1],
        #"ai_flag": "ai" in about.lower(),
        "long_description": about,
        #"long_descriptionVector": embed(about),
        #"product_summary": prod,
        #"product_summaryVector": embed(prod),
        "@search.action": "mergeOrUpload"
    }

def collate_docs(df=df):
    # Collect data from Yahoo Finance and build JSON to push to search index
    docs = []

    for _, row in df.iterrows():
        ticker = row['ticker']
        
        try:
            doc = build_doc(ticker, row)
            docs.append(doc)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return docs


def ingest_to_search(docs, index_name="companies-index"):
    """Upload documents to Azure AI Search index."""
    load_dotenv()
    endpoint = os.environ["AZURE_SEARCH_SERVICE"]
    credential = DefaultAzureCredential()
    client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    
    # Assert we can get Azure Credential
    try:
        token = credential.get_token("https://search.azure.com/.default")
        logger.info("Token acquired for:", token)
    except Exception as e:
        logger.error(f"Failed to acquire Azure credential: {e}")

    # Assert we can connect to Azure Search Service
    try:
        index_client.get_index(args.index_name)
        logger.info("Successfully connected to Azure Search Service")
    except Exception as e:
        logger.error(f"Failed to connect to Azure Search Service: {e}")
    
    if not docs:
        print("No documents to upload")
        return []

    result = client.upload_documents(documents=docs)
    succeeded = sum(1 for r in result if r.succeeded)
    print(f"Uploaded {succeeded}/{len(result)} documents")
    return result


if __name__ == "__main__":
    documents = collate_docs()
    ingest_to_search(documents)
