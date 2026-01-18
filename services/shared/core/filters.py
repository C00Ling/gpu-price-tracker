"""
Enhanced quality filters for GPU listings - Post-Processing Statistical Filtering

This module implements post-processing filtering:
1. SCRAPE: Collect ALL data without filtering
2. POST-PROCESS: Apply statistical outlier detection after scraping is complete

Advantages:
- No warm-up phase needed - we have full statistics before filtering
- More accurate outlier detection with complete dataset
- Easier to debug and tune thresholds
"""
from typing import Tuple, Optional, List, Dict, Any
import re
from core.logging import get_logger
from core.config import config

logger = get_logger("filters")

# Separate keyword lists for different rejection categories

# Mining-related keywords (separate category)
MINING_KEYWORDS = [
    "майнинг", "mining", "burnout", "mining rig", "копана", "ферма", "mining farm",
    "от ферма", "от майнинг", "за майнинг", "копаене", "miner", "майнър",
    "crypto", "крипто", "eth", "ethereum", "bitcoin",
]

# Cooling parts / fans (separate category)
COOLING_KEYWORDS = [
    # Fans
    "вентилатор", "вентилатори", "fan", "fans",
    # Coolers
    "охлаждане", "охладител", "cooler", "cooling",
    # Heatsinks
    "радиатор", "heatsink", "thermal pad", "термопад", "термопадове",
    # Backplates
    "backplate", "бекплейт",
]

# Water cooling parts (separate category)
WATER_COOLING_KEYWORDS = [
    "water block", "waterblock", "воден блок", "водно охлаждане", "водно блок",
    "liquid cooling", "ekwb", "ek-wb", "ek water",
]

# Defective/broken items (general blacklist)
BLACKLIST_KEYWORDS = [
    # Bulgarian - defective
    "заектури", "за част", "част за", "части за", "счупена", "не работи", "повредена", "дефект",
    "за ремонт", "ремонтен", "ремонтен комплект", "комплект за ремонт",
    "артефакти", "черен екран", "не дава екран", "не стартира", "изгоря",
    "развален", "нетествана", "проблем", "не е тествана", "дефектна", "не функционира", "изправни",
    "няма сигнал", "без сигнал", "не дава сигнал",

    # English - defective
    "broken", "damaged", "faulty", "defective", "not working", "for parts",
    "parts only", "part for", "for part", "as is", "repair", "artifacts", "black screen",
    "burnt", "dead", "fried", "doa", "no signal", "no display",

    # Other non-GPU items
    "мишка", "mouse",
]

# Suspicious keywords that trigger statistical filtering (not immediate blacklist)
# These words often appear in scams but can also be legitimate
SUSPICIOUS_KEYWORDS = [
    # Bulgarian
    "подаръци", "подарък", "подаръци+", "подаръци !",
    "срочно", "бързо", "спешно", "много спешно",
    "намалена", "намаление", "промоция", "разпродажба",
    "последна цена", "на цената на", "цената е крайна",
    "договаряне", "договор", "на място",

    # English
    "urgent", "asap", "quickly", "gift", "gifts", "bonus",
    "sale", "discount", "promo", "promotion", "deal",
    "final price", "best price", "lowest price",
]

# Keywords indicating full computer listings (not just GPU)
COMPUTER_KEYWORDS = [
    # Bulgarian
    "компютър", "компютр", "кейс", "кутия", "система", "конфигурация",
    "геймърски пк", "офисен пк", "настолен компютър", "десктоп",
    "лаптоп", "преносим", "ноутбук", "нотбук",

    # English
    "desktop", "gaming pc", "office pc", "computer", "system", "build",
    "configuration", "full pc", "complete pc", "tower",
    "laptop", "notebook", "portable",

    # Multiple components (indicates full system)
    # Intel CPUs - various formats (i7 , i7-, i7-12700, etc.)
    "i3 ", "i3-", "i5 ", "i5-", "i7 ", "i7-", "i9 ", "i9-",
    # AMD CPUs - full and abbreviated forms
    "ryzen 3", "ryzen 5", "ryzen 7", "ryzen 9",
    "r3 ", "r5 ", "r7 ", "r9 ",  # Abbreviated (R5 5600G, R7 5800X, etc.)
    # Component combinations
    "+ cpu", "+ ram", "+ процесор", "+ ssd", "+ hdd",
    # Display sizes (laptops)
    "15.6\"", "15.6'", "15,6\"", "15,6'", "17.3\"", "17.3'", "17,3\"", "17,3'",
    "14\"", "14'", "13.3\"", "13.3'", "13,3\"", "13,3'",
    # Screen specs (laptops)
    "fhd 144hz", "fhd 165hz", "fhd 240hz", "fhd 360hz", "qhd 165hz",
    # Laptop model indicators
    "gp76", "gp66", "ge76", "ge66", "gl66", "gl76",  # MSI gaming laptops
    "rog strix", "tuf gaming", "zephyrus",  # ASUS gaming laptops
    "legion", "ideapad",  # Lenovo laptops
    "omen", "victus", "pavilion gaming",  # HP gaming laptops
    "predator", "nitro",  # Acer gaming laptops
    "alienware", "inspiron", "xps",  # Dell laptops
]

# Outlier detection thresholds
OUTLIER_THRESHOLD_LOW = 0.40   # 40% от медианата (балансирано филтриране на твърде ниски цени)
OUTLIER_THRESHOLD_HIGH = 3.0   # 300% от медианата (DISABLED - не се използва)

# Minimum sample size за статистика
MIN_SAMPLE_SIZE = 3  # Минимум 3 обяви за да приложим статистика (БЕЗ warm-up фаза)
ADAPTIVE_WARMUP_SIZE = 5  # След 5 обяви използваме пълна статистическа филтрация


# Model corrections for incomplete/ambiguous names and non-existent variants
MODEL_CORRECTIONS = {
    # AMD RX 7000-series - fix incomplete model names
    "RX 7900": "RX 7900 XT",      # Default to XT (most common)
    "RX 7800": "RX 7800 XT",      # Only XT variant exists
    "RX 7700": "RX 7700 XT",      # Only XT variant exists
    "RX 7600": "RX 7600",         # Non-XT is the base model

    # AMD RX 6000-series - fix incomplete model names
    "RX 6950": "RX 6950 XT",      # Only XT variant exists
    "RX 6900": "RX 6900 XT",      # Only XT variant exists
    "RX 6800": "RX 6800",         # Non-XT is valid
    "RX 6700": "RX 6700 XT",      # XT is more common
    "RX 6600": "RX 6600",         # Non-XT is the base model
    "RX 6500": "RX 6500 XT",      # Only XT variant exists

    # AMD RX 5000-series
    "RX 5700": "RX 5700 XT",      # XT is more common
    "RX 5600": "RX 5600 XT",      # Only XT variant exists
    "RX 5500": "RX 5500 XT",      # Only XT variant exists

    # NVIDIA RTX 40-series - removed auto-corrections to allow precise VRAM matching
    # Now with VRAM extraction, we want to keep exact model names

    # NVIDIA RTX 30-series - removed auto-corrections to allow precise VRAM matching
    # "RTX 3060" and "RTX 3060 TI" are different cards

    # NVIDIA RTX 20-series - removed auto-corrections
    # RTX 2080/2070/2060 and their SUPER variants are DIFFERENT cards with different performance!
    # RTX 2070: 79 FPS vs RTX 2070 SUPER: 82 FPS - не бива да се смесват

    # Common typos and errors
    "GTX 1060 SUPER": "GTX 1660 SUPER",  # Common confusion
    "GTX 1600": "GTX 1650 SUPER",        # Typo
    "RTX 2260 SUPER": "RTX 2060 SUPER",  # Typo
    "RX 1650": "GTX 1650 SUPER",         # Brand confusion (AMD → NVIDIA)

    # ===================================================================
    # Non-existent GPU models - normalize to real equivalents
    # These variants were never released but sellers often list them incorrectly
    # ===================================================================

    # NVIDIA GTX 10-series - no SUPER variants exist (SUPER only in GTX 16-series)
    "GTX 1080 SUPER": "GTX 1080",    # GTX 1080 SUPER doesn't exist → GTX 1080
    "GTX 1070 SUPER": "GTX 1070",    # GTX 1070 SUPER doesn't exist → GTX 1070
    "GTX 1060 3GB SUPER": "GTX 1060 3GB",  # No SUPER variant
    "GTX 1060 6GB SUPER": "GTX 1060 6GB",  # No SUPER variant
    "GTX 1050 SUPER": "GTX 1050",    # GTX 1050 SUPER doesn't exist → GTX 1050

    # NVIDIA RTX 30-series - no SUPER variants (SUPER only in 20-series and 40-series)
    "RTX 3090 SUPER": "RTX 3090",
    "RTX 3090 TI SUPER": "RTX 3090 TI",
    "RTX 3080 SUPER": "RTX 3080",
    "RTX 3080 TI SUPER": "RTX 3080 TI",
    "RTX 3080 12GB SUPER": "RTX 3080 12GB",
    "RTX 3070 SUPER": "RTX 3070",
    "RTX 3070 TI SUPER": "RTX 3070 TI",
    "RTX 3060 SUPER": "RTX 3060",
    "RTX 3060 TI SUPER": "RTX 3060 TI",
    "RTX 3060 12GB SUPER": "RTX 3060 12GB",
    "RTX 3050 SUPER": "RTX 3050",
    "RTX 3050 8GB SUPER": "RTX 3050 8GB",

    # NVIDIA RTX 20-series - only 2060/2070/2080 have SUPER variants
    "RTX 2080 TI SUPER": "RTX 2080 TI",  # RTX 2080 TI exists, but no SUPER variant
    "RTX 2090": "RTX 2080 TI",           # RTX 2090 doesn't exist, likely means 2080 TI
    "RTX 2090 SUPER": "RTX 2080 TI",
    "RTX 2090 TI": "RTX 2080 TI",
    "RTX 2050": "RTX 2060",              # RTX 2050 doesn't exist, likely means 2060
    "RTX 2050 SUPER": "RTX 2060 SUPER",

    # NVIDIA RTX 40-series - limited SUPER variants
    "RTX 4090 SUPER": "RTX 4090",        # RTX 4090 doesn't have SUPER variant
    "RTX 4090 TI": "RTX 4090",           # RTX 4090 TI doesn't exist
    "RTX 4060 SUPER": "RTX 4060",        # Only RTX 4060 TI exists, not 4060 SUPER

    # NVIDIA GTX 16-series - only 1650 and 1660 have SUPER
    "GTX 1630 SUPER": "GTX 1650 SUPER",  # Likely confusion
    "GTX 1640 SUPER": "GTX 1650 SUPER",  # Likely confusion

    # AMD RX cards - no SUPER variants (AMD uses XT/XTX nomenclature)
    "RX 7900 SUPER": "RX 7900 XT",
    "RX 7800 SUPER": "RX 7800 XT",
    "RX 7700 SUPER": "RX 7700 XT",
    "RX 7600 SUPER": "RX 7600",
    "RX 6900 SUPER": "RX 6900 XT",
    "RX 6800 SUPER": "RX 6800 XT",
    "RX 6700 SUPER": "RX 6700 XT",
    "RX 6600 SUPER": "RX 6600 XT",
    "RX 5700 SUPER": "RX 5700 XT",
    "RX 5600 SUPER": "RX 5600 XT",
}


def normalize_model_name(model: str) -> str:
    """
    Normalize GPU model name for consistency

    Examples:
        RTX3060TI -> RTX 3060 TI
        RTX 3060TI -> RTX 3060 TI
        RX6600XT -> RX 6600 XT
        VEGA56 -> VEGA 56
        gtx 1660ti -> GTX 1660 TI
        GTX 1060 6GB -> GTX 1060 6GB
        RX 7900 -> RX 7900 XT (autocorrect incomplete names)
        AMD Radeon RX 7900 GRE -> RX 7900 GRE
    """
    if not model:
        return model

    # Convert to uppercase
    model = model.upper().strip()

    # Remove brand prefixes (AMD, NVIDIA, GEFORCE, RADEON, INTEL) - with optional spaces
    # This must run BEFORE removing all spaces
    model = re.sub(r'^(AMD|NVIDIA|GEFORCE|RADEON|INTEL)\s+', '', model)

    # Remove "RADEON" if it appears after removing first prefix (e.g., "AMD RADEON RX")
    model = re.sub(r'^RADEON\s+', '', model)
    model = re.sub(r'^GEFORCE\s+', '', model)

    # Remove all remaining spaces
    model = model.replace(" ", "")

    # Add space after brand (RTX, GTX, RX, VEGA, ARC)
    model = re.sub(r'(RTX|GTX|RX|VEGA|ARC)(\d+)', r'\1 \2', model)

    # Special handling for Intel ARC (format: ARC A750, ARC B580)
    model = re.sub(r'ARC([AB])(\d{3})', r'ARC \1\2', model)

    # Add space before memory size (3GB, 6GB, 8GB, 12GB, 16GB, etc.) - FIRST
    # This must run before TI/SUPER/XT to handle cases like "TI16GB"
    model = re.sub(r'(\d{4})(\d{1,2}GB)$', r'\1 \2', model)  # e.g., 30603GB -> 3060 3GB
    model = re.sub(r'(\d{3})(\d{1,2}GB)$', r'\1 \2', model)  # e.g., 5808GB -> 580 8GB (AMD RX 580, RX 570, etc.)
    model = re.sub(r'([AB]\d{3})(\d{1,2}GB)$', r'\1 \2', model)  # e.g., A77016GB -> A770 16GB (Intel ARC)
    model = re.sub(r'(TI|SUPER|XT|XTX|GRE)(\d{1,2}GB)$', r'\1 \2', model)  # e.g., TI16GB -> TI 16GB

    # Normalize "S" suffix to "SUPER" (e.g., RTX2060S -> RTX2060SUPER)
    # Must be done BEFORE adding spaces
    model = re.sub(r'(\d{4})S\b', r'\1SUPER', model)

    # Add space before suffix (TI, SUPER, XT, XTX, GRE)
    model = re.sub(r'(\d+)(TI|SUPER|XT|XTX|GRE)', r'\1 \2', model)

    # Apply model corrections for incomplete/ambiguous names
    if model in MODEL_CORRECTIONS:
        corrected = MODEL_CORRECTIONS[model]
        logger.debug(f"Model correction: '{model}' → '{corrected}'")
        model = corrected

    return model


def is_suspicious_listing(
    title: str,
    price: float,
    gpu_model: str,
    dynamic_min_price: int = 0,
    all_prices_for_model: Optional[List[float]] = None
) -> Tuple[bool, str]:
    """
    DEPRECATED: This function is no longer used for real-time filtering.

    Filtering now happens in post-processing via filter_scraped_data().
    This function is kept for backwards compatibility only.

    Args:
        title: Listing title
        price: Price in BGN
        gpu_model: GPU model name
        dynamic_min_price: Deprecated (kept for backwards compatibility)
        all_prices_for_model: Deprecated (kept for backwards compatibility)

    Returns:
        Tuple of (is_suspicious: bool, reason: str)
    """
    title_lower = title.lower()

    # Normalize the model for comparison
    gpu_model = normalize_model_name(gpu_model)

    # 1. Check for blacklisted keywords (ALWAYS APPLIED - HIGHEST PRIORITY)
    for keyword in BLACKLIST_KEYWORDS:
        if keyword.lower() in title_lower:
            return (True, f"Contains blacklisted keyword: '{keyword}'")

    # 2. Check for computer/full system listings (ALWAYS APPLIED)
    for keyword in COMPUTER_KEYWORDS:
        if keyword.lower() in title_lower:
            return (True, f"Full computer listing (not just GPU): '{keyword}'")

    # 3. Extremely low price check (ALWAYS APPLIED - universal red flag)
    if price < 50:
        return (True, f"Extremely low price: {price}лв (likely broken)")

    # 3. Title length check (ALWAYS APPLIED - low quality listings)
    if len(title) < 10:
        return (True, f"Title too short: '{title}'")

    # 4. ADAPTIVE Statistical outlier detection
    # Only apply if we have enough samples (warm-up phase complete)
    if all_prices_for_model and len(all_prices_for_model) >= ADAPTIVE_WARMUP_SIZE:
        import statistics

        median = statistics.median(all_prices_for_model)

        # Check if price is too low (outlier)
        low_threshold = median * OUTLIER_THRESHOLD_LOW
        if price < low_threshold:
            return (
                True,
                f"Statistical outlier: {price}лв < {low_threshold:.0f}лв "
                f"(30% of median {median:.0f}лв)"
            )

        # Check if price is too high (probably scam/wrong listing)
        high_threshold = median * OUTLIER_THRESHOLD_HIGH
        if price > high_threshold:
            return (
                True,
                f"Price too high: {price}лв > {high_threshold:.0f}лв "
                f"(300% of median {median:.0f}лв)"
            )

    # All checks passed
    return (False, "OK")


def calculate_statistics(prices: List[float]) -> Optional[Dict[str, Any]]:
    """
    Calculate statistics for a list of prices
    
    Args:
        prices: List of prices
    
    Returns:
        Dict with median, mean, std_dev, q1, q3, iqr
        None if not enough data
    """
    if not prices or len(prices) < 2:
        return None
    
    import statistics
    
    sorted_prices = sorted(prices)
    n = len(sorted_prices)
    
    stats = {
        'median': statistics.median(sorted_prices),
        'mean': statistics.mean(sorted_prices),
        'count': n,
    }
    
    # Standard deviation (if enough data)
    if n >= 2:
        stats['std_dev'] = statistics.stdev(sorted_prices)
    
    # Quartiles (if enough data)
    if n >= 4:
        stats['q1'] = sorted_prices[n // 4]
        stats['q3'] = sorted_prices[3 * n // 4]
        stats['iqr'] = stats['q3'] - stats['q1']
    
    return stats


def filter_scraped_data(raw_data: Dict[str, List]) -> tuple[Dict[str, List], Dict[str, int], List[Dict]]:
    """
    Post-processing filtering: филтрира scraped данни СЛЕД събирането им

    Предимства:
    - Имаме пълната статистика преди филтриране (няма warm-up фаза)
    - По-точно outlier detection
    - По-просто за debugging

    Args:
        raw_data: Речник {model: [items]} където items са dict{'price': float, 'url': str, 'title': str}

    Returns:
        Tuple of (filtered_data, filter_stats, rejected_listings)
        - filtered_data: Речник {model: [items]} само с валидни listings
        - filter_stats: Речник {reason: count} с статистика за филтриране
        - rejected_listings: List of rejected items with reasons
    """
    filtered_data = {}
    rejected_listings = []  # Track all rejected listings
    filter_stats = {
        'blacklist_keywords': 0,
        'full_computer': 0,
        'extremely_low_price': 0,
        'statistical_outlier_low': 0,
        'statistical_outlier_high': 0,
        'total_filtered': 0,
        'total_kept': 0,
    }

    for model, items in raw_data.items():
        if not items:
            continue

        valid_items = []
        for item in items:
            price = item['price']
            title = item.get('title', '')
            description = item.get('description', '')
            full_text = f"{title} {description}".lower()
            url = item.get('url', '')

            # Check for mining-related keywords (separate category)
            mining_found = False
            for keyword in MINING_KEYWORDS:
                if keyword.lower() in full_text:
                    filter_stats['blacklist_keywords'] += 1
                    filter_stats['total_filtered'] += 1
                    reason = f"Mining related: '{keyword}'"
                    rejected_listings.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'model': model,
                        'reason': reason,
                        'category': '⛏️ Mining Related'
                    })
                    logger.debug(f"Filtered {model} @ {price}лв: {reason}")
                    mining_found = True
                    break
            if mining_found:
                continue

            # Check for water cooling parts (separate category)
            water_cooling_found = False
            for keyword in WATER_COOLING_KEYWORDS:
                if keyword.lower() in full_text:
                    filter_stats['blacklist_keywords'] += 1
                    filter_stats['total_filtered'] += 1
                    reason = f"Water cooling parts: '{keyword}'"
                    rejected_listings.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'model': model,
                        'reason': reason,
                        'category': '💧 Water Cooling Parts'
                    })
                    logger.debug(f"Filtered {model} @ {price}лв: {reason}")
                    water_cooling_found = True
                    break
            if water_cooling_found:
                continue

            # Check for cooling/fan parts (separate category)
            cooling_found = False
            for keyword in COOLING_KEYWORDS:
                if keyword.lower() in full_text:
                    filter_stats['blacklist_keywords'] += 1
                    filter_stats['total_filtered'] += 1
                    reason = f"Cooling/fan parts: '{keyword}'"
                    rejected_listings.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'model': model,
                        'reason': reason,
                        'category': '🌀 Cooling Parts'
                    })
                    logger.debug(f"Filtered {model} @ {price}лв: {reason}")
                    cooling_found = True
                    break
            if cooling_found:
                continue

            # Check for blacklisted keywords (defective/broken items)
            blacklisted = False
            for keyword in BLACKLIST_KEYWORDS:
                if keyword.lower() in full_text:
                    filter_stats['blacklist_keywords'] += 1
                    filter_stats['total_filtered'] += 1
                    reason = f"Blacklisted keyword: '{keyword}'"
                    rejected_listings.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'model': model,
                        'reason': reason,
                        'category': '🚫 Blacklisted Keywords'
                    })
                    logger.debug(f"Filtered {model} @ {price}лв: {reason}")
                    blacklisted = True
                    break
            if blacklisted:
                continue

            # Check for full computer listings in both title AND description (not just GPU)
            is_computer = False
            for keyword in COMPUTER_KEYWORDS:
                if keyword.lower() in full_text:
                    filter_stats['full_computer'] += 1
                    filter_stats['total_filtered'] += 1
                    reason = f"Full computer listing: '{keyword}'"
                    rejected_listings.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'model': model,
                        'reason': reason,
                        'category': '💻 Full Computer/Laptop'
                    })
                    logger.debug(f"Filtered {model} @ {price}лв: {reason}")
                    is_computer = True
                    break
            if is_computer:
                continue

            # Statistical outlier detection - only for low prices
            # We need to collect all prices first, then filter
            valid_items.append(item)

        # Now apply statistical filtering if we have enough samples
        if valid_items and len(valid_items) >= MIN_SAMPLE_SIZE:
            import statistics

            prices = [item['price'] for item in valid_items]
            median = statistics.median(prices)
            low_threshold = median * OUTLIER_THRESHOLD_LOW

            # Filter out low price outliers - ONLY if listing has suspicious keywords
            final_items = []
            for item in valid_items:
                price = item['price']
                title = item.get('title', '')
                description = item.get('description', '')
                full_text_lower = f"{title} {description}".lower()

                # Check if title OR description contains any suspicious keyword
                suspicious_keyword_found = None
                for keyword in SUSPICIOUS_KEYWORDS:
                    if keyword.lower() in full_text_lower:
                        suspicious_keyword_found = keyword
                        break

                # Only filter if BOTH conditions are met:
                # 1. Price is suspiciously low
                # 2. Listing contains suspicious keywords
                if price < low_threshold and suspicious_keyword_found:
                    filter_stats['statistical_outlier_low'] += 1
                    filter_stats['total_filtered'] += 1
                    reason = f"Suspicious low price: {price:.0f}лв < {low_threshold:.0f}лв (40% of median {median:.0f}лв) + keyword '{suspicious_keyword_found}'"
                    rejected_listings.append({
                        'title': item.get('title', ''),
                        'price': price,
                        'url': item.get('url', ''),
                        'model': model,
                        'reason': reason,
                        'category': '📉 Statistical Outlier (Low Price)'
                    })
                    logger.debug(f"Filtered {model} @ {price}лв: {reason}")
                else:
                    final_items.append(item)
                    filter_stats['total_kept'] += 1

            if final_items:
                filtered_data[model] = final_items
        elif valid_items:
            # Not enough samples for statistics, keep all
            for item in valid_items:
                filter_stats['total_kept'] += 1
            filtered_data[model] = valid_items

    return filtered_data, filter_stats, rejected_listings


def get_filter_summary(filtered_data: Dict[str, List[float]]) -> str:
    """
    Generate a summary of post-processing filtering results

    Args:
        filtered_data: Dict of {model: [prices]} AFTER filtering

    Returns:
        Formatted string with filtering info
    """
    summary = []
    summary.append("📊 Post-Processing Filter Results:")
    summary.append(f"  Low Outlier Threshold:  < {OUTLIER_THRESHOLD_LOW * 100:.0f}% of median")
    summary.append(f"  Min Sample Size:        {MIN_SAMPLE_SIZE} listings")
    summary.append("")

    for model, prices in sorted(filtered_data.items()):
        if len(prices) >= MIN_SAMPLE_SIZE:
            import statistics
            median = statistics.median(prices)
            low = median * OUTLIER_THRESHOLD_LOW
            summary.append(
                f"  {model:20} → min: {low:>5.0f}лв "
                f"(median: {median:.0f}лв, n={len(prices)})"
            )
        else:
            summary.append(
                f"  {model:20} → No filtering (n={len(prices)} < {MIN_SAMPLE_SIZE})"
            )

    return "\n".join(summary)