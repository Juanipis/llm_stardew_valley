import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..websockets.realtime import realtime_monitor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/monitoring")
async def websocket_monitoring_endpoint(
    websocket: WebSocket, connection_type: str = Query(default="dashboard")
):
    """WebSocket endpoint for real-time monitoring updates"""
    await realtime_monitor.connect(websocket, connection_type)

    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")

            # You can add message handling here if needed
            # For now, we just log the message

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await realtime_monitor.disconnect(websocket)
