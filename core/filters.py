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


def normalize_model_name(model: str) -> str:
    """
    Normalize GPU model name for consistency
    
    Examples:
        RTX3060TI -> RTX 3060 TI
        RTX 3060TI -> RTX 3060 TI
        RX6600XT -> RX 6600 XT
        VEGA56 -> VEGA 56
        gtx 1660ti -> GTX 1660 TI
    """
    if not model:
        return model
    
    # Convert to uppercase
    model = model.upper().strip()
    
    # Remove all spaces first
    model = model.replace(" ", "")
    
    # Add space after brand (RTX, GTX, RX, VEGA)
    model = re.sub(r'(RTX|GTX|RX|VEGA)(\d+)', r'\1 \2', model)
    
    # Add space before suffix (TI, SUPER, XT, XTX)
    model = re.sub(r'(\d+)(TI|SUPER|XT|XTX)$', r'\1 \2', model)
    
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


def filter_scraped_data(raw_data: Dict[str, List[float]]) -> tuple[Dict[str, List[float]], Dict[str, int]]:
    """
    Post-processing filtering: филтрира scraped данни СЛЕД събирането им

    Предимства:
    - Имаме пълната статистика преди филтриране (няма warm-up фаза)
    - По-точно outlier detection
    - По-просто за debugging

    Args:
        raw_data: Речник {model: [prices]} със ВСИЧКИ scraped данни

    Returns:
        Tuple of (filtered_data, filter_stats)
        - filtered_data: Речник {model: [prices]} само с валидни цени
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

    for model, prices in raw_data.items():
        if not prices or len(prices) < MIN_SAMPLE_SIZE:
            # Keep models with too few listings (no stats available)
            filtered_data[model] = prices
            filter_stats['total_kept'] += len(prices)
            continue

        import statistics
        median = statistics.median(prices)
        low_threshold = median * OUTLIER_THRESHOLD_LOW
        high_threshold = median * OUTLIER_THRESHOLD_HIGH

        valid_prices = []
        for price in prices:
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

            # Price passed all checks
            valid_prices.append(price)
            filter_stats['total_kept'] += 1

        if valid_prices:
            filtered_data[model] = valid_prices

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