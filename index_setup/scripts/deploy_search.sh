#!/usr/bin/env bash
set -euo pipefail

RG="ai-invest-demo"
LOC="eastus"
TEMPLATE="search_template.json"
PARAMS="search_parameters.json"
RAND_ID=$RANDOM

az deployment group create \
  --name "search-deployment-$RAND_ID" \
  --resource-group "$RG" \
  --template-file "$TEMPLATE" \
  --parameters @"$PARAMS"
