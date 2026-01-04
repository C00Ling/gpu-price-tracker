#!/usr/bin/env python
"""
Minimal API server for testing rejected listings without database
"""
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'shared'))

# Mock config
class MockConfig:
    def get(self, key, default=None):
        return default

import core.config
core.config.config = MockConfig()

from core.cache import cache

app = FastAPI(title="GPU Price Tracker - Test API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/rejected/")
def get_rejected_listings():
    """Get all rejected listings from cache"""
    rejected = cache.get("rejected_listings")
    if rejected is None:
        return []
    return rejected

@app.get("/api/rejected/summary")
def get_rejection_summary():
    """Get summary stats by category"""
    rejected = cache.get("rejected_listings")
    if not rejected:
        return {}

    summary = {}
    for item in rejected:
        category = item.get("category", "Unknown")
        summary[category] = summary.get(category, 0) + 1

    return summary

@app.get("/health")
def health():
    """Health check"""
    cache_count = len(cache.get("rejected_listings") or [])
    return {
        "status": "ok",
        "cache_type": "file" if cache.use_file_cache else "redis",
        "rejected_count": cache_count
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Starting Test API Server")
    print("=" * 70)
    print("📊 API: http://localhost:8000/api/rejected/")
    print("📈 Summary: http://localhost:8000/api/rejected/summary")
    print("💚 Health: http://localhost:8000/health")
    print("📖 Docs: http://localhost:8000/docs")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000)
