# api/routers/websocket.py
"""
WebSocket endpoints for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from core.websocket import manager
from core.logging import get_logger
from storage.repo import GPURepository
from api.dependencies import get_db
import asyncio

logger = get_logger("websocket.router")

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates

    Connection flow:
    1. Client connects via ws://localhost:8000/api/ws
    2. Server sends welcome message
    3. Server broadcasts updates when:
       - New data is scraped
       - Statistics are updated
       - Price drops are detected
    4. Client receives JSON messages with type and data
    """
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()

            # Handle client messages
            if data == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "status": "ok"},
                    websocket
                )
            elif data == "get_stats":
                # Client requested stats update
                # This would trigger a stats fetch and send
                await manager.send_personal_message(
                    {
                        "type": "stats_request_received",
                        "message": "Fetching latest statistics..."
                    },
                    websocket
                )
            else:
                logger.debug(f"Received unknown message: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/ws/connections", tags=["🔌 WebSocket"])
def get_websocket_connections():
    """
    Get number of active WebSocket connections

    Returns the count of currently connected clients
    """
    return {
        "active_connections": manager.get_connection_count(),
        "total_connections": manager.connection_count
    }
