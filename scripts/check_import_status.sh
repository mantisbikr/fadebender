#!/bin/bash
# Check Vertex AI Search import status

OPERATION_ID="import-documents-3140478597672288847"
PROJECT_ID="487213218407"

echo "Checking Vertex AI Search import status..."
echo "================================================"

TOKEN=$(gcloud auth print-access-token)
curl -s -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores/fadebender-knowledge/branches/0/operations/$OPERATION_ID" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
done = d.get('done', False)
meta = d.get('metadata', {})
total = meta.get('totalCount', 0)
success = meta.get('successCount', 0)
failure = meta.get('failureCount', 0)

if done:
    print('✅ Status: DONE')
else:
    print('🔄 Status: IN PROGRESS')

print(f'Total Files: {total}')
print(f'Successful: {success}')
print(f'Failed: {failure}')
print(f'Started: {meta.get(\"createTime\", \"N/A\")}')

if done:
    if int(success) > 0:
        print(f'\n✅ SUCCESS! {success} documents indexed')
        print('You can now test search queries!')
    if int(failure) > 0:
        print(f'\n⚠️  WARNING: {failure} documents failed')
        print('Check error samples for details')
else:
    print('\n⏳ Import still running... check again in 2-3 minutes')
"
