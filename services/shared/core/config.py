import yaml
import os
from pathlib import Path
from typing import Any, Dict

class Config:
    """
    Enhanced configuration manager с support за environment variables
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Зарежда config файла"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Взима стойност от config с поддръжка на environment variables
        
        Examples:
            config.get("database.url")
            config.get("scraper.max_pages")
        """
        # Проверка за environment variable
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            return self._convert_type(env_value)
        
        # Взимане от config файла
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def _convert_type(self, value: str) -> Any:
        """Конвертира string стойност към подходящ тип"""
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return value
    
    @property
    def database_url(self) -> str:
        return self.get("database.url", "sqlite:///./gpu.db")
    
    @property
    def log_level(self) -> str:
        return self.get("logging.level", "INFO")
    
    @property
    def log_file(self) -> str:
        return self.get("logging.file", "logs/gpu_service.log")
    
    @property
    def api_host(self) -> str:
        return self.get("api.host", "0.0.0.0")
    
    @property
    def api_port(self) -> int:
        return self.get("api.port", 8000)
    
    @property
    def scraper_max_pages(self) -> int:
        return self.get("scraper.max_pages", 3)
    
    @property
    def scraper_use_tor(self) -> bool:
        return self.get("scraper.use_tor", True)
    
    @property
    def rate_limit_rpm(self) -> int:
        """Requests per minute"""
        return self.get("scraper.rate_limit.requests_per_minute", 10)
    
    @property
    def rate_limit_delay(self) -> int:
        """Delay between pages in seconds"""
        return self.get("scraper.rate_limit.delay_between_pages", 5)
    
    @property
    def max_retries(self) -> int:
        return self.get("scraper.rate_limit.max_retries", 3)
    
    @property
    def retry_delay(self) -> int:
        return self.get("scraper.rate_limit.retry_delay", 10)


# Global config instance
config = Config()