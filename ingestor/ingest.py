# standard-library
import json
import logging
import os
from functools import lru_cache

# third-party
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from yfinance import Ticker
import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.data import DataObject

# local
from agent_service.theme_taxonomy import THEMES
from .embed import embed  # your local embedding helper

#
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI helper
@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)

def enrich_text(description: str) -> tuple[str, list[str], list[str]]:
    """
    Call GPT-4o → (summary, keywords, themes)
    """
    client = _get_client()
    prompt = (
        "You are an assistant that produces a short company summary, "
        "a list of salient keyword phrases, and up to 7 themes from the allowed list.\n\n"
        "Allowed themes:\n" + "\n".join(f"- {t}" for t in THEMES) + "\n\n"
        "Return JSON ONLY in this form:\n"
        '{"summary": "...", "keywords": ["..."], "themes": ["..."]}\n\n'
        f"Company description:\n'''{description}'''"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    data = json.loads(resp.choices[0].message.content)
    summary  = data.get("summary", "").strip()
    keywords = [k.strip() for k in data.get("keywords", [])][:25]
    themes   = [t for t in data.get("themes", []) if t in THEMES][:7]
    return summary, keywords, themes

# Weaviate connection
client = weaviate.connect_to_local() 
COLLECTION_NAME = os.getenv("WEAVIATE_COLLECTION")

if not client.collections.exists(COLLECTION_NAME):
    raise RuntimeError(f"Collection {COLLECTION_NAME} does not exist")

collection = client.collections.get(COLLECTION_NAME)

# helpers
def sanitize_key(key: str) -> str:
    return key.replace(".", "_")

def build_doc(ticker: str, name: str) -> dict:
    """
    Fetch Yahoo Finance info + GPT-4o enrichment.
    Returns a dict with `embed_text` (to be vectorized later).
    """
    yf   = Ticker(ticker)
    info = yf.info
    about = info.get("longBusinessSummary", "")

    try:
        summary, keywords, themes = enrich_text(about) if about else ("", [], [])
    except Exception as e:
        logger.warning("OpenAI enrichment failed for %s: %s", ticker, e)
        summary, keywords, themes = "", [], []

    #embed_text = " | ".join(filter(None, [summary, " ".join(keywords), " ".join(themes)]))
    embed_text = " | ".join(filter(None, [summary, " ".join(keywords)]))
    
    return {
        "ticker":          sanitize_key(ticker),
        "name":            name,
        "sector":          info.get("sector", "Unknown"),
        "country":         info.get("country", "Unknown"),
        "ebitda_musd":     round(info.get("ebitda", 0) / 1e6, 1),
        "rev_growth_pct":  round(info.get("revenueGrowth", 0) * 100, 0),
        "market_cap_musd": round(info.get("marketCap", 0) / 1e6, 1),
        "description":     about,
        "summary":         summary,
        "keywords":        keywords,
        "themes":          themes,
        "embed_text":      embed_text  # will be turned into a vector below
    }

# main ingest routine
if __name__ == "__main__":
    cache_file = os.path.join(os.path.dirname(__file__), "my_docs.json")

    if not os.path.exists(cache_file):
        data_path = os.path.join(os.path.dirname(__file__), "data", "sample_companies.csv")
        df = pd.read_csv(data_path)
        df["ticker"] = df["ticker"].apply(lambda x: x.split(":")[1])

        docs = [build_doc(row["ticker"], row["company"]) for _, row in df.iterrows()]
        with open(cache_file, "w") as f:
            json.dump(docs, f, indent=2)
        logger.info("Saved %d documents to %s", len(docs), cache_file)
    else:
        with open(cache_file, "r") as f:
            docs = json.load(f)

    # create embeddings & payloads
    payloads: list[DataObject] = []
    for d in docs:
        if not d["embed_text"]:
            logger.warning("Skipping %s – no text to embed", d["ticker"])
            continue

        vector = embed(d["embed_text"])           # ← your local embed() returns list[float]
        d.pop("embed_text")                       # not stored in Weaviate

        payloads.append(
            DataObject(
                properties=d,
                vector=vector
            )
        )

    if payloads:
        try:
            collection.data.insert_many(payloads)
            logger.info("Inserted %d objects", len(payloads))
        except weaviate.exceptions.WeaviateInsertManyAllFailedError as e:
            logger.error("Upload failed: %s", e)
            for idx, err in enumerate(e.errors):
                logger.error("Error %d:\n%s", idx, json.dumps(err, indent=2))
    else:
        raise RuntimeError("No valid payloads to upload")

    client.close()