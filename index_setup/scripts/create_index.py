from dotenv import load_dotenv
import os
import logging

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient

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


# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AZURE_SEARCH_SERVICE = os.environ["AZURE_SEARCH_SERVICE"]
AZURE_OPENAI_ACCOUNT = os.environ["AZURE_OPENAI_ACCOUNT"]
AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_KEY"]
AZURE_AI_MULTISERVICE_ACCOUNT = os.environ["AZURE_AI_MULTISERVICE_ACCOUNT"]
AZURE_AI_MULTISERVICE_KEY = os.environ["AZURE_AI_MULTISERVICE_KEY"]

# Setup Azure credentials
credential = DefaultAzureCredential()

index_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)

# Assert we can get Azure Credential
try:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://search.azure.com/.default")
    print("Token acquired for:", token)
except Exception as e: 
    print(f"Failed to acquire Azure credential: {e}")
    token = None 
    logger.info("Token acquired for: %s", token)
except Exception as e:
    logger.error("Failed to acquire Azure credential: %s", e)
    token = None

# Assert we can connect to Azure Search Service
try:
    index_client.get_index("companies-index")
    print("Successfully connected to Azure Search Service")
    logger.info("Successfully connected to Azure Search Service")
except Exception as e:
    print(f"Failed to connect to Azure Search Service: {e}")
    logger.error("Failed to connect to Azure Search Service: %s", e)
    
# Assert we can connect to Azure OpenAI Service
try:
    openai_credential = get_bearer_token_provider(
        AZURE_OPENAI_ACCOUNT,
        AZURE_OPENAI_KEY,
        "https://cognitiveservices.azure.com/.default"
        )
    print("Successfully connected to Azure OpenAI Service")
    logger.info("Successfully connected to Azure OpenAI Service")
except Exception as e:
    print(f"Failed to connect to Azure OpenAI Service: {e}")
    logger.error("Failed to connect to Azure OpenAI Service: %s", e)
    
# Assert we can connect to Azure AI Multiservice
try:
    multiservice_credential = get_bearer_token_provider(
        AZURE_AI_MULTISERVICE_ACCOUNT,
        AZURE_AI_MULTISERVICE_KEY,
        "https://cognitiveservices.azure.com/.default"
    )
    print("Successfully connected to Azure AI Multiservice")
    logger.info("Successfully connected to Azure AI Multiservice")
except Exception as e:
    print(f"Failed to connect to Azure AI Multiservice: {e}")
    logger.error("Failed to connect to Azure AI Multiservice: %s", e)


# This script creates an Azure AI Search index for company data with vector search capabilities. 
# It uses the Azure SDK for Python to define the index schema, including fields for company information and a vector field for text embeddings.

# Create a search index  
index_name = "companies-index"
index_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)

# --------

fields = [
    SearchField(name="ticker", type=SearchFieldDataType.String, key=True, filterable=True,),  
    SearchField(name="name", type=SearchFieldDataType.String, searchable=True),
    SearchField(name="sector", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SearchField(name="country", type=SearchFieldDataType.String, filterable=True),
    SearchField(name="ebitda_musd", type=SearchFieldDataType.Double, filterable=True, sortable=True),
    SearchField(name="rev_growth_pct", type=SearchFieldDataType.Double, sortable=True),
    SearchField(name="market_cap_musd", type=SearchFieldDataType.Double, sortable=True),
    SearchField(name="description", type=SearchFieldDataType.String, sortable=False, filterable=False, facetable=False),  
    SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1024, vector_search_profile_name="myHnswProfile")
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
                resource_url=AZURE_OPENAI_ACCOUNT,  
                deployment_name="text-embedding-3-large",
                model_name="text-embedding-3-large"
            ),
        ),  
    ], 
)  
  
# Create the search index
index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)  
result = index_client.create_or_update_index(index)  
print(f"{result.name} created")  
result = index_client.create_or_update_index(index)
logger.info("%s created", result.name)