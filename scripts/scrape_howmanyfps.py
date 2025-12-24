#!/usr/bin/env python3
"""
Scraper for HowManyFPS GPU benchmark data
Extracts GPU models and their FPS scores from howmanyfps.com
"""

import requests
from bs4 import BeautifulSoup
import json
import re


def scrape_howmanyfps():
    """Scrape GPU benchmark data from HowManyFPS"""

    url = "https://howmanyfps.com/graphics-cards"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        print("Response:", response.text[:500])
        return None

    print("Parsing HTML...")
    soup = BeautifulSoup(response.text, 'html.parser')

    # Save HTML for debugging
    with open('/tmp/howmanyfps_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Saved debug HTML to /tmp/howmanyfps_debug.html")

    # Try to find GPU data in various formats
    benchmarks = {}

    # Method 1: Look for table rows
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # Extract GPU model and FPS
                model_cell = cells[0].get_text(strip=True)
                fps_cell = cells[1].get_text(strip=True)

                # Clean up model name (remove extra whitespace, icons, etc.)
                model = re.sub(r'\s+', ' ', model_cell).strip()

                # Extract FPS number
                fps_match = re.search(r'(\d+(?:\.\d+)?)', fps_cell)
                if fps_match and model:
                    fps = float(fps_match.group(1))
                    if fps > 10:  # Sanity check - FPS should be reasonable
                        benchmarks[model] = fps
                        print(f"  Found: {model} = {fps} FPS")

    # Method 2: Look for JSON data in script tags
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('gpu' in script.string.lower() or 'graphics' in script.string.lower()):
            # Try to extract JSON data
            json_match = re.search(r'\{[^}]*".*?":\s*\d+[^}]*\}', script.string)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    print(f"Found JSON data: {data}")
                except:
                    pass

    if not benchmarks:
        print("\nNo benchmarks found. Check /tmp/howmanyfps_debug.html for page structure.")
        print("\nYou may need to:")
        print("1. Open the HTML file and find the GPU table structure")
        print("2. Update this script with the correct CSS selectors")
        print("3. Or manually copy the data from the website")
        return None

    print(f"\nExtracted {len(benchmarks)} GPU benchmarks")
    return benchmarks


def format_for_python(benchmarks):
    """Format benchmarks as Python dictionary for scraper.py"""

    print("\n" + "="*80)
    print("SAMPLE_BENCHMARKS = {")

    # Group by manufacturer/series for better organization
    nvidia_rtx_50 = {k: v for k, v in benchmarks.items() if 'RTX 50' in k or 'RTX 51' in k}
    nvidia_rtx_40 = {k: v for k, v in benchmarks.items() if 'RTX 40' in k or 'RTX 41' in k}
    nvidia_rtx_30 = {k: v for k, v in benchmarks.items() if 'RTX 30' in k or 'RTX 31' in k}
    nvidia_rtx_20 = {k: v for k, v in benchmarks.items() if 'RTX 20' in k or 'RTX 21' in k}
    nvidia_gtx = {k: v for k, v in benchmarks.items() if 'GTX' in k}
    amd_rx_9000 = {k: v for k, v in benchmarks.items() if 'RX 9' in k or 'RX 90' in k}
    amd_rx_7000 = {k: v for k, v in benchmarks.items() if 'RX 7' in k or 'RX 70' in k or 'RX 71' in k or 'RX 72' in k or 'RX 73' in k or 'RX 74' in k or 'RX 75' in k or 'RX 76' in k or 'RX 77' in k or 'RX 78' in k or 'RX 79' in k}
    amd_rx_6000 = {k: v for k, v in benchmarks.items() if 'RX 6' in k}
    amd_other = {k: v for k, v in benchmarks.items() if 'RX 5' in k or 'VEGA' in k or 'RADEON' in k}
    intel_arc = {k: v for k, v in benchmarks.items() if 'ARC' in k.upper() or 'INTEL' in k.upper()}

    groups = [
        ("NVIDIA RTX 50-series", nvidia_rtx_50),
        ("NVIDIA RTX 40-series", nvidia_rtx_40),
        ("NVIDIA RTX 30-series", nvidia_rtx_30),
        ("NVIDIA RTX 20-series", nvidia_rtx_20),
        ("NVIDIA GTX series", nvidia_gtx),
        ("AMD RX 9000-series", amd_rx_9000),
        ("AMD RX 7000-series", amd_rx_7000),
        ("AMD RX 6000-series", amd_rx_6000),
        ("AMD other", amd_other),
        ("Intel Arc", intel_arc),
    ]

    for group_name, group_data in groups:
        if group_data:
            print(f"    # {group_name}")
            for model, fps in sorted(group_data.items()):
                print(f'    "{model}": {fps},')
            print()

    print("}")
    print("="*80)


if __name__ == "__main__":
    print("HowManyFPS GPU Benchmark Scraper")
    print("="*80)

    benchmarks = scrape_howmanyfps()

    if benchmarks:
        format_for_python(benchmarks)

        # Save to JSON file
        output_file = "/tmp/howmanyfps_benchmarks.json"
        with open(output_file, 'w') as f:
            json.dump(benchmarks, f, indent=2, sort_keys=True)
        print(f"\nSaved benchmarks to {output_file}")
    else:
        print("\nFailed to scrape benchmarks. See debug output above.")
