# api/routers/rejected.py
from fastapi import APIRouter
from core.cache import cache
from typing import List, Dict

router = APIRouter()


@router.get("/", response_model=List[Dict])
def get_rejected_listings():
    """
    Връща списък с всички отхвърлени обяви от последния scrape

    Returns:
        List of rejected listings with: title, price, url, model, reason, category
    """
    # Get rejected listings from cache
    rejected = cache.get("rejected_listings")

    if rejected is None:
        return []

    return rejected


@router.get("/summary", response_model=Dict[str, int])
def get_rejection_summary():
    """
    Връща обобщена статистика за отхвърлените обяви по категория

    Returns:
        Dict with category -> count
    """
    rejected = cache.get("rejected_listings")

    if not rejected:
        return {}

    # Group by category
    summary = {}
    for item in rejected:
        category = item.get("category", "Unknown")
        summary[category] = summary.get(category, 0) + 1

    return summary


@router.get("/categories", response_model=List[str])
def get_rejection_categories():
    """
    Връща списък с всички категории на отхвърляне

    Returns:
        List of unique category names
    """
    rejected = cache.get("rejected_listings")

    if not rejected:
        return []

    # Get unique categories
    categories = set(item.get("category", "Unknown") for item in rejected)
    return sorted(list(categories))
