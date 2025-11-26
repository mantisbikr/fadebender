#!/bin/bash
# Check Vertex AI Search import status

OPERATION_ID="import-documents-16670553921463527818"
PROJECT_ID="487213218407"

echo "Checking Vertex AI Search import status..."
echo "================================================"

RESPONSE=$(curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores/fadebender-knowledge/branches/0/operations/$OPERATION_ID")

echo "$RESPONSE" | python3 -c "
import json
import sys
data = json.load(sys.stdin)

done = data.get('done', False)
metadata = data.get('metadata', {})
total = metadata.get('totalCount', '0')
success = metadata.get('successCount', '0')
failure = metadata.get('failureCount', '0')

print(f'Status: {json.dumps(metadata, indent=2)}') 
"
