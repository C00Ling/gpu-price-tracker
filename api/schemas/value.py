# api/schemas/value.py
from pydantic import BaseModel

class GPUValue(BaseModel):
    model: str
    fps: float
    price: float
    fps_per_lv: float

class GPUValueList(BaseModel):
    gpus: list[GPUValue]
    count: int