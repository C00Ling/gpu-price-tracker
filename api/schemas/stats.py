# api/schemas/stats.py
from pydantic import BaseModel

class PriceStats(BaseModel):
    model: str
    min: float
    max: float
    median: float
    mean: float
    count: int
    percentile_25: float

class AllStats(BaseModel):
    stats: dict[str, PriceStats]