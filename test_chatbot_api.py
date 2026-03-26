#!/usr/bin/env python
"""Test the chatbot API"""

import requests
import json

# Test query endpoint
payload = {
    'query': 'What insurance products do you offer?',
    'chatbot_id': 'phoenix_insurance_bot',
    'top_k': 4
}

print("Testing Phoenix Insurance AI Chatbot...")
print("=" * 60)

resp = requests.post('http://127.0.0.1:8000/api/query', json=payload, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    print("✅ QUERY SUCCESSFUL!")
    print(f"\n📝 Query: {data['query']}")
    print(f"📊 Found {data['total_results']} results\n")
    
    for result in data['results']:
        print(f"{result['rank']}. {result['page_title']}")
        print(f"   {result['text'][:120]}...")
        if result['source_url']:
            print(f"   🔗 {result['source_url'][:50]}...")
        print()
else:
    print(f"❌ Error {resp.status_code}: {resp.text}")

print("=" * 60)
print("✅ Server is ready to use!")
print("\nOpen your browser to: http://localhost:8000")
