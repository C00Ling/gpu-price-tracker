#!/usr/bin/env python3
"""
Real FPS Benchmark Scraper for HowManyFPS
Extracts actual average FPS across popular games instead of fpsScore
Uses Selenium for JavaScript-rendered content
"""

import json
import time
from typing import Dict, List, Optional
from statistics import mean

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import geckodriver_autoinstaller


# Target games for FPS benchmarking (10 popular titles)
TARGET_GAMES = [
    "cyberpunk-2077",
    "red-dead-redemption-2",
    "assassins-creed-valhalla",
    "call-of-duty-modern-warfare-iii",
    "fortnite",
    "counter-strike-2",
    "grand-theft-auto-v",
    "forza-horizon-5",
    "call-of-duty-warzone",
    "spider-man-remastered",
]

# GPU models to scrape (from existing SAMPLE_BENCHMARKS)
GPU_MODELS = {
    # NVIDIA RTX 50-series
    "geforce-rtx-5090": "RTX 5090",
    "geforce-rtx-5080": "RTX 5080",
    "geforce-rtx-5070-ti": "RTX 5070 TI",
    "geforce-rtx-5070": "RTX 5070",

    # NVIDIA RTX 40-series
    "geforce-rtx-4090": "RTX 4090",
    "geforce-rtx-4080-super": "RTX 4080 SUPER",
    "geforce-rtx-4080": "RTX 4080",
    "geforce-rtx-4070-ti-super": "RTX 4070 TI SUPER",
    "geforce-rtx-4070-ti": "RTX 4070 TI",
    "geforce-rtx-4070-super": "RTX 4070 SUPER",
    "geforce-rtx-4070": "RTX 4070",
    "geforce-rtx-4060-ti-8gb": "RTX 4060 TI 8 GB",
    "geforce-rtx-4060-ti-16gb": "RTX 4060 TI 16 GB",
    "geforce-rtx-4060": "RTX 4060",

    # NVIDIA RTX 30-series
    "geforce-rtx-3090-ti": "RTX 3090 TI",
    "geforce-rtx-3090": "RTX 3090",
    "geforce-rtx-3080-ti": "RTX 3080 TI",
    "geforce-rtx-3080": "RTX 3080",
    "geforce-rtx-3070-ti": "RTX 3070 TI",
    "geforce-rtx-3070": "RTX 3070",
    "geforce-rtx-3060-ti": "RTX 3060 TI",
    "geforce-rtx-3060": "RTX 3060",
    "geforce-rtx-3050": "RTX 3050",

    # NVIDIA RTX 20-series
    "geforce-rtx-2080-ti": "RTX 2080 TI",
    "geforce-rtx-2080-super": "RTX 2080 SUPER",
    "geforce-rtx-2080": "RTX 2080",
    "geforce-rtx-2070-super": "RTX 2070 SUPER",
    "geforce-rtx-2070": "RTX 2070",
    "geforce-rtx-2060-super": "RTX 2060 SUPER",
    "geforce-rtx-2060": "RTX 2060",

    # NVIDIA GTX series
    "geforce-gtx-1660-ti": "GTX 1660 TI",
    "geforce-gtx-1660-super": "GTX 1660 SUPER",
    "geforce-gtx-1660": "GTX 1660",
    "geforce-gtx-1650-super": "GTX 1650 SUPER",
    "geforce-gtx-1080-ti": "GTX 1080 TI",
    "geforce-gtx-1080": "GTX 1080",
    "geforce-gtx-1070-ti": "GTX 1070 TI",
    "geforce-gtx-1070": "GTX 1070",

    # AMD RX 7000-series
    "radeon-rx-7900-xtx": "RX 7900 XTX",
    "radeon-rx-7900-xt": "RX 7900 XT",
    "radeon-rx-7900-gre": "RX 7900 GRE",
    "radeon-rx-7800-xt": "RX 7800 XT",
    "radeon-rx-7700-xt": "RX 7700 XT",
    "radeon-rx-7600-xt": "RX 7600 XT",
    "radeon-rx-7600": "RX 7600",

    # AMD RX 6000-series
    "radeon-rx-6950-xt": "RX 6950 XT",
    "radeon-rx-6900-xt": "RX 6900 XT",
    "radeon-rx-6800-xt": "RX 6800 XT",
    "radeon-rx-6800": "RX 6800",
    "radeon-rx-6750-xt": "RX 6750 XT",
    "radeon-rx-6700-xt": "RX 6700 XT",
    "radeon-rx-6650-xt": "RX 6650 XT",
    "radeon-rx-6600-xt": "RX 6600 XT",
    "radeon-rx-6600": "RX 6600",
    "radeon-rx-6500-xt": "RX 6500 XT",

    # AMD RX 5000-series
    "radeon-rx-5700-xt": "RX 5700 XT",
    "radeon-rx-5700": "RX 5700",
    "radeon-rx-5600-xt": "RX 5600 XT",
    "radeon-rx-5500-xt": "RX 5500 XT",

    # Intel Arc
    "arc-b580": "ARC B580",
    "arc-a770": "ARC A770",
    "arc-a750": "ARC A750",
    "arc-a580": "ARC A580",
}


def create_driver():
    """Create headless Firefox driver with Selenium"""
    # Install geckodriver if not present
    geckodriver_autoinstaller.install()

    firefox_options = Options()
    firefox_options.add_argument('--headless')
    firefox_options.add_argument('--width=1920')
    firefox_options.add_argument('--height=1080')

    # Set user agent
    firefox_options.set_preference('general.useragent.override',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0')

    driver = webdriver.Firefox(options=firefox_options)
    return driver


def scrape_gpu_fps(gpu_slug: str, gpu_name: str, driver) -> Optional[float]:
    """
    Scrape average FPS for a GPU across target games using Selenium

    Args:
        gpu_slug: HowManyFPS URL slug (e.g., "geforce-rtx-4090")
        gpu_name: Display name (e.g., "RTX 4090")
        driver: Selenium WebDriver instance

    Returns:
        Average FPS @ 1080p Ultra, or None if failed
    """
    import re
    from selenium.webdriver.common.by import By

    fps_values = []

    print(f"\n🎯 Scraping {gpu_name} ({gpu_slug})...")

    for game in TARGET_GAMES:
        url = f"https://howmanyfps.com/graphics-cards/{gpu_slug}/{game}"

        try:
            print(f"  📊 {game}...", end=" ", flush=True)

            # Load page with Selenium
            driver.get(url)

            # Wait longer for JavaScript to render FPS data
            time.sleep(5)

            # Get page text
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Try to find "Average: XX" pattern first (most reliable)
            average_match = re.search(r'Average[:\s]+(\d{1,3})', page_text, re.IGNORECASE)

            if average_match:
                fps = int(average_match.group(1))
                fps_values.append(float(fps))
                print(f"✅ {fps} FPS")
            else:
                # Fallback: Look for "XXX AVG FPS" pattern
                avg_fps_match = re.search(r'(\d{2,3})\s*AVG\s*FPS', page_text, re.IGNORECASE)
                if avg_fps_match:
                    fps = int(avg_fps_match.group(1))
                    fps_values.append(float(fps))
                    print(f"✅ {fps} FPS")
                else:
                    print("⚠️  No FPS found")

            # Small delay to be polite
            time.sleep(2)

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    if fps_values:
        avg_fps = round(mean(fps_values), 1)
        print(f"  ✅ Average FPS: {avg_fps} ({len(fps_values)}/{len(TARGET_GAMES)} games)")
        return avg_fps
    else:
        print(f"  ❌ No FPS data found for {gpu_name}")
        return None


def scrape_all_gpus() -> Dict[str, float]:
    """Scrape FPS data for all GPUs using Selenium"""
    benchmarks = {}
    total = len(GPU_MODELS)

    print(f"\n{'='*80}")
    print(f"🚀 REAL FPS BENCHMARK SCRAPER (Selenium)")
    print(f"{'='*80}")
    print(f"📊 Target games: {len(TARGET_GAMES)}")
    print(f"🎮 Resolution: 1080p Ultra")
    print(f"🎯 GPUs to scrape: {total}")
    print(f"{'='*80}\n")

    # Create Selenium driver once for all scraping
    print("🌐 Starting Chrome WebDriver...")
    driver = create_driver()
    print("✅ WebDriver ready!\n")

    try:
        for idx, (slug, name) in enumerate(GPU_MODELS.items(), 1):
            print(f"[{idx}/{total}] ", end="")

            avg_fps = scrape_gpu_fps(slug, name, driver)

            if avg_fps:
                benchmarks[name] = avg_fps

            # Delay between GPUs
            if idx < total:
                time.sleep(2)

    finally:
        # Always close the driver
        print("\n🛑 Closing WebDriver...")
        driver.quit()

    print(f"\n{'='*80}")
    print(f"✅ Scraping complete!")
    print(f"📊 Successfully scraped: {len(benchmarks)}/{total} GPUs")
    print(f"{'='*80}\n")

    return benchmarks


def format_for_python(benchmarks: Dict[str, float]):
    """Format benchmarks as Python dictionary for scraper.py"""

    print("\n" + "="*80)
    print("# Paste this into services/shared/ingest/scraper.py")
    print("="*80)
    print("\n# GPU Benchmark Data - Real average FPS @ 1080p Ultra")
    print(f"# Source: HowManyFPS.com (scraped {time.strftime('%Y-%m-%d')})")
    print(f"# Games tested: {', '.join(TARGET_GAMES)}")
    print("# Note: These are REAL average FPS values, not composite scores")
    print("\nSAMPLE_BENCHMARKS = {")

    # Group by series
    nvidia_rtx_50 = {k: v for k, v in benchmarks.items() if 'RTX 50' in k or 'RTX 51' in k}
    nvidia_rtx_40 = {k: v for k, v in benchmarks.items() if 'RTX 40' in k or 'RTX 41' in k}
    nvidia_rtx_30 = {k: v for k, v in benchmarks.items() if 'RTX 30' in k or 'RTX 31' in k}
    nvidia_rtx_20 = {k: v for k, v in benchmarks.items() if 'RTX 20' in k or 'RTX 21' in k}
    nvidia_gtx = {k: v for k, v in benchmarks.items() if 'GTX' in k}
    amd_rx_7000 = {k: v for k, v in benchmarks.items() if 'RX 7' in k}
    amd_rx_6000 = {k: v for k, v in benchmarks.items() if 'RX 6' in k}
    amd_rx_5000 = {k: v for k, v in benchmarks.items() if 'RX 5' in k}
    intel_arc = {k: v for k, v in benchmarks.items() if 'ARC' in k.upper()}

    groups = [
        ("NVIDIA RTX 50-series", nvidia_rtx_50),
        ("NVIDIA RTX 40-series", nvidia_rtx_40),
        ("NVIDIA RTX 30-series", nvidia_rtx_30),
        ("NVIDIA RTX 20-series", nvidia_rtx_20),
        ("NVIDIA GTX series", nvidia_gtx),
        ("AMD RX 7000-series", amd_rx_7000),
        ("AMD RX 6000-series", amd_rx_6000),
        ("AMD RX 5000-series", amd_rx_5000),
        ("Intel Arc", intel_arc),
    ]

    for group_name, group_data in groups:
        if group_data:
            print(f"    # {group_name} (1080p Ultra avg)")
            for model, fps in sorted(group_data.items(), key=lambda x: x[1], reverse=True):
                print(f'    "{model}": {fps},')
            print()

    print("}")
    print("="*80)


if __name__ == "__main__":
    # Scrape all GPUs
    benchmarks = scrape_all_gpus()

    if benchmarks:
        # Show formatted output
        format_for_python(benchmarks)

        # Save to JSON
        output_file = "/tmp/real_fps_benchmarks.json"
        with open(output_file, 'w') as f:
            json.dump(benchmarks, f, indent=2, sort_keys=True)
        print(f"\n✅ Saved {len(benchmarks)} benchmarks to {output_file}")

        # Save Python format
        python_file = "/tmp/real_fps_benchmarks.py"
        with open(python_file, 'w') as f:
            f.write(f"# GPU Benchmark Data - Real average FPS @ 1080p Ultra\n")
            f.write(f"# Source: HowManyFPS.com (scraped {time.strftime('%Y-%m-%d')})\n")
            f.write(f"# Games: {', '.join(TARGET_GAMES)}\n\n")
            f.write("SAMPLE_BENCHMARKS = {\n")
            for model, fps in sorted(benchmarks.items()):
                f.write(f'    "{model}": {fps},\n')
            f.write("}\n")
        print(f"✅ Saved Python format to {python_file}")
    else:
        print("\n❌ Failed to scrape benchmarks")
