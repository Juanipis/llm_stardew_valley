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
    try:
        await realtime_monitor.connect(websocket, connection_type)

        while True:
            # Keep connection alive and handle any incoming messages
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")

                # Handle ping/pong messages to keep connection alive
                if data == "ping":
                    # Send pong as a structured message for consistency
                    await websocket.send_text("pong")
                    logger.debug("Sent pong response to keep-alive ping")
                    continue

                # Handle other control messages
                if data in ["heartbeat", "keepalive"]:
                    await websocket.send_text("ack")
                    logger.debug(f"Acknowledged {data} message")
                    continue

                # If it's not a control message, try to process it as JSON
                try:
                    import json

                    json_data = json.loads(data)
                    logger.info(f"Received structured message: {json_data}")
                    # Here you could add more sophisticated message handling
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message: {data}")

            except Exception as msg_error:
                logger.debug(f"WebSocket message error: {msg_error}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected ({connection_type})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await realtime_monitor.disconnect(websocket)
