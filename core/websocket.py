# core/websocket.py
"""
WebSocket connection manager for real-time updates
"""
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from core.logging import get_logger
import json
import asyncio

logger = get_logger("websocket")


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"📡 WebSocket connected. Total: {len(self.active_connections)}")

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to GPU Market real-time updates"
            },
            websocket
        )

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"📡 WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        logger.info(f"📡 Broadcasting to {len(self.active_connections)} clients: {message.get('type')}")

        # Send to all connections, removing failed ones
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        """Broadcast statistics update"""
        await self.broadcast({
            "type": "stats_update",
            "data": stats,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def broadcast_scrape_started(self):
        """Notify clients that scraping started"""
        await self.broadcast({
            "type": "scrape_started",
            "message": "Data collection started...",
            "timestamp": asyncio.get_event_loop().time()
        })

    async def broadcast_scrape_completed(self, summary: Dict[str, Any]):
        """Notify clients that scraping completed"""
        await self.broadcast({
            "type": "scrape_completed",
            "message": "Data collection completed",
            "data": summary,
            "timestamp": asyncio.get_event_loop().time()
        })

    async def broadcast_price_drop(self, model: str, old_price: float, new_price: float):
        """Notify clients about price drop"""
        drop_percent = ((old_price - new_price) / old_price) * 100
        await self.broadcast({
            "type": "price_drop",
            "model": model,
            "old_price": old_price,
            "new_price": new_price,
            "drop_percent": round(drop_percent, 2),
            "timestamp": asyncio.get_event_loop().time()
        })

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()
