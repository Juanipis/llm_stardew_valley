import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from app.db import db
from app.config import settings
from app.services.memory.vector_service import vector_service

logger = logging.getLogger(__name__)

# Import realtime monitor for WebSocket notifications
try:
    from app.websockets.realtime import realtime_monitor

    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False
    logger.warning("Realtime monitor not available, WebSocket notifications disabled")


async def get_or_create_active_conversation(
    player_id: str, npc_id: str, context: Dict[str, Any]
) -> str:
    """Obtiene una conversación activa o crea una nueva, usando Prisma."""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=settings.conversation_timeout_minutes
        )

        active_conversation = await db.conversation.find_first(
            where={
                "playerId": player_id,
                "npcId": npc_id,
                "endTime": None,
                "startTime": {"gte": cutoff_time},
            },
            order={"startTime": "desc"},
        )

        if active_conversation:
            logger.debug(f"Found active conversation: {active_conversation.id}")
            return active_conversation.id

        logger.debug("No active conversation found, creating a new one.")
        new_conversation = await db.conversation.create(
            data={
                "playerId": player_id,
                "npcId": npc_id,
                "season": context.get("season"),
                "dayOfMonth": context.get("day_of_month"),
                "dayOfWeek": context.get("day_of_week"),
                "timeOfDay": context.get("time_of_day"),
                "year": context.get("year"),
                "weather": context.get("weather"),
                "playerLocation": context.get("player_location"),
                "friendshipHearts": context.get("friendship_hearts"),
            }
        )
        logger.info(f"Created new conversation: {new_conversation.id}")

        # Send real-time notification for new conversation
        if REALTIME_AVAILABLE:
            try:
                # Get player and NPC names for the notification
                player = await db.player.find_unique(where={"id": player_id})
                npc = await db.npc.find_unique(where={"id": npc_id})

                if player and npc:
                    await realtime_monitor.notify_new_conversation(
                        {
                            "conversation_id": new_conversation.id,
                            "player_name": player.name,
                            "npc_name": npc.name,
                            "location": context.get("player_location"),
                            "season": context.get("season"),
                            "friendship_hearts": context.get("friendship_hearts", 0),
                            "start_time": new_conversation.startTime.isoformat(),
                        }
                    )
            except Exception as e:
                logger.error(f"Error sending new conversation notification: {e}")

        return new_conversation.id
    except Exception as e:
        logger.error(f"Error en get_or_create_active_conversation: {e}")
        return ""


async def add_dialogue_entry(
    conversation_id: str,
    speaker: str,
    message: str,
    generate_embedding: bool = True,
):
    """Enhanced dialogue entry creation with proper embedding support."""
    try:
        # Generate embedding for the message if requested
        embedding = []
        if generate_embedding:
            embedding = await vector_service.generate_embedding(message)
            if embedding:
                logger.debug(
                    f"Generated embedding with {len(embedding)} dimensions for message: {message[:50]}..."
                )
            else:
                logger.warning(
                    f"Failed to generate embedding for message: {message[:50]}..."
                )

        # Create dialogue entry data
        dialogue_data = {
            "conversationId": conversation_id,
            "speaker": speaker,
            "message": message,
        }

        if embedding:
            # Use raw SQL to insert with vector embedding
            # This is necessary because Prisma doesn't natively support vector types
            await db.execute_raw(
                """
                INSERT INTO "DialogueEntry" (id, "conversationId", speaker, message, embedding, timestamp)
                VALUES (gen_random_uuid(), $1, $2, $3, $4::vector, NOW())
                """,
                conversation_id,
                speaker,
                message,
                f"[{','.join(map(str, embedding))}]",  # Format vector for PostgreSQL
            )
            logger.debug(f"Saved dialogue entry with embedding for speaker '{speaker}'")
        else:
            # Fallback to regular Prisma insert without embedding
            await db.dialogueentry.create(data=dialogue_data)
            logger.debug(
                f"Saved dialogue entry without embedding for speaker '{speaker}'"
            )

        logger.debug(
            f"Added dialogue entry for speaker '{speaker}' to conversation '{conversation_id}'"
        )

    except Exception as e:
        logger.error(f"Error al añadir entrada de diálogo: {e}")
        # Fallback: try to save without embedding
        try:
            dialogue_data = {
                "conversationId": conversation_id,
                "speaker": speaker,
                "message": message,
            }
            await db.dialogueentry.create(data=dialogue_data)
            logger.info("Saved dialogue entry without embedding as fallback")
        except Exception as fallback_error:
            logger.error(f"Fallback save also failed: {fallback_error}")


async def end_conversation(conversation_id: str):
    """Marca una conversación como terminada estableciendo su 'endTime'."""
    try:
        # Get conversation details before ending for notification
        conversation_data = None
        if REALTIME_AVAILABLE:
            try:
                conversation = await db.conversation.find_unique(
                    where={"id": conversation_id}, include={"player": True, "npc": True}
                )
                if conversation:
                    conversation_data = {
                        "conversation_id": conversation_id,
                        "player_name": conversation.player.name,
                        "npc_name": conversation.npc.name,
                        "location": conversation.playerLocation,
                        "duration_minutes": (
                            datetime.now(timezone.utc) - conversation.startTime
                        ).total_seconds()
                        / 60,
                        "end_time": datetime.now(timezone.utc).isoformat(),
                    }
            except Exception as e:
                logger.error(f"Error preparing conversation end notification: {e}")

        await db.conversation.update(
            where={"id": conversation_id}, data={"endTime": datetime.now(timezone.utc)}
        )
        logger.info(f"Conversation {conversation_id} has ended.")

        # Send real-time notification for conversation end
        if REALTIME_AVAILABLE and conversation_data:
            try:
                await realtime_monitor.notify_conversation_ended(conversation_data)
            except Exception as e:
                logger.error(f"Error sending conversation end notification: {e}")

    except Exception as e:
        logger.error(f"Error al finalizar la conversación {conversation_id}: {e}")


async def get_conversation_summary(conversation_id: str) -> Dict[str, Any]:
    """
    Get a summary of a conversation for memory analysis.

    Returns conversation data with dialogue entries and context.
    """
    try:
        conversation = await db.conversation.find_unique(
            where={"id": conversation_id},
            include={
                "player": True,
                "npc": True,
                "dialogueEntries": {"order_by": {"timestamp": "asc"}},
            },
        )

        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return {}

        # Calculate conversation duration
        start_time = conversation.startTime
        end_time = conversation.endTime or datetime.now(timezone.utc)
        duration_minutes = (end_time - start_time).total_seconds() / 60

        # Count dialogue entries by speaker
        player_messages = sum(
            1 for entry in conversation.dialogueEntries if entry.speaker == "player"
        )
        npc_messages = sum(
            1 for entry in conversation.dialogueEntries if entry.speaker != "player"
        )

        return {
            "conversation_id": conversation_id,
            "player_name": conversation.player.name,
            "npc_name": conversation.npc.name,
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration_minutes,
            "total_messages": len(conversation.dialogueEntries),
            "player_messages": player_messages,
            "npc_messages": npc_messages,
            "context": {
                "season": conversation.season,
                "location": conversation.playerLocation,
                "friendship_hearts": conversation.friendshipHearts,
                "weather": conversation.weather,
                "game_date": f"{conversation.season} {conversation.dayOfMonth}, Year {conversation.year}"
                if conversation.season
                else None,
            },
            "dialogue_entries": [
                {
                    "speaker": entry.speaker,
                    "message": entry.message,
                    "timestamp": entry.timestamp,
                }
                for entry in conversation.dialogueEntries
            ],
        }

    except Exception as e:
        logger.error(f"Error getting conversation summary for {conversation_id}: {e}")
        return {}


async def search_conversations_by_context(
    player_id: str,
    npc_id: str,
    location: str = None,
    season: str = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search for past conversations based on contextual filters.

    Useful for contextual memory triggers like:
    - "Last time we were at the saloon..."
    - "This reminds me of last winter when..."
    """
    try:
        where_conditions = {
            "playerId": player_id,
            "npcId": npc_id,
            "endTime": {"not": None},  # Only completed conversations
        }

        if location:
            where_conditions["playerLocation"] = location
        if season:
            where_conditions["season"] = season

        conversations = await db.conversation.find_many(
            where=where_conditions,
            order={"endTime": "desc"},
            take=limit,
            include={"dialogueEntries": True},
        )

        return [
            {
                "conversation_id": conv.id,
                "start_time": conv.startTime,
                "end_time": conv.endTime,
                "location": conv.playerLocation,
                "season": conv.season,
                "friendship_hearts": conv.friendshipHearts,
                "message_count": len(conv.dialogueEntries),
            }
            for conv in conversations
        ]

    except Exception as e:
        logger.error(f"Error searching conversations by context: {e}")
        return []
