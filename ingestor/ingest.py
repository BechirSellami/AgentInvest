# Collect data from Yahoo Finance and push to Azure AI Search index
import pandas as pd
from yfinance import Ticker
import time 

# Load data from csv and Yahoo Finance
df = pd.read_csv("../data/sample_companies.csv")

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
        sub_field = row['sector']
        
        try:
            doc = build_doc(ticker)
            docs.append(doc)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return docs