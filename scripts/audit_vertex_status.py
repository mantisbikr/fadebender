import subprocess
import json

PROJECT_NUMBER = "487213218407"
ACCESS_TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()

def run_curl(url):
    cmd = [
        "curl", "-s", "-X", "GET",
        "-H", f"Authorization: Bearer {ACCESS_TOKEN}",
        "-H", "X-Goog-User-Project: fadebender",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": "curl failed", "stderr": result.stderr}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "invalid json", "stdout": result.stdout}

print("--- Checking Data Stores ---")
ds_url = f"https://discoveryengine.googleapis.com/v1beta/projects/{PROJECT_NUMBER}/locations/global/collections/default_collection/dataStores"
print(json.dumps(run_curl(ds_url), indent=2))

print("\n--- Checking Engines (Apps) ---")
eng_url = f"https://discoveryengine.googleapis.com/v1beta/projects/{PROJECT_NUMBER}/locations/global/collections/default_collection/engines"
print(json.dumps(run_curl(eng_url), indent=2))
