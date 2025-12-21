# ingest/pipeline.py
from ingest.scraper import GPUScraper, SAMPLE_BENCHMARKS, ScraperError
from storage.db import SessionLocal, init_db
from storage.repo import GPURepository, RepositoryError
from core.logging import get_logger
from core.config import config
from collections import defaultdict
import sys

logger = get_logger("pipeline")


def run_pipeline():
    """
    Enhanced pipeline със защита от грешки и подробно логване
    """
    logger.info("="*70)
    logger.info("🚀 STARTING DATA COLLECTION PIPELINE")
    logger.info("="*70)
    
    try:
        # 1️⃣ Initialize database
        logger.info("📦 Initializing database...")
        init_db()
        logger.info("✅ Database ready")
        
        # 2️⃣ Initialize scraper
        logger.info(f"🔧 Initializing scraper (TOR: {config.scraper_use_tor})...")
        scraper = GPUScraper(use_tor=config.scraper_use_tor)
        scraper.add_benchmark_data(SAMPLE_BENCHMARKS)
        logger.info("✅ Scraper initialized")
        
        # 3️⃣ Test connection
        logger.info("🔍 Testing connection...")
        if not scraper.test_connection():
            logger.error("❌ No connection! Check if TOR is running.")
            return False
        logger.info("✅ Connection test passed")
        
        # 4️⃣ SCRAPE: Collect ALL data (without filtering)
        logger.info("\n" + "="*70)
        logger.info("🔍 SCRAPING: Collecting all data")
        logger.info("="*70)

        try:
            scraper.scrape_olx_pass(
                search_term="видео карта",
                max_pages=config.scraper_max_pages,
                apply_filters=False  # No filtering during scrape
            )
            raw_total = sum(len(v) for v in scraper.gpu_prices.values())
            logger.info(
                f"✅ Scraping complete: {len(scraper.gpu_prices)} models, "
                f"{raw_total} total listings (unfiltered)"
            )
        except ScraperError as e:
            logger.error(f"❌ Scraping failed: {e}")
            return False

        # 5️⃣ POST-PROCESSING: Filter scraped data
        logger.info("\n" + "="*70)
        logger.info("🧹 POST-PROCESSING: Filtering data")
        logger.info("="*70)

        from core.filters import filter_scraped_data

        try:
            filtered_data, filter_stats = filter_scraped_data(scraper.gpu_prices)
            filtered_total = filter_stats['total_kept']

            logger.info(f"✅ Filtering complete:")
            logger.info(f"   Total listings (raw):      {raw_total}")
            logger.info(f"   Filtered out (outliers):   {filter_stats['total_filtered']}")
            logger.info(f"   - Extremely low price:     {filter_stats['extremely_low_price']}")
            logger.info(f"   - Statistical outlier low: {filter_stats['statistical_outlier_low']}")
            logger.info(f"   - Statistical outlier high:{filter_stats['statistical_outlier_high']}")
            logger.info(f"   Kept (valid):              {filtered_total}")
            logger.info(f"   Filter rate:               {(filter_stats['total_filtered'] / raw_total * 100):.1f}%")

            # Replace raw data with filtered data
            scraper.gpu_prices = defaultdict(list, filtered_data)

        except Exception as e:
            logger.error(f"❌ Post-processing failed: {e}")
            return False

        # 6️⃣ Save to database (only filtered data)
        logger.info("\n💾 Saving to database...")

        try:
            session = SessionLocal()
            repo = GPURepository(session)

            # Clear old data
            logger.info("🗑️  Clearing old data...")
            repo.clear_listings()
            
            # Save new data using bulk insert
            listings = []
            for model, prices in scraper.gpu_prices.items():
                for price in prices:
                    listings.append({
                        'model': model,
                        'source': 'OLX',
                        'price': price
                    })
            
            total_saved = repo.add_listings_bulk(listings)
            session.close()
            
            logger.info(f"✅ Saved {total_saved} listings to database")
            
        except RepositoryError as e:
            logger.error(f"❌ Database save failed: {e}")
            return False
        
        # 8️⃣ Display statistics
        logger.info("\n" + "="*70)
        logger.info("📊 STATISTICS BY MODEL")
        logger.info("="*70)
        
        try:
            session = SessionLocal()
            repo = GPURepository(session)
            
            models = sorted(repo.get_models())
            
            if not models:
                logger.warning("⚠️  No models found in database")
            else:
                logger.info(f"{'Model':<20} | {'Count':<5} | {'Min':<8} | {'Median':<8} | {'Max':<8}")
                logger.info("-" * 70)
                
                for model in models:
                    stats = repo.get_price_stats(model)
                    if stats:
                        logger.info(
                            f"{model:<20} | "
                            f"{stats['count']:<5} | "
                            f"{stats['min']:>6.0f}лв | "
                            f"{stats['median']:>6.0f}лв | "
                            f"{stats['max']:>6.0f}лв"
                        )
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error displaying statistics: {e}")
        
        # 9️⃣ Success!
        logger.info("\n" + "="*70)
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*70)
        logger.info("")
        logger.info("🌐 Start API server with: uvicorn main:app --reload")
        logger.info("📖 API docs: http://127.0.0.1:8000/docs")
        logger.info("🎨 Dashboard: http://127.0.0.1:8000/dashboard")
        logger.info("")
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrupted by user")
        return False
        
    except Exception as e:
        logger.error(f"\n❌ PIPELINE FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)