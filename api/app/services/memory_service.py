# flake8: noqa
import logging
from typing import List, Optional, Dict, Any

# Este archivo ahora actúa como una fachada (Facade) para los sub-servicios,
# manteniendo la compatibilidad con los routers que lo utilizan.

from app.services.memory.entity_service import get_or_create_player, get_or_create_npc
from app.services.memory.personality_service import personality_service
from app.services.memory.conversation_service import (
    get_or_create_active_conversation,
    add_dialogue_entry,
    end_conversation,
)
from app.services.memory.vector_service import vector_service

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Servicio de orquestación para la memoria y personalidad de los NPCs.
    Delega las llamadas a los servicios modulares correspondientes.
    """

    async def get_or_create_player(self, player_name: str) -> str:
        """Delega a entity_service."""
        return await get_or_create_player(player_name)

    async def get_or_create_npc(
        self, npc_name: str, npc_location: Optional[str] = None
    ) -> str:
        """Delega a entity_service."""
        return await get_or_create_npc(npc_name, npc_location)

    async def get_personality_profile(
        self, player_id: str, npc_id: str
    ) -> Dict[str, Any]:
        """Delega a personality_service."""
        return await personality_service.get_personality_profile(player_id, npc_id)

    async def search_relevant_memories(
        self, player_id: str, npc_id: str, query_text: str
    ) -> List[Dict[str, Any]]:
        """Delega a vector_service."""
        return await vector_service.search_relevant_memories(
            player_id, npc_id, query_text
        )

    async def get_or_create_active_conversation(
        self, player_id: str, npc_id: str, context: Dict[str, Any]
    ) -> str:
        """Delega a conversation_service."""
        return await get_or_create_active_conversation(player_id, npc_id, context)

    async def add_dialogue_entry(
        self,
        conversation_id: str,
        speaker: str,
        message: str,
        generate_embedding: bool = True,
    ):
        """Delega a conversation_service."""
        await add_dialogue_entry(conversation_id, speaker, message, generate_embedding)

    async def end_conversation(self, conversation_id: str):
        """Delega a conversation_service."""
        await end_conversation(conversation_id)

    async def update_personality_profile_async(self, conversation_id: str):
        """Delega la actualización de personalidad (en segundo plano) a personality_service."""
        await personality_service.update_personality_profile_async(conversation_id)

    async def generate_relationship_insight(
        self,
        personality_profile: Dict[str, Any],
        player_name: str,
        npc_name: str,
        npc_id: str = None,
        player_id: str = None,
    ) -> str:
        """Delega a personality_service con información del estado emocional."""
        return await personality_service.generate_relationship_insight(
            personality_profile, player_name, npc_name, npc_id, player_id
        )


# Instancia global del servicio para mantener la compatibilidad con los routers.
memory_service = MemoryService()
