#!/usr/bin/env python3
"""
HowManyFPS Scraper with Undetected ChromeDriver
Bypasses Cloudflare bot detection
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_undetected_driver():
    """Create undetected Chrome driver that bypasses Cloudflare"""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = uc.Chrome(options=options, version_main=None)
    return driver


def scrape_gpu_fps_undetected(gpu_slug: str, gpu_name: str, driver):
    """Scrape FPS for a single GPU using undetected ChromeDriver"""

    # Use the leaderboard page which shows AVG FPS
    url = f"https://howmanyfps.com/graphics-cards/{gpu_slug}"

    print(f"\n🎯 Scraping {gpu_name} ({gpu_slug})...")
    print(f"   URL: {url}")

    try:
        # Load page
        driver.get(url)

        # Wait for Cloudflare to resolve (usually 5-10 seconds)
        print("   ⏳ Waiting for page to load...")
        time.sleep(10)

        # Check if we got past Cloudflare
        page_source = driver.page_source

        if "Just a moment" in page_source or "Cloudflare" in driver.title:
            print("   ⚠️  Still blocked by Cloudflare")
            return None

        print("   ✅ Page loaded successfully!")

        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Try to find AVG FPS in the page
        # Pattern: "120 AVG FPS" or similar
        fps_match = re.search(r'(\d{2,3})\s*AVG\s*FPS', page_text, re.IGNORECASE)

        if fps_match:
            fps = int(fps_match.group(1))
            print(f"   ✅ Found: {fps} AVG FPS")
            return float(fps)
        else:
            # Alternative patterns
            avg_match = re.search(r'Average[:\s]+(\d{1,3})', page_text, re.IGNORECASE)
            if avg_match:
                fps = int(avg_match.group(1))
                print(f"   ✅ Found: {fps} FPS (from Average)")
                return float(fps)

            print("   ⚠️  No FPS data found")
            # Save debug info
            with open(f'/tmp/debug_{gpu_slug}.txt', 'w') as f:
                f.write(page_text[:2000])
            return None

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING UNDETECTED CHROMEDRIVER WITH 3 GPUs")
    print("="*80)

    # Test with 3 GPUs
    TEST_GPUS = {
        "geforce-rtx-4090": "RTX 4090",
        "geforce-rtx-4070": "RTX 4070",
        "radeon-rx-7900-xtx": "RX 7900 XTX",
    }

    print("\n🌐 Starting Undetected ChromeDriver...")
    driver = create_undetected_driver()
    print("✅ Driver ready!\n")

    results = {}

    try:
        for idx, (slug, name) in enumerate(TEST_GPUS.items(), 1):
            print(f"\n[{idx}/{len(TEST_GPUS)}]", end=" ")

            fps = scrape_gpu_fps_undetected(slug, name, driver)

            if fps:
                results[name] = fps

            # Delay between requests
            if idx < len(TEST_GPUS):
                time.sleep(3)

    finally:
        print("\n\n🛑 Closing driver...")
        driver.quit()

    print("\n" + "="*80)
    print("✅ TEST RESULTS")
    print("="*80)
    for gpu, fps in results.items():
        print(f"  {gpu}: {fps} FPS")
    print(f"\n📊 Successfully scraped: {len(results)}/{len(TEST_GPUS)} GPUs")
    print("="*80)
