# api/routers/value.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from storage.repo import GPURepository
from core.value import calculate_value_from_stats
from core.cache import cache
from api.dependencies import get_db
from typing import List, Dict

router = APIRouter()


@router.get("/", response_model=List[Dict])
def get_gpu_value(db: Session = Depends(get_db)):
    """
    Връща GPU модели сортирани по FPS per лв
    """
    # Try cache first
    cache_key = "value:all_gpus"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    with GPURepository(db) as repo:
        # Взимаме статистики за всички модели
        models = repo.get_models()
        stats = {}

        for model in models:
            model_stats = repo.get_price_stats(model)
            if model_stats:
                stats[model] = model_stats

        # Изчисляваме value
        result = calculate_value_from_stats(stats)

        # Cache for 10 minutes
        cache.set(cache_key, result, ttl=600)
        return result


@router.get("/top/{n}", response_model=List[Dict])
def get_top_n_gpus(n: int = 10, db: Session = Depends(get_db)):
    """
    Връща топ N GPU модели по FPS per лв
    """
    # Validate n
    if n <= 0:
        raise HTTPException(status_code=400, detail="n must be positive")

    # Try cache first
    cache_key = f"value:top_{n}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    with GPURepository(db) as repo:
        models = repo.get_models()
        stats = {model: repo.get_price_stats(model) for model in models if repo.get_price_stats(model)}

        result = calculate_value_from_stats(stats)
        top_n = result[:n]

        # Cache for 10 minutes
        cache.set(cache_key, top_n, ttl=600)
        return top_n