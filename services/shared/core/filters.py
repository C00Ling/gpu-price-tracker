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

# Expanded blacklist keywords
BLACKLIST_KEYWORDS = [
    # Bulgarian
    "за части", "счупена", "не работи", "повредена", "дефект",
    "за ремонт", "артефакти", "черен екран", "не дава екран", "не стартира", "изгоря",
    "развален", "нетествана", "проблем", "не е тествана", "дефектна", "не функционира", "изправни",
    "няма сигнал", "без сигнал", "не дава сигнал",

    # Mining-related (often worn out)
    "майнинг", "mining", "burnout", "mining rig", "копана", "ферма", "mining farm",
    "от ферма", "от майнинг", "за майнинг", "копаене",

    # English
    "broken", "damaged", "faulty", "defective", "not working", "for parts",
    "parts only", "as is", "repair", "artifacts", "black screen",
    "burnt", "dead", "fried", "doa", "no signal", "no display",

    # Common suspicious patterns
    "срочно", "бързо", "спешно",  # Often scams
]

# Outlier detection thresholds
OUTLIER_THRESHOLD_LOW = 0.50   # 50% от медианата (по-балансирано филтриране)
OUTLIER_THRESHOLD_HIGH = 3.0   # 300% от медианата (за скъпи outliers)

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

    # NVIDIA RTX 20-series
    "RTX 2080": "RTX 2080 SUPER", # SUPER is more common
    "RTX 2070": "RTX 2070 SUPER", # SUPER is more common
    "RTX 2060": "RTX 2060 SUPER", # SUPER is more common

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

    # 2. Extremely low price check (ALWAYS APPLIED - universal red flag)
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


def filter_scraped_data(raw_data: Dict[str, List]) -> tuple[Dict[str, List], Dict[str, int]]:
    """
    Post-processing filtering: филтрира scraped данни СЛЕД събирането им

    Предимства:
    - Имаме пълната статистика преди филтриране (няма warm-up фаза)
    - По-точно outlier detection
    - По-просто за debugging

    Args:
        raw_data: Речник {model: [items]} където items са dict{'price': float, 'url': str}

    Returns:
        Tuple of (filtered_data, filter_stats)
        - filtered_data: Речник {model: [items]} само с валидни listings
        - filter_stats: Речник {reason: count} с статистика за филтриране
    """
    filtered_data = {}
    filter_stats = {
        'blacklist_keywords': 0,
        'extremely_low_price': 0,
        'statistical_outlier_low': 0,
        'statistical_outlier_high': 0,
        'total_filtered': 0,
        'total_kept': 0,
    }

    for model, items in raw_data.items():
        if not items or len(items) < MIN_SAMPLE_SIZE:
            # Keep models with too few listings (no stats available)
            filtered_data[model] = items
            filter_stats['total_kept'] += len(items)
            continue

        import statistics
        # Extract just prices for statistics
        prices = [item['price'] for item in items]
        median = statistics.median(prices)
        low_threshold = median * OUTLIER_THRESHOLD_LOW
        high_threshold = median * OUTLIER_THRESHOLD_HIGH

        valid_items = []
        for item in items:
            price = item['price']

            # Check extremely low price (< 50 лв)
            if price < 50:
                filter_stats['extremely_low_price'] += 1
                filter_stats['total_filtered'] += 1
                logger.debug(f"Filtered {model} @ {price}лв: extremely low price")
                continue

            # Check low outlier
            if price < low_threshold:
                filter_stats['statistical_outlier_low'] += 1
                filter_stats['total_filtered'] += 1
                logger.debug(
                    f"Filtered {model} @ {price}лв: < {low_threshold:.0f}лв "
                    f"(50% of median {median:.0f}лв)"
                )
                continue

            # Check high outlier
            if price > high_threshold:
                filter_stats['statistical_outlier_high'] += 1
                filter_stats['total_filtered'] += 1
                logger.debug(
                    f"Filtered {model} @ {price}лв: > {high_threshold:.0f}лв "
                    f"(300% of median {median:.0f}лв)"
                )
                continue

            # Listing passed all checks
            valid_items.append(item)
            filter_stats['total_kept'] += 1

        if valid_items:
            filtered_data[model] = valid_items

    return filtered_data, filter_stats


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
    summary.append(f"  High Outlier Threshold: > {OUTLIER_THRESHOLD_HIGH * 100:.0f}% of median")
    summary.append(f"  Min Sample Size:        {MIN_SAMPLE_SIZE} listings")
    summary.append("")

    for model, prices in sorted(filtered_data.items()):
        if len(prices) >= MIN_SAMPLE_SIZE:
            import statistics
            median = statistics.median(prices)
            low = median * OUTLIER_THRESHOLD_LOW
            high = median * OUTLIER_THRESHOLD_HIGH
            summary.append(
                f"  {model:20} → {low:>5.0f}лв - {high:>6.0f}лв "
                f"(median: {median:.0f}лв, n={len(prices)})"
            )
        else:
            summary.append(
                f"  {model:20} → No filtering (n={len(prices)} < {MIN_SAMPLE_SIZE})"
            )

    return "\n".join(summary)