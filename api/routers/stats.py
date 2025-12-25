from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from storage.repo import GPURepository
from api.dependencies import get_db
from pydantic import BaseModel
from core.cache import cache

router = APIRouter()


class SummaryStats(BaseModel):
    """Summary statistics response"""
    total_listings: int
    unique_models: int
    avg_price: float
    min_price: float
    max_price: float


def get_all_models_stats(repo: GPURepository) -> dict:
    stats = {}
    for model in repo.get_models():
        stats[model] = repo.get_price_stats(model)
    return stats


@router.get("/summary", response_model=SummaryStats, tags=["📊 Statistics"])
def get_summary_stats(db: Session = Depends(get_db)):
    """
    Връща обобщена статистика за всички обяви

    Това е оптимизиран endpoint за homepage статистиката,
    който връща само агрегираните числа без всички обяви.
    """
    # Try cache first
    cache_key = "stats:summary"
    cached_result = cache.get(cache_key)
    if cached_result:
        return SummaryStats(**cached_result)

    with GPURepository(db) as repo:
        all_listings = repo.get_all_listings()

        if not all_listings:
            result = {
                "total_listings": 0,
                "unique_models": 0,
                "avg_price": 0.0,
                "min_price": 0.0,
                "max_price": 0.0
            }
        else:
            total = len(all_listings)
            # GPU objects have .model and .price attributes
            unique = len(set(listing.model for listing in all_listings))
            prices = [listing.price for listing in all_listings]
            avg = sum(prices) / total

            result = {
                "total_listings": total,
                "unique_models": unique,
                "avg_price": round(avg, 2),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2)
            }

        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)
        return SummaryStats(**result)


@router.get("/", tags=["📊 Statistics"])
def stats_root(db: Session = Depends(get_db)):
    """Връща статистики за всички GPU модели"""
    # Try cache first
    cache_key = "stats:all_models"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    with GPURepository(db) as repo:
        result = get_all_models_stats(repo)
        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)
        return result
