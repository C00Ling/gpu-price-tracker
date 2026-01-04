#!/usr/bin/env python
"""
Simple test script to run the scraping pipeline locally
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables before importing
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/gpu_tracker')
os.environ.setdefault('ENVIRONMENT', 'development')

from services.shared.ingest.pipeline import run_pipeline

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Running Pipeline Test")
    print("=" * 70)

    try:
        success = run_pipeline(ws_manager=None)

        if success:
            print("\n✅ Pipeline completed successfully!")
            print("📊 Check rejected listings at http://localhost:8000/api/rejected/")
            sys.exit(0)
        else:
            print("\n⚠️  Pipeline completed with warnings")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
