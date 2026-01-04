#!/usr/bin/env python3
"""
Test VRAM extraction from titles and descriptions
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker/services/shared')

from ingest.scraper import GPUScraper

# Test cases with different title/description combinations
test_cases = [
    {
        "title": "RTX 3060 12GB",
        "description": "",
        "expected": "RTX 3060 12GB"
    },
    {
        "title": "RTX 3060 видео карта",
        "description": "12GB VRAM GDDR6",
        "expected": "RTX 3060 12GB"
    },
    {
        "title": "ASUS RTX 5060 TI 16 GB",
        "description": "",
        "expected": "RTX 5060 TI 16GB"
    },
    {
        "title": "RX 6600 XT OC Edition",
        "description": "8GB GDDR6 памет",
        "expected": "RX 6600 XT 8GB"
    },
    {
        "title": "Видео карта RTX 4070",
        "description": "12 GB VRAM",
        "expected": "RTX 4070 12GB"
    },
    {
        "title": "RTX 3080 TI Founders Edition",
        "description": "20GB memory",
        "expected": "RTX 3080 TI 20GB"
    },
    {
        "title": "RTX 3060 TI GDDR6X",
        "description": "",
        "expected": "RTX 3060 TI"  # No VRAM in title or description
    },
    {
        "title": "GTX 1060 6GB",
        "description": "",
        "expected": "GTX 1060 6GB"
    },
    {
        "title": "RX 580 Sapphire",
        "description": "8GB GDDR5",
        "expected": "RX 580 8GB"
    },
    {
        "title": "Intel Arc B580",
        "description": "12GB VRAM",
        "expected": "ARC B580 12GB"
    },
]

def main():
    scraper = GPUScraper()

    print("=" * 80)
    print("VRAM EXTRACTION TEST")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        title = test["title"]
        description = test["description"]
        expected = test["expected"]

        # Extract GPU model with VRAM
        result = scraper.extract_gpu_model(title, description)

        # Check if it matches expected
        success = result == expected

        if success:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"

        print(f"Test {i}: {status}")
        print(f"  Title:       '{title}'")
        if description:
            print(f"  Description: '{description}'")
        print(f"  Expected:    '{expected}'")
        print(f"  Got:         '{result}'")
        print()

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

if __name__ == "__main__":
    main()
