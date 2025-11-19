#!/usr/bin/env python3
import subprocess
import json
import sys

# Get access token
token_result = subprocess.run(['gcloud', 'auth', 'print-access-token'],
                              capture_output=True, text=True)
token = token_result.stdout.strip()

# Fetch operation status
curl_cmd = [
    'curl', '-s', '-X', 'GET',
    '-H', f'Authorization: Bearer {token}',
    'https://discoveryengine.googleapis.com/v1/projects/487213218407/locations/global/collections/default_collection/dataStores/fadebender-knowledge/branches/0/operations/import-documents-3140478597672288847'
]

result = subprocess.run(curl_cmd, capture_output=True, text=True)
data = json.loads(result.stdout)

print("=" * 60)
print("IMPORT STATUS")
print("=" * 60)
print(f"Done: {data.get('done', False)}")
print(f"Success Count: {data.get('metadata', {}).get('successCount', 0)}")
print(f"Failure Count: {data.get('metadata', {}).get('failureCount', 0)}")
print(f"Total Count: {data.get('metadata', {}).get('totalCount', 0)}")
print(f"Started: {data.get('metadata', {}).get('createTime', 'N/A')}")
print(f"Updated: {data.get('metadata', {}).get('updateTime', 'N/A')}")
print()

if 'response' in data and 'errorSamples' in data.get('response', {}):
    print("=" * 60)
    print("ERROR SAMPLES (First 5):")
    print("=" * 60)
    for i, err in enumerate(data['response']['errorSamples'][:5], 1):
        print(f"\n{i}. Code: {err.get('code', 'N/A')}")
        print(f"   Message: {err.get('message', 'No message')}")
        if 'details' in err:
            for detail in err['details']:
                if 'resourceName' in detail:
                    print(f"   File: {detail['resourceName']}")
