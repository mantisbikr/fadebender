#!/bin/bash
# Check Vertex AI Search import status

OPERATION_ID="import-documents-3739287128949448167"
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
create_time = metadata.get('createTime', 'unknown')
update_time = metadata.get('updateTime', 'unknown')

print(f'Status: {'✅ DONE' if done else '🔄 IN PROGRESS'}')
print(f'Total Files: {total}')
print(f'Success: {success}')
print(f'Failures: {failure}')
print(f'Started: {create_time}')
print(f'Updated: {update_time}')

if done:
    print('\n✅ Import complete! You can now test search queries.')
else:
    print('\n⏳ Still processing... check again in a few minutes.')
"
