import logging
import json
from typing import Set, Dict, Any
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """WebSocket manager for real-time monitoring updates"""

    def __init__(self):
        # Store active WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        # Store connections by type (dashboard, player-npc detail, etc.)
        self.connections_by_type: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, connection_type: str = "dashboard"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

        if connection_type not in self.connections_by_type:
            self.connections_by_type[connection_type] = set()
        self.connections_by_type[connection_type].add(websocket)

        logger.info(
            f"New WebSocket connection: {connection_type}. Total connections: {len(self.active_connections)}"
        )

        # Send initial connection confirmation
        await self.send_to_connection(
            websocket,
            {
                "type": "connection_confirmed",
                "connection_type": connection_type,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)

        # Remove from all connection types
        for conn_type, connections in self.connections_by_type.items():
            connections.discard(websocket)

        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def send_to_connection(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_type(self, connection_type: str, data: Dict[str, Any]):
        """Broadcast data to all connections of a specific type"""
        if connection_type not in self.connections_by_type:
            return

        disconnected = set()
        for websocket in self.connections_by_type[connection_type]:
            try:
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def broadcast_to_all(self, data: Dict[str, Any]):
        """Broadcast data to all active connections"""
        disconnected = set()
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    # Event methods for different types of updates

    async def notify_new_conversation(self, conversation_data: Dict[str, Any]):
        """Notify about a new conversation starting"""
        message = {
            "type": "new_conversation",
            "data": conversation_data,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_all(message)

    async def notify_conversation_ended(self, conversation_data: Dict[str, Any]):
        """Notify about a conversation ending"""
        message = {
            "type": "conversation_ended",
            "data": conversation_data,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_all(message)

    async def notify_new_dialogue(self, dialogue_data: Dict[str, Any]):
        """Notify about new dialogue entry"""
        message = {
            "type": "new_dialogue",
            "data": dialogue_data,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_all(message)

    async def notify_emotional_state_change(
        self, npc_name: str, old_state: Dict[str, Any], new_state: Dict[str, Any]
    ):
        """Notify about NPC emotional state changes"""
        message = {
            "type": "emotional_state_change",
            "data": {
                "npc_name": npc_name,
                "old_state": old_state,
                "new_state": new_state,
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_all(message)

    async def notify_personality_update(
        self,
        player_name: str,
        npc_name: str,
        old_profile: Dict[str, Any],
        new_profile: Dict[str, Any],
    ):
        """Notify about personality profile updates"""
        message = {
            "type": "personality_update",
            "data": {
                "player_name": player_name,
                "npc_name": npc_name,
                "old_profile": old_profile,
                "new_profile": new_profile,
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_all(message)

    async def notify_analysis_complete(
        self, conversation_id: str, analysis_results: Dict[str, Any]
    ):
        """Notify about completed conversation analysis"""
        message = {
            "type": "analysis_complete",
            "data": {
                "conversation_id": conversation_id,
                "analysis_results": analysis_results,
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_all(message)


# Global instance
realtime_monitor = RealtimeMonitor()
