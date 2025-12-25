# core/scraper_status.py
"""
Simple in-memory scraper status tracking for polling fallback
"""
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

class ScraperStatus:
    """Thread-safe in-memory scraper status tracker"""

    def __init__(self):
        self._lock = Lock()
        self._status: Dict[str, Any] = {
            "is_running": False,
            "progress": 0,
            "status": "idle",
            "details": {},
            "started_at": None,
            "updated_at": None,
            "completed_at": None,
            "error": None
        }

    def start(self):
        """Mark scraper as started"""
        with self._lock:
            self._status.update({
                "is_running": True,
                "progress": 0,
                "status": "Започване...",
                "details": {},
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None
            })

    def update(self, progress: int, status: str, details: Optional[Dict[str, Any]] = None):
        """Update scraper progress"""
        with self._lock:
            self._status.update({
                "progress": progress,
                "status": status,
                "details": details or {},
                "updated_at": datetime.utcnow().isoformat()
            })

    def complete(self, details: Optional[Dict[str, Any]] = None):
        """Mark scraper as completed"""
        with self._lock:
            self._status.update({
                "is_running": False,
                "progress": 100,
                "status": "Завършено! ✅",
                "details": details or {},
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })

    def error(self, error_message: str):
        """Mark scraper as failed"""
        with self._lock:
            self._status.update({
                "is_running": False,
                "status": "Грешка",
                "error": error_message,
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })

    def get_status(self) -> Dict[str, Any]:
        """Get current status (thread-safe copy)"""
        with self._lock:
            return self._status.copy()

    def reset(self):
        """Reset status to idle"""
        with self._lock:
            self._status.update({
                "is_running": False,
                "progress": 0,
                "status": "idle",
                "details": {},
                "started_at": None,
                "updated_at": None,
                "completed_at": None,
                "error": None
            })


# Global scraper status instance
scraper_status = ScraperStatus()
