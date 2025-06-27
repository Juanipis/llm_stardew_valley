import logging
from typing import Optional
from app.db import db

logger = logging.getLogger(__name__)


async def get_or_create_player(player_name: str) -> str:
    """Obtiene o crea un jugador y retorna su ID"""
    try:
        player = await db.player.find_unique(where={"name": player_name})
        if player:
            logger.debug(f"Found existing player {player_name} with id {player.id}")
            return player.id

        logger.debug(f"Creating new player: {player_name}")
        new_player = await db.player.create(data={"name": player_name})
        logger.info(f"Created new player {player_name} with id {new_player.id}")
        return new_player.id
    except Exception as e:
        logger.error(f"Error in get_or_create_player for '{player_name}': {e}")
        return ""


async def get_or_create_npc(npc_name: str, npc_location: Optional[str] = None) -> str:
    """Obtiene o crea un NPC y retorna su ID"""
    try:
        npc = await db.npc.find_unique(where={"name": npc_name})
        if npc:
            # Optionally update location if it's different
            if npc_location and npc.location != npc_location:
                await db.npc.update(
                    where={"id": npc.id}, data={"location": npc_location}
                )
            return npc.id

        logger.debug(f"Creating new NPC: {npc_name}")
        new_npc = await db.npc.create(data={"name": npc_name, "location": npc_location})
        logger.info(f"Created new NPC {npc_name} with id {new_npc.id}")
        return new_npc.id
    except Exception as e:
        logger.error(f"Error in get_or_create_npc for '{npc_name}': {e}")
        return ""
