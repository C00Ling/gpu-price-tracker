from typing import Dict, List
from ingest.scraper import GPUScraper

class OLXSource:
    """Wrapper за GPUScraper, специално за OLX"""
    
    def __init__(self, use_tor: bool = True):
        self.scraper = GPUScraper(use_tor=use_tor)
    
    def fetch(self, max_pages: int = 3) -> Dict[str, List[int]]:
        """
        Връща речник {model: [prices]}

        Uses adaptive filtering - single pass through the data
        """
        # SINGLE PASS: Събиране на данни с adaptive filtering
        self.scraper.scrape_olx_pass(max_pages=max_pages, apply_filters=True)

        return self.scraper.gpu_prices
