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
from data.gpu_fps_manual import GPU_FPS_BENCHMARKS
from core.filters import COMPUTER_KEYWORDS

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
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
        ])

        self.gpu_prices = defaultdict(list)
        self.gpu_benchmarks: Dict[str, float] = {}
        self.min_reasonable_prices = {}
        self.seen_urls = set()  # Track URLs to prevent duplicates from multiple search terms

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
        self._rejected_listings = []  # Store rejected listings with reasons
        self._last_rejection_reason = None  # Track why last listing was rejected
        self._last_rejected_model = None  # Track the base model that was rejected

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
            from stem import Signal
            from stem.control import Controller

            # Try both common TOR control ports (9051 is default, 9151 is browser)
            ports_to_try = [9051, 9151]

            for port in ports_to_try:
                try:
                    with Controller.from_port(port=port) as controller:
                        controller.authenticate()
                        controller.signal(Signal.NEWNYM)
                        logger.info(f"✅ TOR IP renewed successfully via port {port}")
                        time.sleep(10)  # Wait longer for circuit to establish
                        return
                except Exception as port_error:
                    logger.debug(f"Port {port} failed: {port_error}")
                    continue

            logger.warning("❌ Could not renew TOR IP on any port (9051, 9151)")

        except ImportError:
            logger.warning("⚠️  stem library not installed, cannot renew TOR IP")
        except Exception as e:
            logger.error(f"❌ Failed to renew TOR IP: {e}")

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
        user_agent = random.choice(self.user_agents)

        # Detect browser type from user agent
        is_firefox = "Firefox" in user_agent
        is_chrome = "Chrome" in user_agent and "Firefox" not in user_agent

        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "bg-BG,bg;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

        # Add browser-specific headers
        if is_chrome:
            headers.update({
                "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })
        elif is_firefox:
            headers.update({
                "DNT": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })

        # Add referer occasionally (simulate browsing from Google or direct)
        if random.random() < 0.3:  # 30% chance of having referer
            headers["Referer"] = random.choice([
                "https://www.google.com/",
                "https://www.google.bg/",
            ])

        return headers

    @retry_on_failure(
        max_retries=3,
        delay=15,  # Increased from 10 to 15
        backoff=2.0,
        exceptions=(requests.RequestException, requests.HTTPError)
    )
    def make_request(self, url: str) -> Optional[requests.Response]:
        """Прави HTTP заявка с rate limiting и retry"""
        # Rate limiting
        self.request_limiter.wait()

        # Add random delay to simulate human behavior (2-5 seconds)
        human_delay = random.uniform(2.0, 5.0)
        logger.debug(f"Human-like delay: {human_delay:.2f}s")
        time.sleep(human_delay)

        try:
            logger.debug(f"Making request to: {url}")

            r = requests.get(
                url,
                headers=self._get_realistic_headers(),
                proxies=self.get_proxy(),
                timeout=30,  # Increased timeout from 20 to 30
                allow_redirects=True,
            )
            r.raise_for_status()

            logger.debug(f"Request successful: {url} (Status: {r.status_code})")

            # Random delay after successful request
            post_delay = random.uniform(1.0, 3.0)
            time.sleep(post_delay)

            return r

        except requests.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {url}")

            if e.response.status_code == 429:
                logger.warning("⚠️  Rate limited by server, waiting 90s...")
                time.sleep(90)
                if self.use_tor:
                    self.renew_tor_ip()

            if e.response.status_code == 403:
                logger.warning("⚠️  403 Forbidden - possible bot detection")
                if self.use_tor:
                    logger.info("🔄 Renewing TOR IP and waiting 45s...")
                    self.renew_tor_ip()
                    time.sleep(45)  # Increased wait time
                else:
                    logger.warning("⚠️  Consider enabling TOR to avoid 403 errors")
                    time.sleep(30)

            raise

        except requests.Timeout:
            logger.error(f"⏱️  Request timeout: {url}")
            raise

        except requests.ConnectionError as e:
            logger.error(f"🔌 Connection error: {url} - {e}")
            raise

        except Exception as e:
            logger.error(f"❌ Unexpected error during request: {e}")
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
        search_terms=None,
        max_pages=None,
        apply_filters=False
    ) -> Dict[str, List[int]]:
        """
        Събира обяви от OLX със защита от грешки и auto-pagination

        Args:
            search_terms: Single search term (str) or list of search terms (List[str])
                         Default: 13 terms covering all GPU types:
                         - Bulgarian: видео, видеокарта, графична
                         - NVIDIA: rtx, gtx, geforce, nvidia
                         - AMD: rx, radeon, amd
                         - Intel: arc, intel
                         - Technical: gpu
            max_pages: Max pages per search term (default: 3)
            apply_filters: DEPRECATED - filtering happens in post-processing

        NOTE: apply_filters parameter is DEPRECATED and ignored.
        All filtering now happens in post-processing after scraping is complete.
        """
        # Default search terms if none provided
        if search_terms is None:
            search_terms = [
                # Primary Bulgarian terms (highest priority)
                "видеокарта",      # слято написано (264 new GPUs)
                "графична",        # графична карта (105 new GPUs)
                "видео",           # видео карта (103 new GPUs)

                # NVIDIA series (most results)
                "rtx",             # RTX 4090, GeForce RTX 3080 (677 new GPUs)
                "gtx",             # GTX 1660, GeForce GTX 1080 (375 new GPUs)

                # AMD series
                "rx",              # RX 6600, RX 7900 XT (219 new GPUs)

                # Intel
                "arc",             # Arc A770, Intel Arc B580 (4 new GPUs)
            ]

        # Support single string for backwards compatibility
        if isinstance(search_terms, str):
            search_terms = [search_terms]

        max_pages = max_pages or config.scraper_max_pages
        scrape_all = config.get("scraper.scrape_all_pages", False)

        logger.info(
            f"Starting OLX scrape with {len(search_terms)} search terms: {search_terms} "
            f"(max_pages: {max_pages if not scrape_all else 'ALL'} per term)"
        )

        # Report initial progress
        self._report_progress(0, "Започване на scraping...", search_terms=search_terms)

        # Always scrape without filtering - post-processing will handle it
        apply_filters = False

        total_pages_scraped = 0

        # Loop through each search term
        for term_index, search_term in enumerate(search_terms):
            logger.info(f"📍 [{term_index + 1}/{len(search_terms)}] Scraping search term: '{search_term}'")

            page = 1
            consecutive_empty_pages = 0
            max_empty_pages = 3  # Stop after 3 empty pages in a row

            while True:
                # Check if we should stop
                if not scrape_all and page > max_pages:
                    logger.info(f"Reached max pages limit: {max_pages} for term '{search_term}'")
                    break

                if consecutive_empty_pages >= max_empty_pages:
                    logger.info(f"No more results found after {max_empty_pages} empty pages for '{search_term}'. Moving to next term.")
                    break

                try:
                    # Rate limiting между страници
                    if page > 1:
                        self.page_limiter.wait()

                    url = f"https://www.olx.bg/elektronika/q-{search_term}/"
                    if page > 1:
                        url += f"?page={page}"

                    logger.info(f"Scraping '{search_term}' page {page}...")

                    # Report progress for current page
                    # Calculate progress based on term index and page
                    term_progress = (term_index / len(search_terms)) * 80
                    page_progress = (page / max_pages) * (80 / len(search_terms)) if not scrape_all else 5
                    progress_pct = min(int(term_progress + page_progress), 80)

                    self._report_progress(
                        progress_pct,
                        f"Scraping '{search_term}' ({term_index + 1}/{len(search_terms)}) - страница {page}...",
                        current_term=search_term,
                        current_page=page,
                        total_listings=sum(len(v) for v in self.gpu_prices.values())
                    )

                    response = self.make_request(url)
                    if not response:
                        logger.warning(f"Failed to fetch page {page} for '{search_term}', skipping...")
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
                        f"'{search_term}' page {page} complete. Processed {ads_processed}/{len(ads)} ads. "
                        f"Total GPUs: {sum(len(v) for v in self.gpu_prices.values())}"
                    )

                    # Check if this is the last page
                    has_next = self._check_has_next_page(soup)
                    if not has_next:
                        logger.info(f"Reached last page (page {page}) for '{search_term}'.")
                        break

                    page += 1

                except Exception as e:
                    logger.error(f"Error on page {page} for '{search_term}': {e}")
                    consecutive_empty_pages += 1
                    page += 1
                    continue

            total_pages_scraped += page
            logger.info(f"✅ Completed '{search_term}': scanned {page} pages")

        total_listings = sum(len(v) for v in self.gpu_prices.values())
        logger.info(
            f"🎯 Scraping complete for all {len(search_terms)} terms. "
            f"Total pages: {total_pages_scraped}. "
            f"Collected {len(self.gpu_prices)} models, "
            f"{total_listings} total listings"
        )

        # Report scraping completion (80% - post-processing will be 80-100%)
        self._report_progress(
            80,
            "Scraping завършено",
            pages_scraped=total_pages_scraped,
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
            candidate_prices = []

            for candidate in price_candidates:
                text = candidate.text.strip()
                if "лв" in text and re.search(r"\d+", text):
                    # Extract numeric value (including decimals like "1749.99")
                    price_num_match = re.search(r"(\d+(?:[\s,]\d+)*(?:\.\d+)?)", text)
                    if price_num_match:
                        # Parse price (handle "1 500", "1,500", "1500.99" formats)
                        price_str = price_num_match.group(1).replace(" ", "").replace(",", "")
                        try:
                            price_num = float(price_str)
                            # Skip suspiciously low prices (likely decimal parts or badges)
                            if price_num >= 100:  # Increased threshold to avoid decimal portions
                                candidate_prices.append((price_num, text))
                        except ValueError:
                            continue

            # Select the highest price among candidates (avoids decimal portions like "99 лв")
            if candidate_prices:
                candidate_prices.sort(reverse=True)  # Sort by price descending
                price_text = candidate_prices[0][1]  # Take highest price text

        if not title_el or not price_text:
            return False

        title = title_el.text.strip()
        # Updated regex to handle decimal prices like "1749.99 лв", "1 500.50 лв", or "1,500.99 лв"
        price_match = re.search(r"(\d+(?:[\s,]\d+)*(?:\.\d+)?)\s*лв", price_text)

        if not price_match:
            return False

        try:
            # Handle "1 500", "1,500", "1500.99" formats (space/comma = thousands, dot = decimal)
            price_str = price_match.group(1).replace(" ", "").replace(",", "")
            price = float(price_str)
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
        full_text_lower = full_text.lower()

        # Check for full computer listings BEFORE extracting model
        # This prevents false "missing VRAM" rejections for computer listings
        for keyword in COMPUTER_KEYWORDS:
            if keyword.lower() in full_text_lower:
                # Track this as rejected for visibility
                self._filtered_count += 1
                category = "💻 Full Computer/Laptop"
                self._filter_stats[category] = self._filter_stats.get(category, 0) + 1

                self._rejected_listings.append({
                    'title': title,
                    'price': price,
                    'url': url,
                    'model': None,
                    'reason': f"Full computer listing: '{keyword}'",
                    'category': category
                })
                return False

        # Extract and normalize model (with VRAM detection from title/description)
        model = self.extract_gpu_model(title, description)

        # Check if model extraction triggered a rejection (e.g., invalid VRAM)
        # This happens when extract_gpu_model() returns a valid base model but sets _last_rejection_reason
        # ALWAYS track VRAM/model validation rejections (even when apply_filters=False)
        # because this is data validation, not filtering
        if self._last_rejection_reason:
            # Track this rejection FOR VISIBILITY in /rejected page
            self._filtered_count += 1
            category = self._categorize_filter_reason(self._last_rejection_reason)
            self._filter_stats[category] = self._filter_stats.get(category, 0) + 1

            # Store rejected listing (for tracking/monitoring)
            self._rejected_listings.append({
                'title': title,
                'price': price,
                'url': url,
                'model': model or self._last_rejected_model,  # Use extracted model or rejected base model
                'reason': self._last_rejection_reason,
                'category': category
            })

            # Clear the rejection reason and model
            self._last_rejection_reason = None
            self._last_rejected_model = None

            # NOTE: We DON'T skip the listing!
            # Continue processing with the base model (e.g., "RTX 3060 TI" without the invalid "16GB")
            # This allows us to track the issue but still use the valid data

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

                    # Store rejected listing with details
                    self._rejected_listings.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'model': model,
                        'reason': reason,
                        'category': category
                    })

                    return False

            # Check if URL already processed (prevents duplicates from multiple search terms)
            if url in self.seen_urls:
                logger.debug(f"Skipping duplicate URL: {url}")
                return False

            # Store price, URL, title, and description for post-processing filtering
            self.gpu_prices[model].append({'price': price, 'url': url, 'title': title, 'description': description})
            self.seen_urls.add(url)
            logger.debug(f"Added: {model} - {price}лв ({url})")
            return True

        # Model extraction failed - check if we have a rejection reason
        # ALWAYS track VRAM/model validation rejections (even when apply_filters=False)
        # because this is data validation, not filtering
        if self._last_rejection_reason:
            # Track this rejection
            self._filtered_count += 1
            category = self._categorize_filter_reason(self._last_rejection_reason)
            self._filter_stats[category] = self._filter_stats.get(category, 0) + 1

            # Store rejected listing
            self._rejected_listings.append({
                'title': title,
                'price': price,
                'url': url,
                'model': self._last_rejected_model,  # Base model that was rejected
                'reason': self._last_rejection_reason,
                'category': category
            })

            # Clear the rejection reason and model for next listing
            self._last_rejection_reason = None
            self._last_rejected_model = None

        return False

    def _categorize_filter_reason(self, reason: str) -> str:
        """Categorize filter reason for statistics"""
        reason_lower = reason.lower()

        # Check for water cooling keywords BEFORE general blacklist
        water_cooling_keywords = ['ekwb', 'ek-wb', 'ek water', 'water block', 'waterblock',
                                   'воден блок', 'водно охлаждане', 'liquid cooling']
        for wc_keyword in water_cooling_keywords:
            if wc_keyword in reason_lower:
                return "💧 Water Cooling Parts"

        if "blacklisted keyword" in reason_lower:
            return "🚫 Blacklisted Keywords"
        elif "full computer" in reason.lower() or "laptop" in reason.lower():
            return "💻 Full Computer/Laptop"
        elif "typo" in reason.lower():
            return "❌ Invalid GPU Model (Typo)"
        elif "invalid vram" in reason.lower():
            return "💾 Invalid VRAM"
        elif "липсващ vram" in reason.lower() or "cannot determine vram" in reason.lower():
            return "🔍 Липсващ VRAM"
        elif "unknown gpu" in reason.lower() or "invalid/unknown" in reason.lower():
            return "❓ Unknown GPU Model"
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

    def extract_vram_from_text(self, text: str) -> Optional[str]:
        """
        Извлича VRAM от текст (title или description)

        Examples:
            "RTX 3060 12GB" -> "12GB"
            "8GB VRAM memory" -> "8GB"
            "видео карта с 16 GB" -> "16GB"
            "RTX 4080 16 GB GDDR6X" -> "16GB"

        Returns:
            VRAM string (e.g., "12GB") or None if not found
        """
        # Common VRAM sizes: 2GB, 3GB, 4GB, 6GB, 8GB, 10GB, 11GB, 12GB, 16GB, 20GB, 24GB, 32GB, 48GB
        # Match formats: "8GB", "8G", "8гб", "8г" (Cyrillic), "8 GB", etc.
        #
        # IMPORTANT: "3г" alone often means "3 години" (3 years warranty) in Bulgarian!
        # But GTX 1060 3GB is a real card. Solution: exclude warranty context patterns.

        valid_vram_sizes = [2, 3, 4, 6, 8, 10, 11, 12, 16, 20, 24, 32, 48]

        # First, check if text contains warranty context that might confuse us
        # If "Xг гаранция" or "гаранция Xг" pattern exists, exclude that number
        warranty_pattern = r'(\d{1,2})\s?[гГ]\.?\s*(?:гаранция|години|год)|(?:гаранция|години)\s*(\d{1,2})\s?[гГ]'
        warranty_matches = re.findall(warranty_pattern, text, re.IGNORECASE)
        warranty_numbers = set()
        for match in warranty_matches:
            for num in match:
                if num:
                    warranty_numbers.add(int(num))

        # Try patterns in order of specificity
        patterns = [
            r'\b(\d{1,2})\s?GB\b',       # 8GB, 8 GB (Latin, full)
            r'\b(\d{1,2})\s?[Гг][Бб]\b', # 8гб, 8ГБ (Cyrillic, full)
            r'\b(\d{1,2})\s?G\b',        # 8G (Latin, short)
            r'\b(\d{1,2})\s?[Гг]\b',     # 8г (Cyrillic short)
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                vram_size = int(match)
                # Skip if this number was identified as warranty years
                if vram_size in warranty_numbers:
                    continue
                if vram_size in valid_vram_sizes:
                    return f"{vram_size}GB"

        return None

    def extract_gpu_model(self, title: str, description: str = "") -> Optional[str]:
        """
        Извлича и нормализира GPU модел от заглавие и опционално description

        VALIDATES extracted model against known GPUs to reject typos like "GTX 1018"
        Извлича VRAM от title или description и го добавя към модела

        Examples:
            "RTX3060TI 12GB" -> "RTX 3060 TI 12GB" ✅
            "rx 6600xt oc" (desc: "8GB VRAM") -> "RX 6600 XT 8GB" ✅
            "GTX 1660ti super" -> "GTX 1660 TI" ✅
            "GTX 1018" -> None ❌ (typo, should be GTX 1080)
            "Gigabyte 1060 6gb" -> "GTX 1060 6GB" ✅ (добавя GTX префикс)
        """
        patterns = [
            # Standard patterns with brand prefix (with optional space)
            r"RTX\s?\d{4}\s?(TI|SUPER)?",
            r"GTX\s?\d{3,4}\s?(TI|SUPER)?",  # GTX supports 3-4 digits (GTX 960, GTX 1660)
            r"RX\s?\d{3,4}\s?(XTX|XT|GRE)?",  # RX supports 3-4 digits (RX 580, RX 6800)

            # Patterns without space before suffix (common in Bulgarian listings)
            # Examples: RTX3060TI, GTX1660TI, RX5500XT, RX6600XT
            r"RTX\d{4}(TI|SUPER)",  # RTX3060TI, RTX4070SUPER
            r"GTX\d{3,4}(TI|SUPER)",  # GTX1660TI, GTX1650SUPER
            r"RX\d{3,4}(XTX|XT|GRE)?",  # RX5500XT, RX6600XT, RX580

            r"ARC\s?[AB]\d{3}",  # Intel ARC (A-series: Alchemist, B-series: Battlemage)
            r"VEGA\s?\d+",

            # Patterns for listings without GTX/RTX prefix but with manufacturer name
            # Example: "Gigabyte 1060 6gb" -> should be detected as GTX 1060
            r"(?:NVIDIA|GIGABYTE|ASUS|MSI|ZOTAC|EVGA|PNY|PALIT|GAINWARD|INNO3D|KFA2|GALAX|COLORFUL|MANLI)\s+(\d{3,4})\s?(TI|SUPER)?",
        ]

        title_upper = title.upper()

        # First try standard patterns
        for pattern in patterns[:-1]:  # All patterns except the last manufacturer one
            match = re.search(pattern, title_upper)
            if match:
                model = match.group(0)
                break
        else:
            # If standard patterns didn't match, try manufacturer pattern
            match = re.search(patterns[-1], title_upper)
            if match:
                # Extract just the model number (e.g., "1060" from "GIGABYTE 1060")
                model_number = match.group(1)
                suffix = match.group(2) if match.group(2) else ""

                # Determine which brand prefix to add based on model number
                # GTX 10xx, 16xx series: add GTX
                # RTX 20xx, 30xx, 40xx, 50xx: add RTX (shouldn't happen as RTX is usually written)
                if model_number.startswith('1') or model_number.startswith('9'):
                    # GTX 10-series (1030-1080), 16-series (1650-1660), 9-series (960-980)
                    model = f"GTX {model_number}"
                    if suffix:
                        model += f" {suffix}"
                elif model_number.startswith(('2', '3', '4', '5')):
                    # RTX 20/30/40/50-series (unlikely to be missing RTX in title)
                    model = f"RTX {model_number}"
                    if suffix:
                        model += f" {suffix}"
                else:
                    # Unknown series, skip
                    model = None
            else:
                model = None

        if not model:
            return None

        # Normalize the model name
        from core.filters import normalize_model_name
        normalized = normalize_model_name(model)

        # Try to extract VRAM from title first
        vram = self.extract_vram_from_text(title)

        # If no VRAM in title, try description
        if not vram and description:
            vram = self.extract_vram_from_text(description)

        # Add VRAM to model if found AND not already in normalized model
        # Prevents "GTX 1060 6GB" + "6GB" -> "GTX 1060 6GB 6GB"
        if vram and vram not in normalized:
            # VRAM VALIDATION: Check if extracted VRAM is valid for this GPU model
            if not self._is_valid_vram_for_model(normalized, vram):
                logger.warning(f"Invalid VRAM {vram} for model {normalized} - rejecting (likely system RAM confusion)")
                self._last_rejection_reason = f"Invalid VRAM {vram} for model {normalized} (likely system RAM confusion)"
                self._last_rejected_model = normalized  # Save base model for rejected listings
                # Return model without VRAM if base model is valid
                if self._is_valid_gpu_model(normalized):
                    return normalized
                return None

            # Check if VRAM is redundant (model has only one VRAM variant)
            if self._is_redundant_vram(normalized, vram):
                logger.debug(f"Removing redundant VRAM: {normalized} {vram} -> {normalized}")
                model_with_vram = normalized
            else:
                model_with_vram = f"{normalized} {vram}"
        else:
            # No VRAM extracted - check if we should auto-add or reject
            if normalized in GPU_VRAM:
                expected_vram = GPU_VRAM[normalized]

                # Check if this model has multiple VRAM variants in benchmarks
                # Examples: GTX 1060 (3GB/6GB), RX 580 (4GB/8GB), RTX 3080 (10GB/12GB) - has variants
                # ARC A750 (only 8GB), RX 6600 (only 8GB) - single variant
                has_multiple_variants = False
                for benchmark_model in SAMPLE_BENCHMARKS:
                    # Check if there are other VRAM variants (e.g., "GTX 1060 3GB", "GTX 1060 6GB")
                    if benchmark_model.startswith(normalized + " ") and "GB" in benchmark_model:
                        # Found a VRAM variant different from expected
                        variant_vram_match = re.search(r'(\d{1,2})GB', benchmark_model)
                        if variant_vram_match:
                            variant_vram = int(variant_vram_match.group(1))
                            if variant_vram != expected_vram:
                                has_multiple_variants = True
                                break

                if has_multiple_variants:
                    # Model has multiple VRAM variants - REJECT (must specify VRAM)
                    logger.warning(f"Missing VRAM for multi-variant model: {normalized} (has multiple VRAM options)")
                    self._last_rejection_reason = f"Липсващ VRAM: Моделът '{normalized}' има няколко VRAM варианта - трябва да се посочи точният VRAM"
                    self._last_rejected_model = normalized  # Save base model for rejected listings
                    return None
                else:
                    # Model has single VRAM variant - auto-add default
                    vram_str = f"{expected_vram}GB"
                    model_with_vram = f"{normalized} {vram_str}"
                    logger.debug(f"Auto-adding single VRAM variant: {normalized} -> {model_with_vram}")
            else:
                # Model not in GPU_VRAM dictionary - REJECT (cannot determine VRAM)
                logger.warning(f"Cannot determine VRAM for model: {normalized} (not in GPU_VRAM specs)")
                self._last_rejection_reason = f"Липсващ VRAM: Не може да се определи VRAM за модел '{normalized}'"
                self._last_rejected_model = normalized  # Save base model for rejected listings
                return None

        # NORMALIZE: Apply special case model name mappings
        # Some models are sold under unofficial names but should map to official variants
        model_with_vram = self._normalize_special_cases(model_with_vram)

        # VALIDATE: Check if model exists in known GPUs
        # Try with VRAM first, then without
        if self._is_valid_gpu_model(model_with_vram):
            # Clear any rejection reason from validation checks
            self._last_rejection_reason = None
            self._last_rejected_model = None
            return model_with_vram
        elif self._is_valid_gpu_model(normalized):
            # Model without VRAM is valid, but model+VRAM is not
            # This means VRAM variant is not in our database
            # Return model with VRAM anyway to track different variants
            # Check if model_with_vram has VRAM (either extracted or auto-added)
            if model_with_vram != normalized:  # model_with_vram has VRAM added
                logger.debug(f"Model {model_with_vram} not in database, but base model {normalized} is valid")
                # Clear any rejection reason - model is valid
                self._last_rejection_reason = None
                self._last_rejected_model = None
                return model_with_vram
            # Clear rejection reason
            self._last_rejection_reason = None
            self._last_rejected_model = None
            return normalized
        else:
            logger.debug(f"Rejected invalid GPU model: {normalized} (from title: {title})")
            self._last_rejection_reason = f"Invalid/unknown GPU model: {normalized}"
            self._last_rejected_model = normalized  # Save base model for rejected listings
            return None

    def _is_valid_gpu_model(self, model: str) -> bool:
        """
        Validates if GPU model exists in known benchmarks or VRAM specs

        Args:
            model: Normalized GPU model name (e.g., "GTX 1080", "RX 6600 XT")

        Returns:
            True if model is valid, False if it's a typo (e.g., "GTX 1018")
        """
        from core.filters import normalize_model_name

        # Normalize model for comparison
        model_normalized = normalize_model_name(model)

        # Check against benchmark data (most comprehensive list)
        # Need to normalize benchmark keys for case-insensitive comparison
        for benchmark_model in SAMPLE_BENCHMARKS:
            if normalize_model_name(benchmark_model) == model_normalized:
                return True

        # Check against VRAM specs (alternative source)
        for vram_model in GPU_VRAM:
            if normalize_model_name(vram_model) == model_normalized:
                return True

        # Fuzzy matching for common typos
        # "GTX 1018" -> suggest "GTX 1080" (closest match)
        for known_model in SAMPLE_BENCHMARKS.keys():
            # Check if only 1-2 characters differ (likely typo)
            if self._is_likely_typo(model, known_model):
                logger.info(f"Typo detected: '{model}' -> probably '{known_model}' (rejected)")
                self._last_rejection_reason = f"Invalid GPU model (typo): '{model}' → likely '{known_model}'"
                self._last_rejected_model = model  # Save the typo model for rejected listings
                return False

        # Model not found in database at all
        self._last_rejection_reason = f"Unknown GPU model: '{model}'"
        self._last_rejected_model = model  # Save the unknown model for rejected listings
        return False

    def _is_likely_typo(self, model: str, known_model: str) -> bool:
        """
        Check if model is a likely typo of known_model

        Examples of real typos:
        - "GTX 1018" vs "GTX 1080" (transposition)
        - "RTX 409" vs "RTX 4090" (missing digit)

        Examples of DIFFERENT models (NOT typos):
        - "GTX 1080" vs "GTX 1060" (different model numbers)
        - "RTX 3080" vs "RTX 3090" (different tier)
        """
        # Extract GPU brand and model number
        # GTX 1080 8GB -> brand: GTX, number: 1080
        # RTX 3090 24GB -> brand: RTX, number: 3090

        def extract_brand_and_number(m: str) -> tuple:
            """Extract brand (GTX/RTX/RX) and model number"""
            import re
            match = re.search(r'(GTX|RTX|RX|ARC)\s*(\d{3,4})', m.upper())
            if match:
                return match.group(1), match.group(2)
            return None, None

        brand1, num1 = extract_brand_and_number(model)
        brand2, num2 = extract_brand_and_number(known_model)

        # Must have same brand
        if brand1 != brand2 or not brand1:
            return False

        # If model numbers are different (e.g., 1080 vs 1060), NOT a typo
        if num1 != num2:
            # Different model numbers = different GPUs
            # (RX 6700 vs RX 7600, GTX 1080 vs GTX 1060, etc.)
            return False

        # Same brand and model number, check VRAM differences
        # "GTX 1080 8GB" vs "GTX 1080 10GB" -> NOT a typo, different VRAM variants
        if "GB" in model and "GB" in known_model:
            vram1 = re.search(r'(\d{1,2})GB', model)
            vram2 = re.search(r'(\d{1,2})GB', known_model)
            if vram1 and vram2 and vram1.group(1) != vram2.group(1):
                # Different VRAM -> different variants, not typo
                return False

        # Same brand, same model number, check overall string similarity
        if len(model) != len(known_model):
            return False

        # Count differing characters (excluding spaces)
        diffs = sum(1 for a, b in zip(model, known_model) if a != b)

        # If only 1-2 chars differ (after all checks above), likely a typo
        return 1 <= diffs <= 2

    def _normalize_special_cases(self, model: str) -> str:
        """
        Normalize special case model names to their official variants

        Examples:
        - "RTX 4070 TI 16GB" → "RTX 4070 TI SUPER 16GB" (16GB variant is SUPER)
        - "RTX 4070 TI 12GB" → "RTX 4070 TI 12GB" (12GB is original, no change)

        Args:
            model: GPU model name (e.g., "RTX 4070 TI 16GB")

        Returns:
            Normalized model name with official variant naming
        """
        # RTX 4070 Ti 16GB is actually the SUPER variant
        if model == "RTX 4070 TI 16GB":
            logger.debug(f"Normalizing {model} → RTX 4070 TI SUPER 16GB")
            return "RTX 4070 TI SUPER 16GB"

        # Add more special cases here as needed

        return model

    def _is_valid_vram_for_model(self, model: str, vram: str) -> bool:
        """
        Validates if extracted VRAM is correct for the GPU model
        Prevents issues like "GTX 1650 32GB" (likely system RAM confusion)

        Args:
            model: Normalized GPU model name (e.g., "GTX 1650", "RTX 3060")
            vram: Extracted VRAM string (e.g., "8GB", "12GB")

        Returns:
            True if VRAM is valid for this model, False otherwise
        """
        # Extract numeric VRAM value
        try:
            vram_value = int(vram.replace("GB", "").strip())
        except (ValueError, AttributeError):
            logger.debug(f"Could not parse VRAM value: {vram}")
            return True  # If we can't parse, allow it (benefit of the doubt)

        # STEP 1: Check if model+VRAM exists in SAMPLE_BENCHMARKS (most reliable)
        # Example: "RX 580 4GB", "RX 580 8GB" - both are valid variants
        model_with_vram = f"{model} {vram}"
        if model_with_vram in SAMPLE_BENCHMARKS:
            logger.debug(f"✅ {model_with_vram} found in benchmarks - valid VRAM variant")
            return True

        # STEP 2: Check GPU_VRAM dictionary for typical VRAM size
        if model in GPU_VRAM:
            expected_vram = GPU_VRAM[model]

            # Allow exact match
            if vram_value == expected_vram:
                return True

            # Don't immediately reject - check if it's a known variant
            # Check SAMPLE_BENCHMARKS for other VRAM variants of this model
            # Example: RX 580 expects 8GB, but "RX 580 4GB" exists in benchmarks
            for benchmark_model in SAMPLE_BENCHMARKS:
                if benchmark_model.startswith(model + " ") and vram in benchmark_model:
                    logger.debug(f"✅ {model_with_vram} is a known variant in benchmarks")
                    return True

            # VRAM mismatch and no variant found - likely system RAM confusion
            logger.debug(f"❌ VRAM mismatch: {model} typically {expected_vram}GB, found {vram_value}GB (not a known variant)")
            return False

        # Model not in GPU_VRAM dictionary - allow it (we might not have all models)
        # But log for tracking
        logger.debug(f"Model {model} not in GPU_VRAM specs, allowing VRAM {vram}")
        return True

    def _is_redundant_vram(self, model: str, vram: str) -> bool:
        """
        Check if VRAM specification is redundant.

        NOTE: Always returns False to keep VRAM info for all models.
        This ensures different VRAM variants (e.g., RTX 3060 8GB vs 12GB)
        are stored as separate entries in the database.

        Args:
            model: Base GPU model (e.g., "GTX 1080", "GTX 1060")
            vram: VRAM string (e.g., "8GB", "6GB")

        Returns:
            Always False - VRAM is never considered redundant
        """
        # Always keep VRAM information to differentiate variants
        return False

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

        from core.filters import normalize_model_name

        for model, price in min_prices.items():
            norm_model = normalize_model_name(model).replace(" ", "")

            # First pass: exact match only (prevents RTX 2070 matching RTX 2070 SUPER)
            matched = False
            for b_model, fps in self.gpu_benchmarks.items():
                norm_bench = normalize_model_name(b_model).replace(" ", "")
                if norm_model == norm_bench:
                    results.append((model, fps, price, fps / price))
                    matched = True
                    break

            # Second pass: substring match only if no exact match found
            if not matched:
                for b_model, fps in self.gpu_benchmarks.items():
                    norm_bench = normalize_model_name(b_model).replace(" ", "")
                    if norm_model in norm_bench or norm_bench in norm_model:
                        results.append((model, fps, price, fps / price))
                        break

        return sorted(results, key=lambda x: x[3], reverse=True)

    def get_rejected_listings(self) -> List[Dict]:
        """
        Връща списък с всички отхвърлени обяви с причини за отхвърляне

        Returns:
            List of dicts with: title, price, url, model, reason, category
        """
        return self._rejected_listings

    def get_rejection_summary(self) -> Dict[str, int]:
        """
        Връща обобщена статистика за отхвърлените обяви по категория

        Returns:
            Dict with category -> count
        """
        return self._filter_stats


# ================= BENCHMARKS =================
# Real FPS Benchmark Data - Desktop Gaming GPUs Only
# Source: HowManyFPS.com (January 2026)
# Resolution: 1080p Ultra settings
# Updated: 2026-01-02
#
# Note: Real FPS values from benchmark testing across multiple AAA games
# Data represents actual frame rates, not relative scores
# Values of 0.0 are pending manual data entry
# Total: 211 GPU models (100 filled, 111 pending)
SAMPLE_BENCHMARKS = GPU_FPS_BENCHMARKS.copy()

# Legacy relative scores system preserved in data/gpu_benchmarks.py
# Use GPU_FPS_BENCHMARKS for real FPS, or gpu_benchmarks.py for relative scores

# Original SAMPLE_BENCHMARKS (relative scores - DEPRECATED, kept for reference)
# These are now replaced with real FPS values above
# RTX 5090 was baseline = 100, now it's 238 FPS
_DEPRECATED_RELATIVE_SCORES = {
    # NVIDIA RTX 50-series
    "RTX 5090": 100.0,
    "RTX 5080": 66.0,
    "RTX 5070 TI": 52.0,
    "RTX 5070": 45.0,
    "RTX 5060 TI": 32.0,
    "RTX 5060": 27.0,

    # NVIDIA RTX 40-series
    "RTX 4090": 69.0,
    "RTX 4080 SUPER": 59.0,
    "RTX 4080": 57.0,
    "RTX 4070 TI SUPER": 50.0,
    "RTX 4070 TI": 47.0,
    "RTX 4070 SUPER": 43.0,
    "RTX 4070": 40.0,
    "RTX 4060 TI 16 GB": 29.0,
    "RTX 4060 TI 8 GB": 29.0,
    "RTX 4060": 24.0,

    # NVIDIA RTX 30-series
    "RTX 3090 TI": 62.0,
    "RTX 3090": 59.0,
    "RTX 3080 TI": 55.0,
    "RTX 3080 12GB": 53.0,
    "RTX 3080": 52.0,
    "RTX 3070 TI": 41.0,
    "RTX 3070": 39.0,
    "RTX 3060 TI": 34.0,
    "RTX 3060 12GB": 28.0,
    "RTX 3060": 28.0,
    "RTX 3050 8GB": 17.0,
    "RTX 3050": 17.0,

    # NVIDIA RTX 20-series
    "RTX 2080 TI": 47.0,
    "RTX 2080 SUPER": 40.0,
    "RTX 2080": 38.0,
    "RTX 2070 SUPER": 36.0,
    "RTX 2070": 33.0,
    "RTX 2060 SUPER": 31.0,
    "RTX 2060 12GB": 30.0,
    "RTX 2060": 29.0,

    # NVIDIA GTX 16-series (Turing)
    "GTX 1660 TI": 24.0,
    "GTX 1660 SUPER": 23.0,
    "GTX 1660": 21.0,
    "GTX 1650 SUPER": 17.0,
    "GTX 1650 GDDR6": 15.0,
    "GTX 1650": 13.0,
    "GTX 1630": 9.0,

    # NVIDIA GTX 10-series (Pascal)
    "GTX 1080 TI": 37.0,
    "GTX 1080": 31.0,
    "GTX 1070 TI": 29.0,
    "GTX 1070": 26.0,
    "GTX 1060 6GB": 20.0,
    "GTX 1060 3GB": 18.0,
    "GTX 1050 TI": 12.0,
    "GTX 1050": 9.0,

    # NVIDIA GTX 900-series (Maxwell)
    "GTX 980 TI": 24.0,
    "GTX 980": 19.0,
    "GTX 970": 16.0,
    "GTX 960": 10.0,
    "GTX 950": 7.0,

    # NVIDIA GTX 700-series (Kepler)
    "GTX 780 TI": 15.0,
    "GTX 780": 13.0,
    "GTX 770": 11.0,
    "GTX 760": 8.0,
    "GTX 750 TI": 6.0,

    # AMD RX 7000-series (RDNA 3)
    "RX 7900 XTX": 61.0,
    "RX 7900 XT": 55.0,
    "RX 7900 GRE": 50.0,
    "RX 7800 XT": 45.0,
    "RX 7700 XT": 38.0,
    "RX 7600 XT": 26.0,
    "RX 7600 8GB": 22.0,
    "RX 7600": 22.0,

    # AMD RX 6000-series (RDNA 2)
    "RX 6950 XT": 59.0,
    "RX 6900 XT": 57.0,
    "RX 6800 XT": 54.0,
    "RX 6800": 48.0,
    "RX 6750 XT": 40.0,
    "RX 6700 XT": 37.0,
    "RX 6700": 33.0,
    "RX 6650 XT": 31.0,
    "RX 6600 XT 8GB": 29.0,
    "RX 6600 XT": 29.0,
    "RX 6600": 24.0,
    "RX 6500 XT": 14.0,
    "RX 6400": 9.0,
    "RX 6300": 5.0,

    # AMD RX 500-series (Polaris)
    "RX 5700 XT": 33.0,
    "RX 5700": 30.0,
    "RX 5600 XT": 29.0,
    "RX 5600": 26.0,
    "RX 590": 21.0,
    "RX 5500 XT 8GB": 19.0,
    "RX 5500 XT 4GB": 18.0,
    "RX 580 8GB": 18.0,
    "RX 5500": 17.0,
    "RX 580 4GB": 17.0,
    "RX 570 8GB": 16.0,
    "RX 570 4GB": 15.0,
    "RX 560": 9.0,
    "RX 550": 5.0,

    # AMD RX 400-series (Polaris)
    "RX 480 8GB": 18.0,
    "RX 480 4GB": 17.0,
    "RX 470": 15.0,
    "RX 460": 8.0,

    # AMD RX Vega series
    "RX VEGA 64 LIQUID": 30.0,
    "RX VEGA 64": 28.0,
    "RX VEGA 56": 25.0,

    # AMD Radeon VII
    "RADEON VII": 35.0,

    # AMD RX 300-series
    "R9 FURY X": 22.0,
    "R9 FURY": 20.0,
    "R9 NANO": 19.0,
    "R9 390X": 13.0,
    "R9 390": 12.0,
    "R9 380X": 10.0,
    "R9 380": 9.0,

    # Intel Arc (Alchemist)
    "ARC A770 16GB": 36.0,
    "ARC A770": 36.0,
    "ARC A770 8GB": 35.0,
    "ARC B580": 33.0,
    "ARC A750": 31.0,
    "ARC A580": 25.0,
    "ARC A380": 13.0,
    "ARC A310": 7.0,

    # Other budget cards
    "GT 1030": 4.0,
}  # End of deprecated relative scores


GPU_VRAM = {
    # NVIDIA GeForce RTX 50-series (Blackwell)
    "RTX 5090": 32,
    "RTX 5080": 16,
    "RTX 5070 TI": 16,
    "RTX 5070": 12,
    "RTX 5060 TI 16GB": 16,
    "RTX 5060 TI 12GB": 12,
    "RTX 5060 TI 8GB": 8,
    "RTX 5060 TI": 8,
    "RTX 5060": 8,

    # NVIDIA GeForce RTX 40-series (Ada Lovelace)
    "RTX 4090": 24,
    "RTX 4080 SUPER": 16,
    "RTX 4080": 16,
    "RTX 4070 TI SUPER": 16,
    "RTX 4070 TI 16GB": 16,  # RTX 4070 Ti SUPER variant
    "RTX 4070 TI 12GB": 12,  # Original RTX 4070 Ti
    "RTX 4070 TI": 12,
    "RTX 4070 SUPER": 12,
    "RTX 4070": 12,
    "RTX 4060 TI 16GB": 16,
    "RTX 4060 TI 8GB": 8,
    "RTX 4060 TI": 8,
    "RTX 4060": 8,

    # NVIDIA GeForce RTX 30-series (Ampere)
    "RTX 3090 TI": 24,
    "RTX 3090": 24,
    "RTX 3080 TI 20GB": 20,
    "RTX 3080 TI 12GB": 12,
    "RTX 3080 TI": 12,
    "RTX 3080 12GB": 12,
    "RTX 3080 10GB": 10,
    "RTX 3080": 10,
    "RTX 3070 TI": 8,
    "RTX 3070": 8,
    "RTX 3060 TI GDDR6X": 8,
    "RTX 3060 TI": 8,
    "RTX 3060 12GB": 12,
    "RTX 3060 8GB": 8,
    "RTX 3060": 12,
    "RTX 3050 8GB": 8,
    "RTX 3050 6GB": 6,
    "RTX 3050": 8,

    # NVIDIA GeForce RTX 20-series (Turing)
    "RTX 2080 TI": 11,
    "RTX 2080 SUPER": 8,
    "RTX 2080": 8,
    "RTX 2070 SUPER": 8,
    "RTX 2070": 8,
    "RTX 2060 SUPER": 8,
    "RTX 2060 12GB": 12,
    "RTX 2060 6GB": 6,
    "RTX 2060": 6,

    # NVIDIA GeForce GTX 10/16-series (Pascal/Turing)
    "GTX 1660 SUPER": 6,
    "GTX 1660 TI": 6,
    "GTX 1660": 6,
    "GTX 1650 SUPER": 4,
    "GTX 1650": 4,
    "GTX 1630": 4,
    "GTX 1080 TI": 11,
    "GTX 1080": 8,
    "GTX 1070 TI": 8,
    "GTX 1070": 8,
    "GTX 1060 6GB": 6,
    "GTX 1060 3GB": 3,
    "GTX 1060": 6,  # Default to 6GB variant (most common), but has 3GB too
    "GTX 1050 TI": 4,
    "GTX 1050": 2,

    # NVIDIA GTX 900-series (Maxwell)
    "GTX 980 TI": 6,
    "GTX 980": 4,
    "GTX 970": 4,
    "GTX 960": 2,
    "GTX 950": 2,

    # AMD Radeon RX 9000-series (RDNA 4)
    "RX 9070 XT": 16,
    "RX 9070": 12,
    "RX 9070 GRE": 12,
    "RX 9060 XT 16GB": 16,
    "RX 9060 XT": 16,
    "RX 9060": 8,

    # AMD Radeon RX 7000-series (RDNA 3)
    "RX 7900 XTX": 24,
    "RX 7900 XT": 20,
    "RX 7900 GRE": 16,
    "RX 7800 XT": 16,
    "RX 7700 XT": 12,
    "RX 7650 GRE": 8,
    "RX 7600 XT": 16,
    "RX 7600": 8,
    "RX 7400": 4,

    # AMD Radeon RX 6000-series (RDNA 2)
    "RX 6950 XT": 16,
    "RX 6900 XT": 16,
    "RX 6800 XT": 16,
    "RX 6800": 16,
    "RX 6750 XT": 12,
    "RX 6750 GRE 12GB": 12,
    "RX 6750 GRE 10GB": 10,
    "RX 6700 XT": 12,
    "RX 6700": 10,
    "RX 6650 XT": 8,
    "RX 6600 XT": 8,
    "RX 6600": 8,
    "RX 6600 LE": 8,
    "RX 6500 XT": 4,
    "RX 6400": 4,

    # AMD Radeon RX 5000-series (RDNA 1)
    "RX 5700 XT": 8,
    "RX 5700": 8,
    "RX 5600 XT": 6,
    "RX 5500 XT 8GB": 8,
    "RX 5500 XT 4GB": 4,
    "RX 5500 XT": 8,
    "RX 5500": 4,

    # AMD Radeon RX 500-series (Polaris)
    "RX 590": 8,
    "RX 580 8GB": 8,
    "RX 580 4GB": 4,
    "RX 580": 8,
    "RX 570 8GB": 8,
    "RX 570 4GB": 4,
    "RX 570": 8,  # Default to 8GB variant (most common), but has 4GB too
    "RX 560": 4,
    "RX 550": 2,

    # AMD Radeon RX 400-series (Polaris)
    "RX 490": 8,
    "RX 480 8GB": 8,
    "RX 480 4GB": 4,
    "RX 480": 8,
    "RX 470 8GB": 8,
    "RX 470 4GB": 4,
    "RX 470": 4,
    "RX 460 4GB": 4,
    "RX 460 2GB": 2,
    "RX 460": 4,

    # AMD Radeon Vega
    "RADEON VII": 16,
    "RX VEGA 64": 8,
    "RX VEGA 56": 8,

    # Intel Arc (Alchemist & Battlemage)
    "ARC B580": 12,
    "ARC B570": 10,
    "ARC A770 16GB": 16,
    "ARC A770 8GB": 8,
    "ARC A770": 16,
    "ARC A750": 8,
    "ARC A580": 8,
    "ARC A380": 6,
    "ARC A350": 4,
    "ARC A310": 4,

    # Titan cards
    "TITAN RTX": 24,
    "TITAN V": 12,
    "TITAN XP": 12,

    # Budget cards
    "GT 1030": 2,
}

