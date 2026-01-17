#!/usr/bin/env python3
"""
Test FPS scraper with 3 GPUs
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

from scripts.scrape_real_fps import create_driver, scrape_gpu_fps, TARGET_GAMES

# Test with 3 GPUs
TEST_GPUS = {
    "geforce-rtx-4090": "RTX 4090",
    "geforce-rtx-4070": "RTX 4070",
    "radeon-rx-7900-xtx": "RX 7900 XTX",
}

if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING FPS SCRAPER WITH 3 GPUs")
    print("="*80)
    print(f"📊 Games: {len(TARGET_GAMES)}")
    print(f"🎮 GPUs: {list(TEST_GPUS.values())}")
    print("="*80 + "\n")

    # Create driver
    print("🌐 Starting Chrome WebDriver...")
    driver = create_driver()
    print("✅ WebDriver ready!\n")

    results = {}

    try:
        for idx, (slug, name) in enumerate(TEST_GPUS.items(), 1):
            print(f"[{idx}/{len(TEST_GPUS)}] Testing {name}...")

            avg_fps = scrape_gpu_fps(slug, name, driver)

            if avg_fps:
                results[name] = avg_fps

            print()

    finally:
        print("🛑 Closing WebDriver...")
        driver.quit()

    print("\n" + "="*80)
    print("✅ TEST RESULTS")
    print("="*80)
    for gpu, fps in results.items():
        print(f"  {gpu}: {fps} FPS avg")
    print(f"\n📊 Successfully tested: {len(results)}/{len(TEST_GPUS)} GPUs")
    print("="*80)
