# core/value.py
from typing import Dict, List, Tuple
from ingest.scraper import SAMPLE_BENCHMARKS

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


def calculate_value_from_stats(stats: Dict[str, Dict]) -> List[Dict]:
    """
    Изчислява FPS/лв за всеки модел от stats dict (за API)

    Args:
        stats: Речник {model: {min, max, median, mean, count}}

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

        # Използваме MIN цена - най-добрата налична оферта
        price = data.get("min", 1)
        fps_per_lv = round(fps / price, 3)

        result.append({
            "model": model,
            "fps": fps,
            "price": price,
            "fps_per_lv": fps_per_lv
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
    
    # Normalize both the input model and benchmark models
    normalized_model = normalize_model_name(model).replace(' ', '')
    
    for bench_model, fps in SAMPLE_BENCHMARKS.items():
        bench_normalized = normalize_model_name(bench_model).replace(' ', '')
        
        # Exact match or contains
        if bench_normalized == normalized_model or \
           bench_normalized in normalized_model or \
           normalized_model in bench_normalized:
            return fps
    
    return None