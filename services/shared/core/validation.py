"""
Input validation utilities
"""
import re
from typing import Optional
from fastapi import HTTPException


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_gpu_model(model: str) -> str:
    """
    Валидира GPU модел
    
    Args:
        model: GPU model string
    
    Returns:
        Cleaned model string
    
    Raises:
        ValidationError: Ако моделът е невалиден
    """
    if not model or not isinstance(model, str):
        raise ValidationError("Model must be a non-empty string")
    
    model = model.strip()
    
    if not model:
        raise ValidationError("Model cannot be empty")
    
    if len(model) > 100:
        raise ValidationError("Model name too long (max 100 characters)")
    
    # Проверка за опасни characters
    if re.search(r'[<>\"\'%;()&+]', model):
        raise ValidationError("Model contains invalid characters")
    
    return model


def validate_price_strict(price: float) -> float:
    """
    Валидира цена (строга версия - хвърля ValidationError)

    Args:
        price: Price value

    Returns:
        Validated price

    Raises:
        ValidationError: Ако цената е невалидна
    """
    if not isinstance(price, (int, float)):
        raise ValidationError("Price must be a number")

    if price <= 0:
        raise ValidationError("Price must be positive")

    if price > 100000:  # Максимална разумна цена за GPU
        raise ValidationError("Price unreasonably high (max 100000лв)")

    return float(price)


def validate_source(source: str) -> str:
    """
    Валидира източник
    
    Args:
        source: Source name
    
    Returns:
        Validated source
    
    Raises:
        ValidationError: Ако източникът е невалиден
    """
    if not source or not isinstance(source, str):
        raise ValidationError("Source must be a non-empty string")
    
    source = source.strip()
    
    if not source:
        raise ValidationError("Source cannot be empty")
    
    if len(source) > 50:
        raise ValidationError("Source name too long (max 50 characters)")
    
    # Само букви, цифри, тире и долни черти
    if not re.match(r'^[a-zA-Z0-9_-]+$', source):
        raise ValidationError("Source contains invalid characters")
    
    return source


def validate_pagination(page: int = 1, size: int = 100) -> tuple[int, int]:
    """
    Валидира pagination параметри
    
    Args:
        page: Page number (1-indexed)
        size: Page size
    
    Returns:
        Tuple of (page, size)
    
    Raises:
        ValidationError: Ако параметрите са невалидни
    """
    if not isinstance(page, int) or page < 1:
        raise ValidationError("Page must be a positive integer")
    
    if not isinstance(size, int) or size < 1:
        raise ValidationError("Size must be a positive integer")
    
    if size > 1000:
        raise ValidationError("Size too large (max 1000)")
    
    return page, size


def sanitize_search_term(term: str) -> str:
    """
    Почиства search term за безопасно използване
    
    Args:
        term: Search term
    
    Returns:
        Sanitized term
    """
    if not term or not isinstance(term, str):
        return ""
    
    # Премахваме специални символи
    term = re.sub(r'[<>\"\'%;()&+]', '', term)
    
    # Trimваме whitespace
    term = term.strip()
    
    # Ограничаваме дължината
    if len(term) > 200:
        term = term[:200]
    
    return term


# FastAPI dependency за валидация
def validate_model_param(model: str) -> str:
    """FastAPI dependency за валидация на модел"""
    try:
        return validate_gpu_model(model)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Test-compatible validation functions (return bool)
def validate_model_name(model: Optional[str]) -> bool:
    """
    Проверява дали model name е валиден (за тестове)

    Args:
        model: Model name

    Returns:
        True ако е валиден, False иначе
    """
    if not model or not isinstance(model, str):
        return False

    model = model.strip()

    if not model or len(model) < 2:
        return False

    return True


def validate_price_bool(price: Optional[float]) -> bool:
    """
    Проверява дали цената е валидна (за тестове)

    Args:
        price: Price value (can be None for validation testing)

    Returns:
        True ако е валидна, False иначе
    """
    if price is None:
        return False

    if not isinstance(price, (int, float)):
        return False

    if price <= 0:
        return False

    return True


# Backwards compatibility alias for tests
validate_price = validate_price_bool