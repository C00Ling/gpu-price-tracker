from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from storage.repo import GPURepository, RepositoryError
from api.dependencies import get_db
from core.validation import validate_model_param, validate_pagination
from core.logging import get_logger
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

router = APIRouter()
logger = get_logger("api.listings")


# Pydantic schemas
class GPUListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model: str
    price: float
    source: str
    url: Optional[str] = None


class GPUListingCreate(BaseModel):
    model: str
    price: float
    source: str


class PaginatedResponse(BaseModel):
    items: List[GPUListingResponse]
    total: int
    page: int
    size: int
    pages: int


@router.get("/", response_model=List[GPUListingResponse])
def get_listings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(100, ge=1, le=1000, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Връща всички обяви с pagination
    
    - **page**: Номер на страницата (започва от 1)
    - **size**: Брой елементи на страница (max 1000)
    """
    try:
        logger.info(f"GET /listings (page={page}, size={size})")
        
        with GPURepository(db) as repo:
            all_listings = repo.get_all_listings()
            
            # Manual pagination
            start = (page - 1) * size
            end = start + size
            
            paginated = all_listings[start:end]
            
            logger.info(f"Returned {len(paginated)} listings")
            return paginated
            
    except RepositoryError as e:
        logger.error(f"Repository error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{model}", response_model=List[GPUListingResponse])
def get_listings_by_model(
    model: str = Depends(validate_model_param),
    db: Session = Depends(get_db)
):
    """
    Връща обяви за конкретен GPU модел
    
    - **model**: GPU модел (напр. RTX 4070)
    """
    try:
        logger.info(f"GET /listings/{model}")
        
        with GPURepository(db) as repo:
            listings = repo.get_by_model(model)
            
            if not listings:
                logger.warning(f"No listings found for model: {model}")
                raise HTTPException(
                    status_code=404,
                    detail=f"No listings found for model: {model}"
                )
            
            logger.info(f"Found {len(listings)} listings for {model}")
            return listings
            
    except HTTPException:
        raise
    except RepositoryError as e:
        logger.error(f"Repository error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/count/total")
def get_total_count(db: Session = Depends(get_db)):
    """
    Връща общ брой обяви
    """
    try:
        logger.info("GET /listings/count/total")
        
        with GPURepository(db) as repo:
            total = len(repo.get_all_listings())
            logger.info(f"Total listings: {total}")
            return {"total": total}
            
    except Exception as e:
        logger.error(f"Error getting count: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models/list")
def get_available_models(db: Session = Depends(get_db)):
    """
    Връща списък с всички налични модели
    """
    try:
        logger.info("GET /listings/models/list")
        
        with GPURepository(db) as repo:
            models = repo.get_models()
            logger.info(f"Found {len(models)} unique models")
            return {"models": sorted(models), "count": len(models)}
            
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")