#!/usr/bin/env python3
"""
Extract ALL GPU FPS data from HowManyFPS screenshots
More thorough extraction - aim for ~200 GPU models
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

from pathlib import Path
import json

SCREENSHOTS_DIR = Path("/home/petar/Downloads/FireShot")

def main():
    print("="*80)
    print("COMPREHENSIVE FPS DATA EXTRACTION")
    print("="*80)

    screenshots = sorted(SCREENSHOTS_DIR.glob("*.png"))
    print(f"\nFound {len(screenshots)} screenshots")
    print("\nScreenshots to analyze:")
    for i, screenshot in enumerate(screenshots, 1):
        print(f"  {i}. {screenshot.name}")

    print("\n" + "="*80)
    print("Next step: Use Claude's vision to extract ALL GPUs from each screenshot")
    print("Expected: ~200 GPU models total")
    print("="*80)

if __name__ == "__main__":
    main()
