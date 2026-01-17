# core/value.py
from typing import Dict, List, Tuple, Optional
from ingest.scraper import SAMPLE_BENCHMARKS, GPU_VRAM
from data.gpu_benchmarks import GPU_BENCHMARKS

def calculate_value(prices_by_model: Dict[str, List[float]],
                   benchmarks: Dict[str, float]) -> List[Tuple[str, float, float, float]]:
    """
    Изчислява FPS/лв за всеки модел

    Args:
        prices_by_model: Dict със ключ модел, стойност списък с цени
        benchmarks: Dict със ключ модел, стойност FPS

    Returns:
        List of tuples (model, fps, price, fps_per_lv) сортиран по FPS/лв
    """
    result = []

    for model, prices in prices_by_model.items():
        if not prices:
            continue

        # Вземи FPS от benchmarks
        fps = benchmarks.get(model)
        if fps is None or fps <= 0:
            continue

        # Използваме min цена (най-добрата оферта)
        price = min(prices)
        if price <= 0:
            continue

        fps_per_lv = fps / price

        result.append((model, fps, price, fps_per_lv))

    # Сортиране по най-добър FPS/лв (descending)
    result.sort(key=lambda x: x[3], reverse=True)
    return result


def calculate_value_from_stats(stats: Dict[str, Dict], min_vram: Optional[int] = None) -> List[Dict]:
    """
    Изчислява FPS/лв за всеки модел от stats dict (за API)

    Всеки VRAM вариант се показва отделно.
    Например: "RTX 3060 8GB" и "RTX 3060 12GB" са отделни записи.

    Args:
        stats: Речник {model: {min, max, median, mean, count}}
        min_vram: Минимум VRAM в GB (опционално филтриране)

    Returns:
        Списък с модели сортирани по FPS/лв
    """
    result = []

    for model, data in stats.items():
        if not data or data.get("min", 0) == 0:
            continue

        # Взимаме FPS от benchmark данните
        fps = get_fps_for_model(model)
        if fps is None:
            continue  # Пропускаме модели без FPS данни

        # Взимаме VRAM за модела
        vram = get_vram_for_model(model)

        # Взимаме относителния скор за модела (RTX 5090 = 100)
        relative_score = get_relative_score_for_model(model)

        # Филтрираме по VRAM, ако е зададен минимум
        if min_vram is not None:
            if vram is None or vram < min_vram:
                continue

        # Използваме MIN цена - най-добрата налична оферта
        price = data.get("min", 1)
        fps_per_lv = round(fps / price, 3)

        result.append({
            "model": model,
            "fps": fps,
            "price": price,
            "fps_per_lv": fps_per_lv,
            "vram": vram,
            "relative_score": relative_score
        })

    # Сортиране по най-добър FPS/лв
    result.sort(key=lambda x: x["fps_per_lv"], reverse=True)
    return result


def get_fps_for_model(model: str) -> float | None:
    """
    Намира FPS за даден модел от benchmark данните
    Използва нормализация за по-добро съвпадение
    """
    from core.filters import normalize_model_name

    # Normalize the input model
    normalized_model = normalize_model_name(model)

    # First try exact match (highest priority)
    for bench_model, fps in SAMPLE_BENCHMARKS.items():
        bench_normalized = normalize_model_name(bench_model)
        if bench_normalized == normalized_model:
            return fps

    # If no exact match, try fuzzy matching with word boundaries
    # This prevents "RX 6800" from matching "RX 6800 XT"
    normalized_model_no_spaces = normalized_model.replace(' ', '')

    for bench_model, fps in SAMPLE_BENCHMARKS.items():
        bench_normalized = normalize_model_name(bench_model).replace(' ', '')

        # Only match if one contains the other AND they're similar length
        # This prevents substring false matches
        if normalized_model_no_spaces in bench_normalized or \
           bench_normalized in normalized_model_no_spaces:
            # Check if length difference is reasonable (within 3 chars)
            if abs(len(bench_normalized) - len(normalized_model_no_spaces)) <= 3:
                return fps

    return None


def get_vram_for_model(model: str) -> int | None:
    """
    Намира VRAM за даден модел от GPU_VRAM данните
    Използва нормализация за по-добро съвпадение
    """
    import re
    from core.filters import normalize_model_name

    # Normalize the input model
    normalized_model = normalize_model_name(model)

    # First try exact match (highest priority)
    for vram_model, vram in GPU_VRAM.items():
        vram_normalized = normalize_model_name(vram_model)
        if vram_normalized == normalized_model:
            return vram

    # If no exact match, try fuzzy matching with word boundaries
    # This prevents "RX 6800" from matching "RX 6800 XT"
    normalized_model_no_spaces = normalized_model.replace(' ', '')

    for vram_model, vram in GPU_VRAM.items():
        vram_normalized = normalize_model_name(vram_model).replace(' ', '')

        # Only match if one contains the other AND they're similar length
        # This prevents substring false matches
        if normalized_model_no_spaces in vram_normalized or \
           vram_normalized in normalized_model_no_spaces:
            # Check if length difference is reasonable (within 3 chars)
            if abs(len(vram_normalized) - len(normalized_model_no_spaces)) <= 3:
                return vram

    # Try to extract VRAM from model name (e.g., "RTX 4080 16GB" -> 16)
    vram_pattern = re.search(r'(\d+)\s*GB', model, re.IGNORECASE)
    if vram_pattern:
        return int(vram_pattern.group(1))

    # Fallback: Common VRAM values for known GPU series
    model_upper = model.upper()

    # NVIDIA RTX 50 series
    if 'RTX 5090' in model_upper: return 32
    if 'RTX 5080' in model_upper: return 16
    if 'RTX 5070' in model_upper: return 12
    if 'RTX 5060' in model_upper: return 8

    # NVIDIA RTX 40 series
    if 'RTX 4090' in model_upper: return 24
    if 'RTX 4080' in model_upper: return 16
    if 'RTX 4070 TI' in model_upper or 'RTX 4070TI' in model_upper: return 12
    if 'RTX 4070' in model_upper: return 12
    if 'RTX 4060 TI' in model_upper or 'RTX 4060TI' in model_upper: return 16
    if 'RTX 4060' in model_upper: return 8
    if 'RTX 4050' in model_upper: return 6

    # NVIDIA RTX 30 series
    if 'RTX 3090 TI' in model_upper or 'RTX 3090TI' in model_upper: return 24
    if 'RTX 3090' in model_upper: return 24
    if 'RTX 3080 TI' in model_upper or 'RTX 3080TI' in model_upper: return 12
    if 'RTX 3080' in model_upper and '12GB' in model_upper: return 12
    if 'RTX 3080' in model_upper: return 10
    if 'RTX 3070 TI' in model_upper or 'RTX 3070TI' in model_upper: return 8
    if 'RTX 3070' in model_upper: return 8
    if 'RTX 3060 TI' in model_upper or 'RTX 3060TI' in model_upper: return 8
    if 'RTX 3060' in model_upper and '12GB' in model_upper: return 12
    if 'RTX 3060' in model_upper: return 12
    if 'RTX 3050' in model_upper: return 8

    # AMD RX 7000 series
    if 'RX 7900 XTX' in model_upper: return 24
    if 'RX 7900 XT' in model_upper: return 20
    if 'RX 7800 XT' in model_upper: return 16
    if 'RX 7700 XT' in model_upper: return 12
    if 'RX 7600' in model_upper: return 8

    # AMD RX 6000 series
    if 'RX 6950 XT' in model_upper: return 16
    if 'RX 6900 XT' in model_upper: return 16
    if 'RX 6800 XT' in model_upper: return 16
    if 'RX 6800' in model_upper: return 16
    if 'RX 6750 XT' in model_upper: return 12
    if 'RX 6700 XT' in model_upper: return 12
    if 'RX 6700' in model_upper: return 10
    if 'RX 6650 XT' in model_upper: return 8
    if 'RX 6600 XT' in model_upper: return 8
    if 'RX 6600' in model_upper: return 8
    if 'RX 6500 XT' in model_upper: return 4
    if 'RX 6400' in model_upper: return 4

    # NVIDIA RTX 20 series
    if 'RTX 2080 TI' in model_upper or 'RTX 2080TI' in model_upper: return 11
    if 'RTX 2080' in model_upper: return 8
    if 'RTX 2070' in model_upper: return 8
    if 'RTX 2060' in model_upper: return 6

    # NVIDIA GTX 16 series
    if 'GTX 1660 TI' in model_upper or 'GTX 1660TI' in model_upper: return 6
    if 'GTX 1660' in model_upper: return 6
    if 'GTX 1650' in model_upper: return 4

    # AMD RX 5000 series
    if 'RX 5700 XT' in model_upper: return 8
    if 'RX 5700' in model_upper: return 8
    if 'RX 5600 XT' in model_upper: return 6
    if 'RX 5500 XT' in model_upper: return 8

    return None


def get_relative_score_for_model(model: str) -> int | None:
    """
    Намира относителния performance score за даден модел
    RTX 5090 = 100 (baseline)

    Args:
        model: GPU model name

    Returns:
        Относителен скор (0-100) или None ако не е намерен
    """
    from core.filters import normalize_model_name

    # Normalize the input model
    normalized_model = normalize_model_name(model)

    # First try exact match (highest priority)
    for bench_model, score in GPU_BENCHMARKS.items():
        bench_normalized = normalize_model_name(bench_model)
        if bench_normalized == normalized_model:
            return score

    # If no exact match, try fuzzy matching with word boundaries
    normalized_model_no_spaces = normalized_model.replace(' ', '')

    for bench_model, score in GPU_BENCHMARKS.items():
        bench_normalized = normalize_model_name(bench_model).replace(' ', '')

        # Only match if one contains the other AND they're similar length
        if normalized_model_no_spaces in bench_normalized or \
           bench_normalized in normalized_model_no_spaces:
            # Check if length difference is reasonable (within 3 chars)
            if abs(len(bench_normalized) - len(normalized_model_no_spaces)) <= 3:
                return score

    # If not found in GPU_BENCHMARKS, calculate from FPS data
    # RTX 5090 baseline: 238 FPS = 100%
    fps = get_fps_for_model(model)
    if fps is not None and fps > 0:
        RTX_5090_FPS = 238
        relative_score = round((fps / RTX_5090_FPS) * 100)
        return relative_score

    return None