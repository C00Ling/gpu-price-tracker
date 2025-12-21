# api/schemas/listings.py
from pydantic import BaseModel

class GPUListingBase(BaseModel):
    model: str
    source: str
    price: float

class GPUListingCreate(GPUListingBase):
    pass

class GPUListingResponse(GPUListingBase):
    id: int
    
    class Config:
        from_attributes = True