import os
import requests
import json

url = "https://eiendom-search.search.windows.net/indexes/knowledge-index/docs/search?api-version=2021-04-30-Preview"
headers = {
    "Content-Type": "application/json",
    "api-key": os.environ.get("AZURE_SEARCH_API_KEY", "")
}

payload = {
    "search": "*",
    "select": "id,source_file",
    "top": 5
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

print(f"\n=== Sample Documents in knowledge-index ===")
print(f"Total: {data.get('@odata.count', 'N/A')}")
print(f"\nFirst 5 documents:")
for i, doc in enumerate(data.get('value', [])[:5]):
    print(f"\n{i+1}. ID: {doc.get('id', 'N/A')[:50]}...")
    print(f"   Source: {doc.get('source_file', 'N/A')}")

# Check if embeddings exist
print(f"\n=== Checking for Embeddings ===")
payload2 = {
    "search": "*",
    "select": "id,embedding",
    "top": 1
}
response2 = requests.post(url, headers=headers, json=payload2)
data2 = response2.json()
if data2.get('value'):
    doc = data2['value'][0]
    has_embedding = doc.get('embedding') is not None
    if has_embedding:
        print(f"✅ Documents have embeddings!")
        print(f"   Example: {len(doc['embedding'])} dimensions")
    else:
        print(f"❌ Documents do NOT have embeddings")
