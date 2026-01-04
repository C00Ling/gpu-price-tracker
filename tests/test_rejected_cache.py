#!/usr/bin/env python
"""
Quick test to verify rejected listings cache works with file fallback
"""
import sys
import os

# Add path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'shared'))

# Mock config for testing
class MockConfig:
    def get(self, key, default=None):
        return default

# Replace config before importing cache
import core.config
core.config.config = MockConfig()

# Now import cache
from core.cache import cache

# Create sample rejected listings
sample_rejected = [
    {
        'title': 'RTX 3060 TI 12GB Gaming',
        'price': 650.0,
        'url': 'https://olx.bg/test1',
        'model': 'RTX 3060 TI',
        'reason': "Invalid GPU model (typo): 'RTX 3060 TI 12GB' → likely 'RTX 5060 TI 16GB'",
        'category': '❌ Invalid GPU Model (Typo)'
    },
    {
        'title': 'GTX 1070 16GB Супер оферта!',
        'price': 450.0,
        'url': 'https://olx.bg/test2',
        'model': 'GTX 1070',
        'reason': 'Invalid VRAM 16 for model GTX 1070 (likely system RAM confusion)',
        'category': '💾 Invalid VRAM'
    },
    {
        'title': 'Gaming Laptop GTX 1650',
        'price': 1200.0,
        'url': 'https://olx.bg/test3',
        'model': None,
        'reason': "Blacklisted keyword: 'лаптоп'",
        'category': '💻 Full Computer/Laptop'
    },
    {
        'title': 'RTX 4090 само 200лв!!!',
        'price': 200.0,
        'url': 'https://olx.bg/test4',
        'model': 'RTX 4090',
        'reason': 'Extremely low price (likely scam)',
        'category': '💸 Extremely Low Price'
    },
]

print("=" * 70)
print("🧪 Testing Rejected Listings Cache")
print("=" * 70)

# Save to cache
print("\n📝 Saving sample rejected listings to cache...")
success = cache.set("rejected_listings", sample_rejected, ttl=86400)

if success:
    print("✅ Successfully saved to cache!")
else:
    print("❌ Failed to save to cache")
    sys.exit(1)

# Read back from cache
print("\n📖 Reading back from cache...")
retrieved = cache.get("rejected_listings")

if retrieved is None:
    print("❌ Failed to retrieve from cache")
    sys.exit(1)

print(f"✅ Retrieved {len(retrieved)} rejected listings")

# Display summary
print("\n📊 Summary by category:")
categories = {}
for item in retrieved:
    cat = item.get('category', 'Unknown')
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count}")

print("\n" + "=" * 70)
print("✅ TEST PASSED!")
print("=" * 70)
print("\n📁 Cache file location:", os.path.abspath("cache"))
print("🌐 Start API server to view at: http://localhost:8000/api/rejected/")
print()
