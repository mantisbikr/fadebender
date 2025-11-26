#!/bin/bash

PROJECT_ID="487213218407"
LOCATION="global"
DATA_STORE_ID="fadebender-knowledge"
BRANCH_ID="0"
GCS_URI="gs://fadebender-knowledge/fadebender/user-guide.html"

echo "Triggering Vertex AI Search import for $GCS_URI..."

ACCESS_TOKEN=$(gcloud auth print-access-token)

curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  "https://discoveryengine.googleapis.com/v1beta/projects/$PROJECT_ID/locations/$LOCATION/collections/default_collection/dataStores/$DATA_STORE_ID/branches/$BRANCH_ID/documents:import" \
  -d '{
    "reconciliationMode": "INCREMENTAL",
    "gcsSource": {
      "inputUris": ["'"$GCS_URI"'"],
      "dataSchema": "content"
    }
  }'

echo ""
echo "Request sent."
