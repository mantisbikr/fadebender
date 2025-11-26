import requests
import json
import sys

# Configuration
# Adjust URL if your local emulator is on a different port
# Standard Firebase Emulator port for functions is 5001
BASE_URL = "http://127.0.0.1:5001/fadebender/us-central1"
HELP_ENDPOINT = f"{BASE_URL}/help"

def test_rag_query(query):
    print(f"\n🔹 Query: '{query}'")
    print("-" * 40)
    
    try:
        response = requests.post(
            HELP_ENDPOINT,
            json={"query": query, "userId": "test-rag-cli"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return

        data = response.json()
        
        # Print the Answer
        print(f"📝 Answer:\n{data.get('response', 'No response text')}\n")
        
        # Print the Sources (this proves RAG is working)
        sources = data.get('sources', [])
        if sources:
            print("📚 Sources Used:")
            for i, source in enumerate(sources, 1):
                title = source.get('title', 'Unknown')
                snippet = source.get('snippet', '').replace('\n', ' ')[:150] + "..."
                print(f"  {i}. {title}")
                print(f"     '{snippet}'")
        else:
            print("⚠️ No sources cited (Fallback mode might be active)")
            
        # Print metadata
        print(f"\n⚙️  Mode: {data.get('mode', 'unknown')}")
        print(f"🤖 Model: {data.get('model_used', 'unknown')}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {HELP_ENDPOINT}")
        print("   Make sure Firebase Emulators are running: 'firebase emulators:start'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # Default test query that relies on specific knowledge in your user guide
        query = "how do I load a reverb preset?"
        
    test_rag_query(query)
