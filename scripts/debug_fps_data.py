#!/usr/bin/env python3
"""
Debug script to see what data structure HowManyFPS returns
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

import json
import re
from scripts.scrape_real_fps import create_driver

# Test one URL
URL = "https://howmanyfps.com/graphics-cards/geforce-rtx-4090/cyberpunk-2077"

print(f"🔍 Debugging HowManyFPS data structure")
print(f"📊 URL: {URL}\n")

# Create driver
print("🌐 Starting Firefox...")
driver = create_driver()

try:
    # Load page
    print("📥 Loading page...")
    driver.get(URL)

    # Wait for JS to load
    import time
    time.sleep(3)

    # Get page source
    page_source = driver.page_source

    # Extract __NEXT_DATA__
    next_data_match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        page_source,
        re.DOTALL
    )

    if next_data_match:
        print("✅ Found __NEXT_DATA__ JSON!\n")
        next_data = json.loads(next_data_match.group(1))

        # Save full JSON to file
        with open('/tmp/howmanyfps_debug.json', 'w') as f:
            json.dump(next_data, f, indent=2)
        print("📝 Saved full JSON to /tmp/howmanyfps_debug.json\n")

        # Explore structure
        print("="*80)
        print("STRUCTURE ANALYSIS")
        print("="*80)

        # Top level keys
        print(f"\nTop-level keys: {list(next_data.keys())}")

        # Check props
        if 'props' in next_data:
            props = next_data['props']
            print(f"\nprops keys: {list(props.keys())}")

            if 'pageProps' in props:
                page_props = props['pageProps']
                print(f"\npageProps keys: {list(page_props.keys())}")

                # Look for GPU/game data
                for key in page_props.keys():
                    value = page_props[key]
                    print(f"\n  pageProps['{key}'] type: {type(value).__name__}")
                    if isinstance(value, dict):
                        print(f"    Keys: {list(value.keys())[:10]}")  # First 10 keys
                        # If this looks like our data, print it
                        if 'fps' in value or 'game' in value or 'gpu' in value:
                            print(f"\n    🎯 FOUND POTENTIAL FPS DATA IN '{key}':")
                            print(f"    {json.dumps(value, indent=6)[:500]}")  # First 500 chars

    else:
        print("❌ No __NEXT_DATA__ found!")
        # Save HTML to see what we got
        with open('/tmp/howmanyfps_debug.html', 'w') as f:
            f.write(page_source)
        print("📝 Saved HTML to /tmp/howmanyfps_debug.html")

finally:
    print("\n🛑 Closing browser...")
    driver.quit()
    print("✅ Done!")
