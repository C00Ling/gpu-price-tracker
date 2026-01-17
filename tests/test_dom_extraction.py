#!/usr/bin/env python3
"""
Test extracting FPS from the DOM directly
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

import time
from scripts.scrape_real_fps import create_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://howmanyfps.com/graphics-cards/geforce-rtx-4090/cyberpunk-2077"

print(f"🔍 Testing DOM extraction")
print(f"📊 URL: {URL}\n")

# Create driver
print("🌐 Starting Firefox...")
driver = create_driver()

try:
    # Load page
    print("📥 Loading page...")
    driver.get(URL)

    # Wait longer for page to load
    print("⏳ Waiting 10 seconds for full page load...")
    time.sleep(10)

    # Try to find FPS value in the page
    print("\n" + "="*80)
    print("SEARCHING FOR FPS IN DOM")
    print("="*80)

    # Strategy 1: Find any element containing FPS number
    try:
        # Look for common patterns
        selectors_to_try = [
            "//div[contains(@class, 'fps')]",
            "//span[contains(@class, 'fps')]",
            "//div[contains(text(), 'FPS')]",
            "//span[contains(text(), 'FPS')]",
            "//*[contains(@class, 'average')]",
            "//*[contains(@class, 'benchmark')]",
            "//*[contains(@class, 'rating')]",
            "//h1",
            "//h2",
            "//h3"
        ]

        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"\n✅ Found {len(elements)} elements with selector: {selector}")
                    for i, elem in enumerate(elements[:5]):  # First 5
                        text = elem.text.strip()
                        if text and len(text) < 200:  # Skip huge blocks
                            print(f"   [{i}] {text[:100]}")
            except:
                pass

    except Exception as e:
        print(f"❌ Error searching DOM: {e}")

    # Strategy 2: Get page text and search for numbers
    print("\n" + "="*80)
    print("PAGE TEXT SEARCH")
    print("="*80)

    page_text = driver.find_element(By.TAG_NAME, "body").text

    # Search for FPS patterns
    import re
    fps_patterns = [
        r'(\d{1,3})\s*(?:fps|FPS)',
        r'Average[:\s]+(\d{1,3})',
        r'(\d{1,3})\s*frames',
    ]

    for pattern in fps_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            print(f"\n✅ Pattern '{pattern}' found {len(matches)} matches:")
            print(f"   {matches[:10]}")

    # Strategy 3: Save screenshot
    screenshot_path = "/tmp/howmanyfps_screenshot.png"
    driver.save_screenshot(screenshot_path)
    print(f"\n📸 Screenshot saved to: {screenshot_path}")

    # Strategy 4: Save full HTML
    html_path = "/tmp/howmanyfps_full.html"
    with open(html_path, 'w') as f:
        f.write(driver.page_source)
    print(f"💾 Full HTML saved to: {html_path}")

finally:
    print("\n🛑 Closing browser...")
    driver.quit()
    print("✅ Done!")
