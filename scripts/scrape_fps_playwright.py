#!/usr/bin/env python3
"""
HowManyFPS Scraper using Playwright
Much better at bypassing Cloudflare than Selenium
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

import time
import re
from playwright.sync_api import sync_playwright


def scrape_gpu_fps_playwright(gpu_slug: str, gpu_name: str, page):
    """Scrape AVG FPS for a GPU using Playwright"""

    url = f"https://howmanyfps.com/graphics-cards/{gpu_slug}"

    print(f"\n🎯 Scraping {gpu_name} ({gpu_slug})...")

    try:
        # Navigate to page
        print(f"   📥 Loading {url}...")
        page.goto(url, wait_until="networkidle", timeout=60000)

        # Wait a bit more for JavaScript to execute
        print("   ⏳ Waiting for content to render...")
        time.sleep(5)

        # Check if we passed Cloudflare
        title = page.title()
        if "Just a moment" in title:
            print("   ⚠️  Cloudflare challenge detected, waiting longer...")
            time.sleep(10)

        # Get page content
        content = page.content()
        page_text = page.inner_text("body")

        # Debug: Check what we got
        if "Cloudflare" in content[:1000]:
            print("   ❌ Still blocked by Cloudflare")
            # Save debug HTML
            with open(f'/tmp/playwright_debug_{gpu_slug}.html', 'w') as f:
                f.write(content)
            return None

        print("   ✅ Page loaded!")

        # Try to find AVG FPS
        # Pattern 1: "120 AVG FPS"
        fps_match = re.search(r'(\d{2,3})\s*AVG\s*FPS', page_text, re.IGNORECASE)

        if fps_match:
            fps = int(fps_match.group(1))
            print(f"   ✅ Found: {fps} AVG FPS")
            return float(fps)

        # Pattern 2: Look for the FPS value in a specific element
        # From your screenshot, I see the FPS is in elements with specific classes
        try:
            # Try to find elements that might contain FPS
            fps_elements = page.query_selector_all('text=/\\d{2,3}\\s*AVG\\s*FPS/i')
            if fps_elements:
                fps_text = fps_elements[0].inner_text()
                fps_match = re.search(r'(\d{2,3})', fps_text)
                if fps_match:
                    fps = int(fps_match.group(1))
                    print(f"   ✅ Found in element: {fps} FPS")
                    return float(fps)
        except Exception as e:
            print(f"   ⚠️  Element search failed: {e}")

        # Pattern 3: Alternative text search
        avg_match = re.search(r'Average[:\s]+(\d{1,3})', page_text, re.IGNORECASE)
        if avg_match:
            fps = int(avg_match.group(1))
            print(f"   ✅ Found from Average: {fps} FPS")
            return float(fps)

        print("   ⚠️  No FPS data found")

        # Save debug text
        with open(f'/tmp/playwright_debug_{gpu_slug}.txt', 'w') as f:
            f.write(page_text[:5000])

        return None

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING PLAYWRIGHT SCRAPER WITH 3 GPUs")
    print("="*80)

    # Test GPUs
    TEST_GPUS = {
        "geforce-rtx-4090": "RTX 4090",
        "geforce-rtx-4070": "RTX 4070",
        "radeon-rx-7900-xtx": "RX 7900 XTX",
    }

    results = {}

    with sync_playwright() as p:
        print("\n🌐 Launching Chromium...")

        # Launch browser with stealth settings
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Create context with realistic settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )

        page = context.new_page()

        print("✅ Browser ready!\n")

        try:
            for idx, (slug, name) in enumerate(TEST_GPUS.items(), 1):
                print(f"\n[{idx}/{len(TEST_GPUS)}]", end=" ")

                fps = scrape_gpu_fps_playwright(slug, name, page)

                if fps:
                    results[name] = fps

                # Delay between requests
                if idx < len(TEST_GPUS):
                    print("   💤 Waiting 3 seconds...")
                    time.sleep(3)

        finally:
            print("\n\n🛑 Closing browser...")
            browser.close()

    print("\n" + "="*80)
    print("✅ TEST RESULTS")
    print("="*80)

    if results:
        for gpu, fps in results.items():
            print(f"  {gpu}: {fps} FPS")
        print(f"\n📊 Successfully scraped: {len(results)}/{len(TEST_GPUS)} GPUs")
    else:
        print("  ❌ No data collected")
        print("\n💡 Debug files saved to /tmp/playwright_debug_*")

    print("="*80)
