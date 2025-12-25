from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from storage.orm import GPU
from core.logging import get_logger
from typing import List, Dict, Optional, Any
import statistics

logger = get_logger("storage")


class RepositoryError(Exception):
    """Custom exception за repository грешки"""
    pass


class GPURepository:
    """Enhanced GPU Repository с proper error handling и model normalization"""

    def __init__(self, session: Optional[Session] = None):
        from storage.db import SessionLocal
        self.session = session or SessionLocal()
        self.own_session = session is None
        logger.debug("GPURepository initialized")

    def add_listing(self, model: str, source: str, price: float) -> GPU:
        """
        Добавя нова обява в базата с нормализиран модел
        
        Args:
            model: GPU модел
            source: Източник (OLX, etc.)
            price: Цена в лева
        
        Returns:
            GPU обект
        
        Raises:
            RepositoryError: Ако записът не успее
        """
        try:
            # Validation
            if not model or not model.strip():
                raise ValueError("Model cannot be empty")
            
            if not source or not source.strip():
                raise ValueError("Source cannot be empty")
            
            if price <= 0:
                raise ValueError(f"Price must be positive, got {price}")
            
            # Normalize model before saving
            from core.filters import normalize_model_name
            normalized_model = normalize_model_name(model.strip())
            
            gpu = GPU(model=normalized_model, source=source.strip(), price=price)
            self.session.add(gpu)
            self.session.commit()
            
            logger.debug(f"Added listing: {normalized_model} - {price}лв from {source}")
            return gpu
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise RepositoryError(f"Invalid input: {e}")
        
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error while adding listing: {e}")
            raise RepositoryError(f"Failed to add listing: {e}")
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error while adding listing: {e}")
            raise RepositoryError(f"Unexpected error: {e}")

    def add_listings_bulk(self, listings: List[Dict[str, Any]]) -> int:
        """
        Добавя множество обяви наведнъж с нормализация

        Args:
            listings: List of dicts with keys: model, source, price, url (optional)

        Returns:
            Брой успешно добавени обяви
        """
        try:
            from core.filters import normalize_model_name

            gpu_objects = []
            for item in listings:
                if not all(k in item for k in ['model', 'source', 'price']):
                    logger.warning(f"Skipping invalid listing: {item}")
                    continue

                if item['price'] <= 0:
                    logger.warning(f"Skipping listing with invalid price: {item}")
                    continue

                # Normalize model
                normalized_model = normalize_model_name(item['model'].strip())

                gpu = GPU(
                    model=normalized_model,
                    source=item['source'].strip(),
                    price=item['price'],
                    url=item.get('url', '')  # Optional URL field
                )
                gpu_objects.append(gpu)
            
            self.session.bulk_save_objects(gpu_objects)
            self.session.commit()
            
            logger.info(f"Bulk added {len(gpu_objects)} listings")
            return len(gpu_objects)
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error in bulk insert: {e}")
            raise RepositoryError(f"Bulk insert failed: {e}")

    def get_all_listings(self) -> List[GPU]:
        """Връща всички обяви"""
        try:
            listings = self.session.query(GPU).all()
            logger.debug(f"Retrieved {len(listings)} listings")
            return listings
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving listings: {e}")
            raise RepositoryError(f"Failed to retrieve listings: {e}")

    def get_by_model(self, model: str) -> List[GPU]:
        """Връща обяви за конкретен модел с нормализация"""
        try:
            if not model or not model.strip():
                logger.warning("Empty model name provided")
                return []
            
            # Normalize the search model
            from core.filters import normalize_model_name
            normalized_model = normalize_model_name(model.strip())
            
            listings = self.session.query(GPU).filter(
                GPU.model == normalized_model
            ).all()
            
            logger.debug(f"Retrieved {len(listings)} listings for {normalized_model}")
            return listings
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving listings for {model}: {e}")
            raise RepositoryError(f"Failed to retrieve listings: {e}")

    def get_prices(self, model: str) -> List[float]:
        """Връща списък с цени за даден модел с нормализация"""
        try:
            from core.filters import normalize_model_name
            normalized_model = normalize_model_name(model.strip())
            
            results = self.session.query(GPU.price).filter(
                GPU.model == normalized_model
            ).all()
            
            prices = [float(r[0]) for r in results]
            logger.debug(f"Retrieved {len(prices)} prices for {normalized_model}")
            return prices
            
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving prices for {model}: {e}")
            return []

    def get_price_stats(self, model: str) -> Optional[Dict]:
        """
        Статистики за даден модел с нормализация
        
        Returns:
            Dict с min, max, median, mean, count, percentile_25
            или None ако няма данни
        """
        try:
            prices = self.get_prices(model)
            
            if not prices:
                logger.debug(f"No prices found for {model}")
                return None
            
            n = len(prices)
            sorted_prices = sorted(prices)
            
            stats = {
                'min': min(prices),
                'max': max(prices),
                'median': statistics.median(prices),
                'mean': sum(prices) / n,
                'count': n,
                'percentile_25': (
                    statistics.quantiles(prices, n=4)[0] 
                    if n >= 4 
                    else min(prices)
                )
            }
            
            logger.debug(f"Calculated stats for {model}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating stats for {model}: {e}")
            return None

    def get_models(self) -> List[str]:
        """Връща списък с уникални модели (вече нормализирани)"""
        try:
            results = self.session.query(GPU.model).distinct().all()
            models = [r[0] for r in results]
            logger.debug(f"Retrieved {len(models)} unique models")
            return models
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving models: {e}")
            return []

    def get_available_models(self) -> List[str]:
        """Alias за get_models() - за test compatibility"""
        return self.get_models()

    def get_listings_by_model(self, model: str) -> List[GPU]:
        """Alias за get_by_model() - за test compatibility"""
        return self.get_by_model(model)

    def get_total_count(self) -> int:
        """Връща общия брой обяви в базата"""
        try:
            count = self.session.query(GPU).count()
            logger.debug(f"Total listings count: {count}")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error getting total count: {e}")
            raise RepositoryError(f"Failed to get total count: {e}")

    def delete_listing(self, listing_id: int) -> bool:
        """
        Изтрива обява по ID

        Args:
            listing_id: ID на обявата

        Returns:
            True ако е изтрита, False ако не съществува
        """
        try:
            listing = self.session.query(GPU).filter(GPU.id == listing_id).first()
            if listing:
                self.session.delete(listing)
                self.session.commit()
                logger.info(f"Deleted listing with ID {listing_id}")
                return True
            else:
                logger.warning(f"Listing with ID {listing_id} not found")
                return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting listing {listing_id}: {e}")
            raise RepositoryError(f"Failed to delete listing: {e}")

    def clear_listings(self) -> int:
        """
        Изтрива всички обяви

        Returns:
            Брой изтрити записи
        """
        try:
            count = self.session.query(GPU).count()
            self.session.query(GPU).delete()
            self.session.commit()
            logger.info(f"Cleared {count} listings")
            return count
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error clearing listings: {e}")
            raise RepositoryError(f"Failed to clear listings: {e}")

    def delete_by_model(self, model: str) -> int:
        """
        Изтрива всички обяви за даден модел с нормализация
        
        Returns:
            Брой изтрити записи
        """
        try:
            from core.filters import normalize_model_name
            normalized_model = normalize_model_name(model.strip())
            
            count = self.session.query(GPU).filter(
                GPU.model == normalized_model
            ).delete()
            self.session.commit()
            logger.info(f"Deleted {count} listings for {normalized_model}")
            return count
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting listings for {model}: {e}")
            raise RepositoryError(f"Failed to delete listings: {e}")

    def close(self):
        """Затваря сесията"""
        if self.own_session:
            try:
                self.session.close()
                logger.debug("Repository session closed")
            except Exception as e:
                logger.error(f"Error closing session: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Exception in context manager: {exc_val}")
            self.session.rollback()
        self.close()