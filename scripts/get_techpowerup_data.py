#!/usr/bin/env python3
"""
Get GPU performance data from TechPowerUp GPU Database
They have relative performance scores which are very reliable
"""
import requests
from bs4 import BeautifulSoup
import json

# Sample GPU list to test
SAMPLE_GPUS = {
    "RTX 5090": "https://www.techpowerup.com/gpu-specs/geforce-rtx-5090.c4256",
    "RTX 4090": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4090.c3889",
    "RTX 4080": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4080.c3888",
    "RX 7900 XTX": "https://www.techpowerup.com/gpu-specs/radeon-rx-7900-xtx.c3941",
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("="*80)
print("🔍 TESTING TECHPOWERUP GPU DATABASE ACCESS")
print("="*80)

for gpu_name, url in SAMPLE_GPUS.items():
    print(f"\n📊 Testing: {gpu_name}")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"   ✅ Status: {response.status_code}")

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for performance score
            # TechPowerUp shows "Performance" or "Relative Performance"
            perf_section = soup.find('dt', string='Performance')
            if perf_section:
                perf_value = perf_section.find_next('dd')
                if perf_value:
                    print(f"   📈 Performance: {perf_value.text.strip()}")

            # Look for other useful data
            specs = {}
            for dt in soup.find_all('dt'):
                dd = dt.find_next('dd')
                if dd:
                    key = dt.text.strip()
                    value = dd.text.strip()
                    if key in ['GPU Chip', 'Architecture', 'CUDA Cores', 'Memory Size', 'TDP']:
                        specs[key] = value

            print(f"   📋 Specs found: {len(specs)}")
            for key, value in specs.items():
                print(f"      - {key}: {value}")

        else:
            print(f"   ❌ Status: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

print("="*80)
print("💡 TechPowerUp provides GPU specs but not direct FPS numbers")
print("   However, they have relative performance scores we could use")
print("="*80)
