from dotenv import load_dotenv
import argparse
import os
import logging

from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndex
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Create or update an Azure Search index")
    parser.add_argument(
        "--index-name",
        default=os.environ.get("AZURE_SEARCH_INDEX", "companies-index"),
        help="Name of the index to create or update",
    )
    return parser.parse_args()


def main() -> None:
    """Script entry point."""
    load_dotenv()

    endpoint = os.environ["AZURE_SEARCH_SERVICE"]
    openai_account = os.environ["AZURE_OPENAI_ACCOUNT"]

    args = parse_args()

    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

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

    # Assert we can connect to Azure OpenAI Service
    try:
        _ = get_bearer_token_provider(
            openai_account,
            os.environ.get("AZURE_OPENAI_KEY", ""),
            "https://cognitiveservices.azure.com/.default",
        )
        logger.info("Successfully connected to Azure OpenAI Service")
    except Exception as e:
        logger.error(f"Failed to connect to Azure OpenAI Service: {e}")

    # This script creates an Azure AI Search index for company data with vector search capabilities.
    # It uses the Azure SDK for Python to define the index schema, including fields for company information and a vector field for text embeddings.

    # Create a search index
    index_name = args.index_name
    
    # Define the fields for the index
    fields = [
        SearchField(name="ticker", type=SearchFieldDataType.String, key=True, filterable=True,),
        SearchField(name="name", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="sector", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="country", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="ebitda_musd", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SearchField(name="rev_growth_pct", type=SearchFieldDataType.Double, sortable=True),
        SearchField(name="market_cap_musd", type=SearchFieldDataType.Double, sortable=True),
        SearchField(name="description", type=SearchFieldDataType.String, sortable=False, filterable=False, facetable=False),
        SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1024, vector_search_profile_name="myHnswProfile"),
    ]
  
    # Configure the vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="myHnsw"),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                vectorizer_name="myOpenAI",
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="myOpenAI",
                kind="azureOpenAI",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_account,
                    deployment_name="text-embedding-3-large",
                    model_name="text-embedding-3-large",
                ),
            ),
        ],
    )
  
    # Create the search index
    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
    result = index_client.create_or_update_index(index)
    print(f"{result.name} created")


if __name__ == "__main__":
    main()
