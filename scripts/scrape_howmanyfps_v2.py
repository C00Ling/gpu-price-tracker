#!/usr/bin/env python3
"""
Improved scraper for HowManyFPS GPU benchmark data
Extracts fpsScore from __NEXT_DATA__ JSON
"""

import requests
import json
import re
from typing import Dict, Optional


def scrape_howmanyfps() -> Optional[Dict[str, float]]:
    """
    Scrape GPU benchmark data (fpsScore) from HowManyFPS

    Returns:
        Dict mapping GPU model names to fpsScore values
        Example: {"RTX 4090": 27799, "RX 7900 XTX": 22673, ...}
    """

    benchmarks = {}
    page = 1
    max_pages = 50  # Safety limit

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
    }

    while page <= max_pages:
        url = f"https://howmanyfps.com/graphics-cards?page={page}" if page > 1 else "https://howmanyfps.com/graphics-cards"

        print(f"\nFetching page {page}: {url}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        print("Parsing HTML...")
        html = response.text

        # Extract __NEXT_DATA__ JSON
        next_data_match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html,
            re.DOTALL
        )

        if not next_data_match:
            print(f"ERROR: Could not find __NEXT_DATA__ on page {page}")
            break

        try:
            next_data = json.loads(next_data_match.group(1))
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse __NEXT_DATA__ JSON on page {page}: {e}")
            break

        # Navigate to GPU data
        try:
            page_props = next_data.get('props', {}).get('pageProps', {})
            app_ssr = page_props.get('appSsrProps', {})
            query_state = app_ssr.get('queryClientState', {})
            queries = query_state.get('queries', [])

            if not queries:
                print(f"No queries found on page {page}")
                break

            # Find the GPU query
            found_gpus = False
            for query in queries:
                query_key = query.get('queryKey', [])
                state = query.get('state', {})
                data = state.get('data', {})

                # Check if this is the GPUs query
                if isinstance(query_key, list) and len(query_key) > 0:
                    first_key = query_key[0]
                    if isinstance(first_key, list) and len(first_key) > 0 and first_key[0] == 'gpus':
                        # Data structure: {data: [...], itemsPerPage, itemsCount, pageCount}
                        gpu_list = data.get('data', [])
                        total_pages = data.get('pageCount', 1)
                        total_count = data.get('itemsCount', 0)

                        if not gpu_list:
                            print(f"GPU list is empty on page {page}, stopping")
                            found_gpus = True
                            page = max_pages + 1  # Stop loop
                            break

                        print(f"Page {page}/{total_pages}: Extracting {len(gpu_list)} GPUs (Total: {total_count})")

                        for gpu in gpu_list:
                            if isinstance(gpu, dict):
                                name = gpu.get('shortName') or gpu.get('model')
                                fps_score = gpu.get('fpsScore')

                                if name and fps_score:
                                    clean_name = normalize_gpu_name(name)
                                    benchmarks[clean_name] = float(fps_score)
                                    print(f"  {clean_name}: {fps_score}")

                        found_gpus = True

                        # Check if we're done
                        if page >= total_pages:
                            print(f"\n✅ Reached last page ({total_pages})")
                            page = max_pages + 1  # Stop loop
                        else:
                            page += 1

                        break

            if not found_gpus:
                print(f"No GPU data found on page {page}, stopping")
                break

        except Exception as e:
            print(f"ERROR parsing GPU data on page {page}: {e}")
            import traceback
            traceback.print_exc()
            break

        # Small delay between pages to be polite
        if page <= max_pages:
            import time
            time.sleep(1)

    if not benchmarks:
        print("\n❌ No benchmarks found!")
        return None

    print(f"\n✅ Extracted {len(benchmarks)} total GPU benchmarks")
    return benchmarks


def normalize_gpu_name(name: str) -> str:
    """
    Normalize GPU name to match our existing format

    Examples:
        "NVIDIA GeForce RTX 4090" -> "RTX 4090"
        "AMD Radeon RX 7900 XTX" -> "RX 7900 XTX"
        "Intel Arc A770" -> "ARC A770"
    """
    # Remove prefixes
    name = name.replace('NVIDIA GeForce ', '')
    name = name.replace('AMD Radeon ', '')
    name = name.replace('Intel ', '')
    name = name.replace('Arc ', 'ARC ')

    # Normalize spacing
    name = ' '.join(name.split())

    return name.upper()


def format_for_python(benchmarks: Dict[str, float]):
    """Format benchmarks as Python dictionary for scraper.py"""

    print("\n" + "="*80)
    print("# Paste this into services/shared/ingest/scraper.py")
    print("="*80)
    print("\nSAMPLE_BENCHMARKS = {")

    # Group by manufacturer/series
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
    print("HowManyFPS GPU Benchmark Scraper v2")
    print("="*80)

    benchmarks = scrape_howmanyfps()

    if benchmarks:
        format_for_python(benchmarks)

        # Save to JSON
        output_file = "/tmp/howmanyfps_benchmarks_v2.json"
        with open(output_file, 'w') as f:
            json.dump(benchmarks, f, indent=2, sort_keys=True)
        print(f"\n✅ Saved {len(benchmarks)} benchmarks to {output_file}")
    else:
        print("\n❌ Failed to scrape benchmarks")
        print("\nTroubleshooting:")
        print("1. Check /tmp/howmanyfps_nextdata.json to see the page structure")
        print("2. Website structure may have changed - update scraper logic")
