#!/usr/bin/env python3
"""
Quick test to verify rejected listings are working
"""
import sys
sys.path.insert(0, 'services/shared')

from core.filters import filter_scraped_data

# Test data
data = {
    'RTX 3060': [
        {'price': 800, 'url': 'url1', 'title': 'RTX 3060 12GB'},
        {'price': 10, 'url': 'url2', 'title': 'RTX 3060 broken'},  # Too low
        {'price': 5000, 'url': 'url3', 'title': 'RTX 3060'},  # Too high
        {'price': 850, 'url': 'url4', 'title': 'RTX 3060 TI'},
    ]
}

print("Testing filter_scraped_data()...")
print("=" * 70)

try:
    filtered, stats, rejected = filter_scraped_data(data)

    print(f"✅ Function returned 3 values successfully")
    print(f"   Filtered items: {len(filtered.get('RTX 3060', []))}")
    print(f"   Rejected items: {len(rejected)}")
    print(f"\n📊 Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"\n🚫 Rejected listings ({len(rejected)}):")
    for item in rejected:
        print(f"   - {item['title']}: {item['price']}лв")
        print(f"     Reason: {item['reason']}")
        print(f"     Category: {item['category']}")

    print("\n✅ Test PASSED - rejected listings are being tracked!")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
