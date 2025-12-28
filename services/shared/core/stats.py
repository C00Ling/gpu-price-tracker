# core/stats.py
from storage.repo import GPURepository
from typing import Dict

def get_price_stats(repo: GPURepository, model: str) -> Dict:
    """
    Връща статистики за даден GPU модел.
    """
    prices = repo.get_prices(model)
    if not prices:
        return {}

    prices_sorted = sorted(prices)
    n = len(prices)

    return {
        "min": min(prices),
        "max": max(prices),
        "median": prices_sorted[n // 2],
        "mean": sum(prices) / n,
        "count": n,
        "percentile_25": prices_sorted[n // 4] if n >= 4 else min(prices)
    }

def calculate_stats(repo: GPURepository) -> Dict[str, Dict]:
    """
    Извлича статистики за всички налични модели.
    Връща речник с ключ = модел, стойност = статистики.
    """
    stats = {}
    models = repo.get_models()
    for model in models:
        stats[model] = get_price_stats(repo, model)
    return stats

def calculate_price_stats(prices_by_model: Dict[str, list]) -> Dict[str, Dict]:
    """
    Изчислява статистики за цените по модел.

    Args:
        prices_by_model: Dict със ключ модел, стойност списък с цени

    Returns:
        Dict със ключ модел, стойност речник със статистики
    """
    import statistics

    stats = {}
    for model, prices in prices_by_model.items():
        if not prices:
            continue

        stats[model] = {
            "min": min(prices),
            "max": max(prices),
            "median": statistics.median(prices),
            "mean": statistics.mean(prices),
            "count": len(prices)
        }

    return stats
