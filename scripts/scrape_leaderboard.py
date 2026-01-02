#!/usr/bin/env python3
"""
Scrape the HowManyFPS leaderboard page directly
This page shows all GPUs with their AVG FPS at once
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

import time
import re
from playwright.sync_api import sync_playwright


def scrape_leaderboard():
    """Scrape FPS data from the main leaderboard page"""

    # The leaderboard URL (from your screenshot)
    url = "https://howmanyfps.com/graphics-cards"

    results = {}

    with sync_playwright() as p:
        print("="*80)
        print("🎮 SCRAPING HOWMANYFPS LEADERBOARD")
        print("="*80)
        print(f"\n📊 URL: {url}\n")

        print("🌐 Launching Chromium...")

        browser = p.chromium.launch(
            headless=False,  # Non-headless might help with Cloudflare
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        page = context.new_page()

        try:
            print("📥 Loading leaderboard page...")

            # Use simpler wait strategy
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for Cloudflare
            print("⏳ Waiting for Cloudflare to resolve...")
            time.sleep(15)

            # Check page title
            title = page.title()
            print(f"📄 Page title: {title}")

            if "Just a moment" in title:
                print("⚠️  Cloudflare is still checking, waiting longer...")
                time.sleep(20)

            # Get page content
            page_text = page.inner_text("body")

            # Save full text for debugging
            with open('/tmp/leaderboard_text.txt', 'w') as f:
                f.write(page_text)
            print("📝 Saved page text to /tmp/leaderboard_text.txt")

            # Save HTML
            with open('/tmp/leaderboard.html', 'w') as f:
                f.write(page.content())
            print("📝 Saved HTML to /tmp/leaderboard.html")

            # Take screenshot
            page.screenshot(path='/tmp/leaderboard_screenshot.png', full_page=True)
            print("📸 Saved screenshot to /tmp/leaderboard_screenshot.png")

            # Try to find GPU + FPS pairs
            # Pattern: GPU name followed by FPS
            # Example from screenshot: "RX 9070 XT" then "120 AVG FPS"

            print("\n" + "="*80)
            print("SEARCHING FOR GPU DATA")
            print("="*80)

            # Look for pattern: GPU name ... XXX AVG FPS
            gpu_fps_pattern = r'((?:RTX|RX|GTX|ARC)\s+[\w\s]+?)\s*.*?(\d{2,3})\s*AVG\s*FPS'
            matches = re.findall(gpu_fps_pattern, page_text, re.IGNORECASE | re.DOTALL)

            if matches:
                print(f"\n✅ Found {len(matches)} GPU entries:\n")
                for gpu_name, fps in matches[:20]:  # First 20
                    gpu_clean = ' '.join(gpu_name.split())  # Clean whitespace
                    fps_value = int(fps)
                    results[gpu_clean] = float(fps_value)
                    print(f"  {gpu_clean}: {fps_value} FPS")
            else:
                print("\n⚠️  No GPU data found with pattern matching")

                # Alternative: Look for any AVG FPS mentions
                fps_mentions = re.findall(r'(\d{2,3})\s*AVG\s*FPS', page_text, re.IGNORECASE)
                if fps_mentions:
                    print(f"\n📊 Found {len(fps_mentions)} FPS values: {fps_mentions[:10]}")
                else:
                    print("\n❌ No FPS data found at all")

        except Exception as e:
            print(f"\n❌ Error: {e}")

        finally:
            input("\n⏸️  Press Enter to close browser...")
            browser.close()

    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    if results:
        print(f"\n✅ Successfully scraped {len(results)} GPUs\n")
        for gpu, fps in sorted(results.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {gpu}: {fps} FPS")
    else:
        print("\n❌ No data collected")
        print("💡 Check debug files in /tmp/")

    return results


if __name__ == "__main__":
    scrape_leaderboard()
