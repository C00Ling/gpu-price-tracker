# storage/price_history.py
"""
Price history tracking for price drop detection
"""
from sqlalchemy.orm import Session
from storage.repo import GPURepository
from core.logging import get_logger
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

logger = get_logger("price_history")


class PriceHistoryTracker:
    """Tracks price history and detects significant drops"""

    def __init__(self, session: Session):
        self.session = session
        self.repo = GPURepository(session)

    def get_historical_prices(self, model: str, days: int = 7) -> Dict:
        """
        Get historical prices for a model

        For now, uses current database as "history"
        In production, you'd want a separate price_history table with timestamps

        Returns:
            Dict with keys: model (str), prices (List[float]), count (int)
        """
        prices = self.repo.get_prices(model)
        return {
            "model": model,
            "prices": prices,
            "count": len(prices)
        }

    def detect_price_drops(self, threshold_percent: float = 10.0) -> List[Tuple[str, float, float, float]]:
        """
        Detect significant price drops across all models

        Returns list of (model, old_price, new_price, drop_percent)

        Algorithm:
        1. Get current min price for each model
        2. Compare with previous stats (cached or stored)
        3. If drop > threshold, report it

        Note: In a real implementation, you'd store price snapshots
        in a separate table with timestamps
        """
        drops = []

        try:
            models = self.repo.get_models()

            for model in models:
                stats = self.repo.get_price_stats(model)
                if not stats:
                    continue

                current_min = stats.get('min', 0)
                current_median = stats.get('median', 0)

                # Simple heuristic: if min is significantly below median,
                # it might be a new drop
                if current_median > 0:
                    diff_percent = ((current_median - current_min) / current_median) * 100

                    if diff_percent >= threshold_percent:
                        # Potential price drop detected
                        drops.append((
                            model,
                            current_median,  # "old" price (median)
                            current_min,     # "new" price (min)
                            diff_percent
                        ))

                        logger.info(
                            f"💰 Price drop detected: {model} "
                            f"{current_median:.2f}лв → {current_min:.2f}лв (-{diff_percent:.1f}%)"
                        )

        except Exception as e:
            logger.error(f"Error detecting price drops: {e}")

        return drops

    def get_price_change_summary(self) -> Dict:
        """Get summary of price changes"""
        try:
            models = self.repo.get_models()
            total_models = len(models)

            drops_detected = len(self.detect_price_drops(threshold_percent=5.0))

            return {
                "total_models": total_models,
                "drops_detected": drops_detected,
                "check_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting price change summary: {e}")
            return {}


def create_price_snapshot(session: Session) -> Dict:
    """
    Create a snapshot of current prices

    This would be called periodically to build price history
    In production, you'd store this in a price_snapshots table
    """
    repo = GPURepository(session)
    snapshot = {}

    try:
        models = repo.get_models()

        for model in models:
            stats = repo.get_price_stats(model)
            if stats:
                snapshot[model] = {
                    "min": stats.get("min"),
                    "median": stats.get("median"),
                    "mean": stats.get("mean"),
                    "count": stats.get("count"),
                    "timestamp": datetime.now().isoformat()
                }

        logger.info(f"📸 Created price snapshot for {len(snapshot)} models")
        return snapshot

    except Exception as e:
        logger.error(f"Error creating price snapshot: {e}")
        return {}
