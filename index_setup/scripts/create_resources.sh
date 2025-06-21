#!/usr/bin/env bash
set -euo pipefail

# -----------  VARIABLES  -------------
RG='ai-invest-demo'
LOC='eastus'
RAND_ID=$RANDOM
SEARCH_NAME='aisearchdemo'$RAND_ID          # must be globally unique
INDEX_NAME='companies'
AOAI_NAME='aoai'$RAND_ID
EMB_DEPLOY='text-embedding-3-small'
GPT_DEPLOY='gpt-4o'
SKUS='s0'                                  # both Search & AOAI

# -----------  RESOURCE GROUP ----------
az group create -n "$RG" -l "$LOC"

# -----------  SEARCH SERVICE ----------
az extension add --name azure-search   # one-time
az search service create \
  --name "$SEARCH_NAME" \
  --resource-group "$RG" \
  --location "$LOC" \
  --sku standard \
  --partition-count 1 \
  --replica-count 1

# -----------  AZURE OPENAI ------------
az cognitiveservices account create \
  --kind OpenAI \
  --name "$AOAI_NAME" \
  --resource-group "$RG" \
  --location "$LOC" \
  --sku "$SKUS"

az cognitiveservices account deployment create \
  --resource-group "$RG" --name "$AOAI_NAME" \
  --deployment-name "$EMB_DEPLOY" \
  --model-name text-embedding-3-small --model-version "1106" \
  --sku "$SKUS"

az cognitiveservices account deployment create \
  --resource-group "$RG" --name "$AOAI_NAME" \
  --deployment-name "$GPT_DEPLOY" \
  --model-name gpt-4o --model-version "latest" \
  --sku "$SKUS"

# -----------  KEYS & ENDPOINTS ---------
SEARCH_KEY=$(az search admin-key show -g "$RG" -n "$SEARCH_NAME" --query primaryKey -o tsv)
AOAI_KEY=$(az cognitiveservices account keys list -g "$RG" -n "$AOAI_NAME" --query key1 -o tsv)
AOAI_ENDPOINT=$(az cognitiveservices account show -g "$RG" -n "$AOAI_NAME" --query properties.endpoint -o tsv)

echo ">> Search admin key: $SEARCH_KEY"
echo ">> AOAI endpoint   : $AOAI_ENDPOINT"
echo ">> AOAI key        : $AOAI_KEY"

# -----------  CREATE INDEX -------------
curl -X PUT \
  "https://${SEARCH_NAME}.search.windows.net/indexes/${INDEX_NAME}?api-version=2023-11-01-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_KEY}" \
  -d @index_schema.json

echo "Index '${INDEX_NAME}' created on ${SEARCH_NAME}"