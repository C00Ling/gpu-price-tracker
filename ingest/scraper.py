# ingest/scraper.py
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import statistics
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from core.logging import get_logger
from core.rate_limiter import RateLimiter, retry_on_failure
from core.config import config

logger = get_logger("scraper")


class ScraperError(Exception):
    """Custom exception за scraper грешки"""
    pass


class GPUScraper:
    """Enhanced GPU scraper с TOR, филтри, rate limiting и error handling"""

    def __init__(self, use_proxy=False, proxy_list=None, use_tor=None, progress_callback=None):
        # Load from config if not specified
        self.use_tor = use_tor if use_tor is not None else config.scraper_use_tor
        self.use_proxy = use_proxy or self.use_tor
        self.proxy_list = proxy_list or []
        self.proxy_index = 0
        self.progress_callback = progress_callback

        self.tor_proxy = config.get("scraper.tor_proxy", {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        })

        self.user_agents = config.get("scraper.user_agents", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ])

        self.gpu_prices = defaultdict(list)
        self.gpu_benchmarks: Dict[str, float] = {}
        self.min_reasonable_prices = {}

        self.blacklist_keywords = config.get("scraper.blacklist_keywords", [])
        self.suspicious_price_threshold = config.get(
            "scraper.suspicious_price_threshold", 0.5
        )

        # Rate limiters
        self.request_limiter = RateLimiter(
            calls=config.rate_limit_rpm,
            period=60
        )
        self.page_limiter = RateLimiter(
            calls=1,
            period=config.rate_limit_delay
        )

        # Filter tracking
        self._filter_stats = {}
        self._filtered_count = 0

        logger.info(
            f"GPUScraper initialized (TOR: {self.use_tor}, "
            f"Rate limit: {config.rate_limit_rpm}/min)"
        )

    def _report_progress(self, progress: int, status: str, **details):
        """Report progress via callback if provided"""
        if self.progress_callback:
            try:
                self.progress_callback(progress, status, details)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    # ================= PROXY =================

    def get_proxy(self):
        if self.use_tor:
            return self.tor_proxy
        if not self.use_proxy or not self.proxy_list:
            return None
        proxy = self.proxy_list[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
        return {"http": proxy, "https": proxy}

    def renew_tor_ip(self):
        """Обновява TOR IP адреса"""
        if not self.use_tor:
            return
        try:
            from stem.control import Controller
            from stem.signal import NEWNYM  # type: ignore

            with Controller.from_port(port="9151") as c:
                c.authenticate()
                c.signal(NEWNYM)
                time.sleep(5)
                logger.info("TOR IP renewed successfully")
        except ImportError:
            logger.warning("stem library not installed, cannot renew TOR IP")
        except Exception as e:
            logger.error(f"Failed to renew TOR IP: {e}")

    def test_connection(self) -> bool:
        """Тества връзката с TOR fallback"""
        # First try with TOR if enabled
        if self.use_tor:
            try:
                logger.info("Testing connection with TOR...")
                r = requests.get(
                    "https://api.ipify.org?format=json",
                    proxies=self.get_proxy(),
                    timeout=10,
                )
                ip = r.json().get('ip', 'Unknown')
                logger.info(f"✅ TOR connection OK. Current IP: {ip}")
                return True
            except Exception as e:
                logger.warning(f"⚠️ TOR connection failed: {e}")
                logger.info("🔄 Falling back to direct connection (no TOR)...")
                self.use_tor = False
                self.use_proxy = False

        # Try without TOR (either fallback or never enabled)
        try:
            logger.info("Testing direct connection...")
            r = requests.get(
                "https://api.ipify.org?format=json",
                timeout=10,
            )
            ip = r.json().get('ip', 'Unknown')
            logger.info(f"✅ Direct connection OK. Current IP: {ip}")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed completely: {e}")
            return False

    # ================= CORE =================

    def _get_realistic_headers(self) -> dict:
        """Generate realistic browser headers to avoid detection"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "bg-BG,bg;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    @retry_on_failure(
        max_retries=3,
        delay=10,
        backoff=2.0,
        exceptions=(requests.RequestException, requests.HTTPError)
    )
    def make_request(self, url: str) -> Optional[requests.Response]:
        """Прави HTTP заявка с rate limiting и retry"""
        # Rate limiting
        self.request_limiter.wait()

        try:
            logger.debug(f"Making request to: {url}")

            r = requests.get(
                url,
                headers=self._get_realistic_headers(),
                proxies=self.get_proxy(),
                timeout=20,
                allow_redirects=True,
            )
            r.raise_for_status()

            logger.debug(f"Request successful: {url} (Status: {r.status_code})")
            return r

        except requests.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {url}")

            if e.response.status_code == 429:
                logger.warning("Rate limited by server, waiting 60s...")
                time.sleep(60)

            if e.response.status_code == 403:
                logger.warning("403 Forbidden - possible bot detection")
                if self.use_tor:
                    logger.info("Renewing TOR IP and waiting 30s...")
                    self.renew_tor_ip()
                    time.sleep(30)

            if self.use_tor and e.response.status_code in [403, 429]:
                logger.info("Renewing TOR IP...")
                self.renew_tor_ip()

            raise

        except requests.Timeout:
            logger.error(f"Request timeout: {url}")
            raise

        except requests.ConnectionError as e:
            logger.error(f"Connection error: {url} - {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during request: {e}")
            raise

    def _check_has_next_page(self, soup: BeautifulSoup) -> bool:
        """Проверява дали има следваща страница"""
        # Method 1: Check for next button with data-testid
        next_button = soup.find("a", {"data-testid": "pagination-forward"})
        if next_button:
            # Check if it's disabled
            classes = next_button.get("class")
            if classes is None:
                classes = []
            elif isinstance(classes, str):
                classes = [classes]
            if any("disabled" in str(c).lower() for c in classes):
                logger.debug("Next button is disabled")
                return False
            # Check if href is present
            if next_button.get("href"):
                logger.debug("Next button found with href")
                return True
            else:
                logger.debug("Next button found but no href")
                return False

        # Method 2: Check for any pagination link with arrow/next indicator
        pagination_links = soup.find_all("a", href=re.compile(r"\?page=\d+"))
        if pagination_links:
            # Check if any link points to a higher page number than current
            current_url = soup.find("link", {"rel": "canonical"})
            if current_url:
                current_href = current_url.get("href")
                if current_href:
                    current_page_match = re.search(r"page=(\d+)", str(current_href))
                    if current_page_match:
                        current_page = int(current_page_match.group(1))
                        for link in pagination_links:
                            link_href = link.get("href")
                            if link_href:
                                link_page_match = re.search(r"page=(\d+)", str(link_href))
                                if link_page_match:
                                    link_page = int(link_page_match.group(1))
                                    if link_page > current_page:
                                        logger.debug(f"Found link to page {link_page} > current {current_page}")
                                        return True

        # Method 3: Look for pagination text like "Страница X от Y"
        pagination_texts = soup.find_all(string=re.compile(r"[Сс]траница\s+\d+\s+от\s+\d+"))
        for text in pagination_texts:
            match = re.search(r"[Сс]траница\s+(\d+)\s+от\s+(\d+)", str(text))
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                logger.debug(f"Found pagination: page {current} of {total}")
                return current < total

        # Method 4: Check for any arrow-like next indicators
        next_indicators = soup.find_all(["a", "button"], string=re.compile(r"[→›»]|[Нн]апред|[Сс]ледваща"))
        for indicator in next_indicators:
            if indicator.get("href") or indicator.get("onclick"):
                logger.debug("Found next indicator with action")
                return True

        # Default: If we can't determine, assume no next page (conservative)
        logger.debug("No pagination indicators found, assuming last page")
        return False

    def scrape_olx_pass(
        self,
        search_term="видео карта",
        max_pages=None,
        apply_filters=False
    ) -> Dict[str, List[int]]:
        """
        Събира обяви от OLX със защита от грешки и auto-pagination

        NOTE: apply_filters parameter is DEPRECATED and ignored.
        All filtering now happens in post-processing after scraping is complete.
        """
        max_pages = max_pages or config.scraper_max_pages
        scrape_all = config.get("scraper.scrape_all_pages", False)

        logger.info(
            f"Starting OLX scrape: '{search_term}' "
            f"(max_pages: {max_pages if not scrape_all else 'ALL'})"
        )

        # Report initial progress
        self._report_progress(0, "Започване на scraping...", search_term=search_term)

        # Always scrape without filtering - post-processing will handle it
        apply_filters = False

        page = 1
        consecutive_empty_pages = 0
        max_empty_pages = 3  # Stop after 3 empty pages in a row

        while True:
            # Check if we should stop
            if not scrape_all and page > max_pages:
                logger.info(f"Reached max pages limit: {max_pages}")
                break

            if consecutive_empty_pages >= max_empty_pages:
                logger.info(f"No more results found after {max_empty_pages} empty pages. Stopping.")
                break

            try:
                # Rate limiting между страници
                if page > 1:
                    self.page_limiter.wait()

                url = f"https://www.olx.bg/ads/q-{search_term}/"
                if page > 1:
                    url += f"?page={page}"

                logger.info(f"Scraping page {page}...")

                # Report progress for current page
                progress_pct = min(int((page / max_pages) * 80), 80) if not scrape_all else min(page * 5, 80)
                self._report_progress(
                    progress_pct,
                    f"Scraping страница {page}...",
                    current_page=page,
                    total_listings=sum(len(v) for v in self.gpu_prices.values())
                )

                response = self.make_request(url)
                if not response:
                    logger.warning(f"Failed to fetch page {page}, skipping...")
                    consecutive_empty_pages += 1
                    page += 1
                    continue

                soup = BeautifulSoup(response.content, "html.parser")
                ads = soup.find_all("a", href=re.compile(r"^/d/ad/"))

                # Check if page is empty
                if len(ads) == 0:
                    consecutive_empty_pages += 1
                    logger.info(f"Page {page} is empty (attempt {consecutive_empty_pages}/{max_empty_pages})")
                    page += 1
                    continue

                # Reset empty page counter
                consecutive_empty_pages = 0

                logger.debug(f"Found {len(ads)} ads on page {page}")

                ads_processed = 0
                for ad in ads:
                    try:
                        # Check if ad was processed (returns True if added)
                        if self._process_ad(ad, apply_filters):
                            ads_processed += 1
                    except Exception as e:
                        logger.warning(f"Error processing ad: {e}")
                        continue

                logger.info(
                    f"Page {page} complete. Processed {ads_processed}/{len(ads)} ads. "
                    f"Total GPUs: {sum(len(v) for v in self.gpu_prices.values())}"
                )

                # Check if this is the last page
                has_next = self._check_has_next_page(soup)
                if not has_next:
                    logger.info(f"Reached last page (page {page}). No 'next' button found.")
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                consecutive_empty_pages += 1
                page += 1
                continue

        total_listings = sum(len(v) for v in self.gpu_prices.values())
        logger.info(
            f"Scraping complete. Scanned {page} pages. "
            f"Collected {len(self.gpu_prices)} models, "
            f"{total_listings} total listings"
        )

        # Report scraping completion (80% - post-processing will be 80-100%)
        self._report_progress(
            80,
            "Scraping завършено",
            pages_scraped=page,
            models_found=len(self.gpu_prices),
            total_listings=total_listings
        )

        # Log filter statistics if filters were applied
        if apply_filters and hasattr(self, '_filter_stats') and self._filter_stats:
            logger.info("📊 Filter Statistics:")
            for reason, count in sorted(self._filter_stats.items()):
                logger.info(f"  {reason}: {count}")

        return self.gpu_prices

    def _process_ad(self, ad, apply_filters: bool) -> bool:
        """
        Обработва една обява

        Returns:
            True if ad was processed and added, False otherwise
        """
        # Extract URL from the ad link
        url = ad.get('href', '')
        if url and not url.startswith('http'):
            url = f"https://www.olx.bg{url}"

        title_el = ad.find(["h4", "h6"])

        # Try multiple methods to find the price element (OLX structure varies)
        price_el = None
        price_text = ""

        # Method 1: Look for price with data-testid (most reliable)
        price_el = ad.find_next("p", {"data-testid": "ad-price"})
        if price_el:
            price_text = price_el.text.strip()

        # Method 2: Look for price in next <p> with "лв" (original method)
        if not price_text:
            price_candidates = ad.find_all_next("p", limit=5)  # Check first 5 <p> elements
            for candidate in price_candidates:
                text = candidate.text.strip()
                if "лв" in text and re.search(r"\d+", text):
                    # Prefer elements with higher prices (avoid "99 лв" type promotional text)
                    price_num_match = re.search(r"(\d+(?:\s\d+)*)", text)
                    if price_num_match:
                        price_num = int(price_num_match.group(1).replace(" ", ""))
                        # Skip suspiciously low "prices" that are likely badges/promotions
                        if price_num >= 20:  # Minimum reasonable price for any GPU part
                            price_text = text
                            break

        if not title_el or not price_text:
            return False

        title = title_el.text.strip()
        price_match = re.search(r"(\d+(?:\s\d+)*)\s*лв", price_text)

        if not price_match:
            return False

        try:
            price = int(price_match.group(1).replace(" ", ""))
        except ValueError:
            logger.warning(f"Invalid price format: {price_match.group(1)}")
            return False

        # Try to extract description snippet (if available in listing preview)
        description = ""
        # OLX often shows description in <p> tags near the title
        desc_candidates = ad.find_all("p")
        for p in desc_candidates:
            text = p.text.strip()
            # Skip price paragraphs and very short text
            if text and "лв" not in text and len(text) > 20:
                description = text
                break

        # Combine title and description for filtering
        full_text = f"{title} {description}".strip()

        # Extract and normalize model
        model = self.extract_gpu_model(title)

        if model:
            if apply_filters:
                # Get all current prices for this model (for outlier detection)
                current_prices = self.gpu_prices.get(model, [])

                # Check full text (title + description) for suspicious content
                is_suspicious, reason = self.is_suspicious_listing(
                    full_text, price, model, current_prices
                )

                if is_suspicious:
                    logger.debug(f"Filtered: {model} - {price}лв [{reason}]")

                    # Track filter reason
                    self._filtered_count += 1
                    category = self._categorize_filter_reason(reason)
                    self._filter_stats[category] = self._filter_stats.get(category, 0) + 1

                    return False

            # Store both price and URL
            self.gpu_prices[model].append({'price': price, 'url': url})
            logger.debug(f"Added: {model} - {price}лв ({url})")
            return True

        return False

    def _categorize_filter_reason(self, reason: str) -> str:
        """Categorize filter reason for statistics"""
        if "blacklisted keyword" in reason.lower():
            return "🚫 Blacklisted Keywords"
        elif "statistical outlier" in reason.lower():
            return "📊 Statistical Outlier (Too Low)"
        elif "too high" in reason.lower():
            return "💸 Statistical Outlier (Too High)"
        elif "extremely low" in reason.lower():
            return "⚠️  Extremely Low Price (<50лв)"
        elif "too short" in reason.lower():
            return "📝 Low Quality Title"
        else:
            return "❓ Other"

    # ================= FILTERS =================

    def is_suspicious_listing(
        self,
        title: str,
        price: int,
        gpu_model: str,
        all_prices_for_model: Optional[list] = None
    ) -> Tuple[bool, str]:
        """Проверява дали обявата е съмнителна"""
        from core.filters import is_suspicious_listing as filter_check

        # Use enhanced filter with statistical outlier detection
        return filter_check(
            title,
            price,
            gpu_model,
            dynamic_min_price=0,  # Not used anymore
            all_prices_for_model=all_prices_for_model or []
        )

    def calculate_dynamic_min_prices(self):
        """Изчислява динамични минимални цени (deprecated but kept for compatibility)"""
        logger.info("Calculating dynamic minimum prices (using statistical methods)...")

        # This method is now deprecated as we use real-time statistical filtering
        # But we keep it for backwards compatibility with the pipeline
        for model, prices in self.gpu_prices.items():
            if len(prices) >= 2:
                median = statistics.median(prices)
                min_price = int(median * 0.30)  # 30% threshold
                self.min_reasonable_prices[model] = min_price
                logger.debug(f"{model}: statistical minimum = {min_price}лв")
            else:
                self.min_reasonable_prices[model] = 0

    # ================= ANALYSIS =================

    def extract_gpu_model(self, title: str) -> Optional[str]:
        """
        Извлича и нормализира GPU модел от заглавие

        Examples:
            "RTX3060TI 12GB" -> "RTX 3060 TI"
            "rx 6600xt oc" -> "RX 6600 XT"
            "GTX 1660ti super" -> "GTX 1660 TI"
        """
        patterns = [
            r"RTX\s?\d{4}\s?(TI|SUPER)?",
            r"GTX\s?\d{4}\s?(TI|SUPER)?",
            r"RX\s?\d{4}\s?(XTX|XT|GRE)?",  # XTX before XT (longer match first)
            r"ARC\s?[AB]\d{3}",  # Intel ARC (A-series: Alchemist, B-series: Battlemage)
            r"VEGA\s?\d+",
        ]

        title_upper = title.upper()

        for pattern in patterns:
            match = re.search(pattern, title_upper)
            if match:
                model = match.group(0)

                # Normalize the model name
                from core.filters import normalize_model_name
                normalized = normalize_model_name(model)

                return normalized

        return None

    def get_min_prices(self, use_percentile=True) -> Dict[str, int]:
        """Връща минимални цени"""
        result = {}
        for model, prices in self.gpu_prices.items():
            if not prices:
                continue
            if use_percentile and len(prices) >= 3:
                prices_sorted = sorted(prices)
                result[model] = prices_sorted[len(prices) // 4]
            else:
                result[model] = min(prices)
        return result

    def add_benchmark_data(self, data: Dict[str, float]):
        """Добавя benchmark данни"""
        self.gpu_benchmarks = data
        logger.info(f"Loaded {len(data)} benchmark entries")

    def calculate_value(
        self,
        use_percentile=True
    ) -> List[Tuple[str, float, int, float]]:
        """Изчислява FPS/лв"""
        min_prices = self.get_min_prices(use_percentile)
        results = []

        for model, price in min_prices.items():
            # Normalize both for comparison
            from core.filters import normalize_model_name
            norm_model = normalize_model_name(model).replace(" ", "")

            for b_model, fps in self.gpu_benchmarks.items():
                norm_bench = normalize_model_name(b_model).replace(" ", "")

                if norm_model == norm_bench or norm_model in norm_bench or norm_bench in norm_model:
                    results.append((model, fps, price, fps / price))
                    break

        return sorted(results, key=lambda x: x[3], reverse=True)


# ================= BENCHMARKS =================
# Sources: TechPowerUp Reviews + Tom's Hardware + TechSpot + GamersNexus (2025)
# Resolution: 1080p Ultra/High (Raster Performance)
# Updated: 2025-12-24
#
# Note: Values are average FPS across multiple AAA games at 1080p ultra/high settings
# Data represents rasterization (traditional rendering), not ray tracing
# Compiled from multiple benchmark sources for accuracy and coverage

# GPU Benchmark Data - 1080p Ultra Average FPS (2025)
# Comprehensive dataset compiled from multiple reliable sources
# Data represents average FPS across modern AAA games at 1080p Ultra settings
SAMPLE_BENCHMARKS = {
    # NVIDIA GeForce RTX 50-series (Blackwell) - Latest Generation
    "RTX 5090": 188.0,
    "RTX 5080": 171.0,
    "RTX 5070 TI": 160.0,
    "RTX 5070": 145.0,
    "RTX 5060 TI 16GB": 118.0,
    "RTX 5060 TI 8GB": 115.0,
    "RTX 5060 TI": 115.0,
    "RTX 5060": 97.0,

    # NVIDIA GeForce RTX 40-series (Ada Lovelace)
    "RTX 4090": 184.0,
    "RTX 4080 SUPER": 177.0,
    "RTX 4080": 174.0,
    "RTX 4070 TI SUPER": 167.0,
    "RTX 4070 TI": 164.0,
    "RTX 4070 SUPER": 160.0,
    "RTX 4070": 150.0,
    "RTX 4060 TI 16GB": 127.0,
    "RTX 4060 TI 8GB": 124.0,
    "RTX 4060 TI": 124.0,
    "RTX 4060": 107.0,

    # NVIDIA GeForce RTX 30-series (Ampere)
    "RTX 3090 TI": 157.0,
    "RTX 3090": 154.0,
    "RTX 3080 TI": 152.0,
    "RTX 3080 12GB": 150.0,
    "RTX 3080": 148.0,
    "RTX 3070 TI": 140.0,
    "RTX 3070": 134.0,
    "RTX 3060 TI": 120.0,
    "RTX 3060 12GB": 97.0,
    "RTX 3060": 97.0,
    "RTX 3050 8GB": 74.0,
    "RTX 3050": 74.0,

    # NVIDIA GeForce RTX 20-series (Turing)
    "RTX 2080 TI": 130.0,
    "RTX 2080 SUPER": 120.0,
    "RTX 2080": 117.0,
    "RTX 2070 SUPER": 110.0,
    "RTX 2070": 100.0,
    "RTX 2060 SUPER": 94.0,
    "RTX 2060 12GB": 84.0,
    "RTX 2060": 84.0,

    # NVIDIA GeForce GTX 16-series (Turing)
    "GTX 1660 SUPER": 80.0,
    "GTX 1660 TI": 78.0,
    "GTX 1660": 74.0,
    "GTX 1650 SUPER": 66.0,
    "GTX 1650": 54.0,

    # NVIDIA GeForce GTX 10-series (Pascal)
    "GTX 1080 TI": 104.0,
    "GTX 1080": 90.0,
    "GTX 1070 TI": 82.0,
    "GTX 1070": 76.0,
    "GTX 1060 6GB": 60.0,
    "GTX 1060 3GB": 56.0,
    "GTX 1050 TI": 44.0,
    "GTX 1050": 36.0,

    # AMD Radeon RX 9000-series (RDNA 4) - Latest Generation
    "RX 9070 XT": 160.0,
    "RX 9070": 150.0,
    "RX 9060 XT": 112.0,

    # AMD Radeon RX 7000-series (RDNA 3)
    "RX 7900 XTX": 174.0,
    "RX 7900 XT": 170.0,
    "RX 7900 GRE": 164.0,
    "RX 7800 XT": 154.0,
    "RX 7700 XT": 144.0,
    "RX 7600 XT 16GB": 120.0,
    "RX 7600 XT": 120.0,
    "RX 7600": 107.0,

    # AMD Radeon RX 6000-series (RDNA 2)
    "RX 6950 XT": 160.0,
    "RX 6900 XT": 156.0,
    "RX 6800 XT": 150.0,
    "RX 6800": 144.0,
    "RX 6750 XT": 137.0,
    "RX 6700 XT": 130.0,
    "RX 6700": 120.0,
    "RX 6650 XT": 114.0,
    "RX 6600 XT": 110.0,
    "RX 6600": 94.0,
    "RX 6500 XT": 70.0,
    "RX 6400": 52.0,

    # AMD Radeon RX 5000-series (RDNA 1)
    "RX 5700 XT": 100.0,
    "RX 5700": 94.0,
    "RX 5600 XT": 87.0,
    "RX 5500 XT 8GB": 70.0,
    "RX 5500 XT": 70.0,

    # AMD Radeon RX 500-series (Polaris)
    "RX 590": 64.0,
    "RX 580 8GB": 60.0,
    "RX 580": 60.0,
    "RX 570 8GB": 54.0,
    "RX 570": 54.0,
    "RX 560": 38.0,

    # AMD Radeon Vega
    "RADEON VII": 107.0,
    "RX VEGA 64": 90.0,
    "RX VEGA 56": 84.0,

    # Intel Arc (Alchemist & Battlemage)
    "ARC B580": 117.0,
    "ARC B570": 107.0,
    "ARC A770 16GB": 110.0,
    "ARC A770": 110.0,
    "ARC A750": 104.0,
    "ARC A580": 94.0,
    "ARC A380": 67.0,

    # NVIDIA Titan Series
    "TITAN RTX": 137.0,
    "TITAN V": 97.0,
    "TITAN XP": 87.0,
}

# GPU VRAM specifications in GB
GPU_VRAM = {
    # NVIDIA GeForce RTX 50-series (Blackwell)
    "RTX 5090": 32,
    "RTX 5080": 16,
    "RTX 5070 TI": 16,
    "RTX 5070": 12,
    "RTX 5060 TI 16GB": 16,
    "RTX 5060 TI 8GB": 8,
    "RTX 5060 TI": 8,
    "RTX 5060": 8,

    # NVIDIA GeForce RTX 40-series (Ada Lovelace)
    "RTX 4090": 24,
    "RTX 4080 SUPER": 16,
    "RTX 4080": 16,
    "RTX 4070 TI SUPER": 16,
    "RTX 4070 TI": 12,
    "RTX 4070 SUPER": 12,
    "RTX 4070": 12,
    "RTX 4060 TI 16GB": 16,
    "RTX 4060 TI": 8,
    "RTX 4060": 8,

    # NVIDIA GeForce RTX 30-series (Ampere)
    "RTX 3090 TI": 24,
    "RTX 3090": 24,
    "RTX 3080 TI": 12,
    "RTX 3080 12GB": 12,
    "RTX 3080": 10,
    "RTX 3070 TI": 8,
    "RTX 3070": 8,
    "RTX 3060 TI": 8,
    "RTX 3060": 12,
    "RTX 3050": 8,

    # NVIDIA GeForce RTX 20-series (Turing)
    "RTX 2080 TI": 11,
    "RTX 2080 SUPER": 8,
    "RTX 2080": 8,
    "RTX 2070 SUPER": 8,
    "RTX 2070": 8,
    "RTX 2060 SUPER": 8,
    "RTX 2060": 6,

    # NVIDIA GeForce GTX 10/16-series (Pascal/Turing)
    "GTX 1660 SUPER": 6,
    "GTX 1660 TI": 6,
    "GTX 1660": 6,
    "GTX 1650 SUPER": 4,
    "GTX 1080 TI": 11,
    "GTX 1080": 8,
    "GTX 1070 TI": 8,
    "GTX 1070": 8,
    "GTX 1060 6GB": 6,
    "GTX 1060 3GB": 3,
    "GTX 1050 TI": 4,
    "GTX 1050": 2,

    # AMD Radeon RX 9000-series (RDNA 4)
    "RX 9070 XT": 16,
    "RX 9070": 12,
    "RX 9060 XT": 12,

    # AMD Radeon RX 7000-series (RDNA 3)
    "RX 7900 XTX": 24,
    "RX 7900 XT": 20,
    "RX 7900 GRE": 16,
    "RX 7800 XT": 16,
    "RX 7700 XT": 12,
    "RX 7600 XT": 16,
    "RX 7600": 8,

    # AMD Radeon RX 6000-series (RDNA 2)
    "RX 6950 XT": 16,
    "RX 6900 XT": 16,
    "RX 6800 XT": 16,
    "RX 6800": 16,
    "RX 6750 XT": 12,
    "RX 6700 XT": 12,
    "RX 6700": 10,
    "RX 6650 XT": 8,
    "RX 6600 XT": 8,
    "RX 6600": 8,
    "RX 6500 XT": 4,

    # AMD Radeon RX 5000-series (RDNA 1)
    "RX 5700 XT": 8,
    "RX 5700": 8,
    "RX 5600 XT": 6,
    "RX 5500 XT": 8,

    # AMD Radeon RX 500-series (Polaris)
    "RX 590": 8,
    "RX 580": 8,
    "RX 570": 4,

    # AMD Radeon Vega
    "RADEON VII": 16,
    "RX VEGA 64": 8,
    "RX VEGA 56": 8,

    # Intel Arc (Alchemist & Battlemage)
    "ARC B580": 12,
    "ARC B570": 10,
    "ARC A770": 16,
    "ARC A750": 8,
    "ARC A580": 8,
    "ARC A380": 6,

    # Titan cards
    "TITAN RTX": 24,
    "TITAN V": 12,
    "TITAN XP": 12,
}