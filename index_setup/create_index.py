
from dotenv import load_dotenv
import argparse
import os
import logging

import weaviate
from weaviate.classes.config import Property, DataType, Configure
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

 
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update a Weaviate collection")
    parser.add_argument(
        "--collection-name",
        default=os.environ.get("WEAVIATE_COLLECTION"),
        help="Name of the Weaviate collection to create",
    )
    return parser.parse_args()
 
   
def main() -> None:
    load_dotenv()
    args = parse_args()
 
    client = weaviate.connect_to_local()

    if client.collections.exists(args.collection_name):
        logger.info("Collection %s exists, deleting", args.collection_name)
        client.collections.delete(args.collection_name)

    client.collections.create(
        name=args.collection_name,
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
        vector_index_config=Configure.VectorIndex.hnsw()
        )
  
    logger.info("Collection %s created", args.collection_name)
    client.close()
 
if __name__ == "__main__":
    main()