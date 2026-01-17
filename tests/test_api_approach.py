#!/usr/bin/env python3
"""
Test if HowManyFPS has an API we can use directly
"""
import requests
import json

# Try to find the API endpoint
# Based on the query structure, it might be something like /api/...

# From the JSON we saw query keys like:
# ["gpu-info-description", "geforce-rtx-4090", {...}]

# Let's try different API formats
base_url = "https://howmanyfps.com"

# Possible API endpoints
api_tests = [
    f"{base_url}/api/gpu-info/geforce-rtx-4090",
    f"{base_url}/api/gpus/geforce-rtx-4090",
    f"{base_url}/api/benchmarks/geforce-rtx-4090/cyberpunk-2077",
    f"{base_url}/api/fps/geforce-rtx-4090/cyberpunk-2077",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
    'Accept': 'application/json',
}

for url in api_tests:
    print(f"\n🔍 Testing: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS!")
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            print(f"   Data: {json.dumps(data, indent=2)[:500]}")
            break
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("Let me also try the trpc API format (React Query)")
print("="*80)

# HowManyFPS might use tRPC (TypeScript RPC)
# Format: /api/trpc/query?batch=1&input=...
trpc_url = f"{base_url}/api/trpc/gpuGame"
trpc_input = json.dumps({
    "gpuSlug": "geforce-rtx-4090",
    "gameSlug": "cyberpunk-2077",
    "preset": "RT Overdrive",
    "resolution": "1920 x 1080",
})

print(f"\n🔍 Testing tRPC: {trpc_url}")
try:
    response = requests.get(f"{trpc_url}?input={trpc_input}", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Data found!")
        print(f"   {response.text[:500]}")
except Exception as e:
    print(f"   ❌ Error: {e}")
