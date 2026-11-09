import logging
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone

from ..db import db
from ..services.memory_service import memory_service
from ..services.memory.emotional_state_service import emotional_state_service
from ..services.memory.personality_service import personality_service
from ..services.memory.vector_service import vector_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def monitoring_dashboard(request: Request):
    """Main monitoring dashboard page"""
    return templates.TemplateResponse(
        "monitoring_dashboard.html",
        {"request": request, "title": "StardewEchoes - NPC Monitoring Dashboard"},
    )


@router.get("/player/{player_name}/npc/{npc_name}", response_class=HTMLResponse)
async def player_npc_detail(request: Request, player_name: str, npc_name: str):
    """Detailed view of a specific player-NPC relationship"""
    return templates.TemplateResponse(
        "player_npc_detail.html",
        {
            "request": request,
            "player_name": player_name,
            "npc_name": npc_name,
            "title": f"StardewEchoes - {player_name} & {npc_name}",
        },
    )


@router.get("/api/active_conversations")
async def get_active_conversations():
    """Get all currently active conversations"""
    try:
        # Use timezone-aware datetime to match database timestamps
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=30
        )  # 30 minutes timeout

        conversations = await db.conversation.find_many(
            where={"endTime": None, "startTime": {"gte": cutoff_time}},
            include={
                "player": True,
                "npc": True,
                "dialogueEntries": {"order_by": {"timestamp": "desc"}, "take": 1},
            },
            order={"startTime": "desc"},
        )

        active_convs = []
        for conv in conversations:
            last_message = conv.dialogueEntries[0] if conv.dialogueEntries else None
            active_convs.append(
                {
                    "id": conv.id,
                    "player_name": conv.player.name,
                    "npc_name": conv.npc.name,
                    "start_time": conv.startTime.isoformat(),
                    "location": conv.playerLocation,
                    "season": conv.season,
                    "friendship_hearts": conv.friendshipHearts,
                    "last_message": {
                        "speaker": last_message.speaker,
                        "message": last_message.message,
                        "timestamp": last_message.timestamp.isoformat(),
                    }
                    if last_message
                    else None,
                    "duration_minutes": (
                        datetime.now(timezone.utc) - conv.startTime
                    ).total_seconds()
                    / 60,
                }
            )

        return {"active_conversations": active_convs}
    except Exception as e:
        logger.error(f"Error getting active conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/recent_conversations")
async def get_recent_conversations(limit: int = Query(default=10, le=50)):
    """Get recently completed conversations"""
    try:
        conversations = await db.conversation.find_many(
            where={"endTime": {"not": None}},
            include={"player": True, "npc": True, "dialogueEntries": True},
            order={"endTime": "desc"},
            take=limit,
        )

        recent_convs = []
        for conv in conversations:
            duration = (conv.endTime - conv.startTime).total_seconds() / 60
            message_count = len(conv.dialogueEntries)

            recent_convs.append(
                {
                    "id": conv.id,
                    "player_name": conv.player.name,
                    "npc_name": conv.npc.name,
                    "start_time": conv.startTime.isoformat(),
                    "end_time": conv.endTime.isoformat(),
                    "duration_minutes": duration,
                    "message_count": message_count,
                    "location": conv.playerLocation,
                    "season": conv.season,
                    "friendship_hearts": conv.friendshipHearts,
                }
            )

        return {"recent_conversations": recent_convs}
    except Exception as e:
        logger.error(f"Error getting recent conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/player/{player_name}/relationships")
async def get_player_relationships(player_name: str):
    """Get all relationships for a specific player"""
    try:
        player_id = await memory_service.get_or_create_player(player_name)

        # Get all personality profiles for this player
        profiles = await db.playerpersonalityprofile.find_many(
            where={"playerId": player_id}, include={"npc": True}
        )

        relationships = []
        for profile in profiles:
            # Get latest conversation info
            latest_conv = await db.conversation.find_first(
                where={"playerId": player_id, "npcId": profile.npcId},
                order={"startTime": "desc"},
            )

            # Get emotional state for this specific player-NPC relationship
            emotional_state = await emotional_state_service.get_emotional_state(
                profile.npcId, player_id
            )

            relationships.append(
                {
                    "npc_name": profile.npc.name,
                    "npc_id": profile.npcId,
                    "personality": {
                        "summary": profile.summary,
                        "friendliness": float(profile.friendliness),
                        "trust": float(profile.trust),
                        "affection": float(profile.affection),
                        "annoyance": float(profile.annoyance),
                        "romantic_interest": float(profile.romantic_interest),
                        "admiration": float(profile.admiration),
                    },
                    "emotional_state": {
                        "current_mood": emotional_state["current_mood"],
                        "mood_intensity": emotional_state["mood_intensity"],
                        "last_updated": emotional_state["last_updated"].isoformat()
                        if emotional_state["last_updated"]
                        else None,
                    },
                    "last_interaction": {
                        "date": latest_conv.startTime.isoformat()
                        if latest_conv
                        else None,
                        "location": latest_conv.playerLocation if latest_conv else None,
                        "friendship_hearts": latest_conv.friendshipHearts
                        if latest_conv
                        else 0,
                    },
                }
            )

        return {"player_name": player_name, "relationships": relationships}
    except Exception as e:
        logger.error(f"Error getting player relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/npc/{npc_name}/relationships")
async def get_npc_relationships(npc_name: str):
    """Get all relationships for a specific NPC"""
    try:
        npc_id = await memory_service.get_or_create_npc(npc_name)

        profiles = await db.playerpersonalityprofile.find_many(
            where={"npcId": npc_id}, include={"player": True}
        )

        relationships = []
        for profile in profiles:
            latest_conv = await db.conversation.find_first(
                where={"playerId": profile.playerId, "npcId": npc_id},
                order={"startTime": "desc"},
            )

            relationships.append(
                {
                    "player_name": profile.player.name,
                    "player_id": profile.playerId,
                    "personality": {
                        "summary": profile.summary,
                        "friendliness": float(profile.friendliness),
                        "trust": float(profile.trust),
                        "affection": float(profile.affection),
                        "annoyance": float(profile.annoyance),
                        "romantic_interest": float(profile.romantic_interest),
                    },
                    "last_interaction": {
                        "date": latest_conv.startTime.isoformat()
                        if latest_conv
                        else None,
                        "location": latest_conv.playerLocation if latest_conv else None,
                        "friendship_hearts": latest_conv.friendshipHearts
                        if latest_conv
                        else 0,
                    },
                }
            )

        # Get NPC's current emotional state
        emotional_state = await emotional_state_service.get_emotional_state(npc_id)

        return {
            "npc_name": npc_name,
            "emotional_state": emotional_state,
            "relationships": relationships,
        }
    except Exception as e:
        logger.error(f"Error getting NPC relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversation/{conversation_id}/details")
async def get_conversation_details(conversation_id: str):
    """Get detailed information about a specific conversation"""
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
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get personality profile at the time of conversation
        personality_profile = await personality_service.get_personality_profile(
            conversation.playerId, conversation.npcId
        )

        # Get emotional state
        emotional_state = await emotional_state_service.get_emotional_state(
            conversation.npcId
        )

        dialogue_entries = [
            {
                "id": entry.id,
                "speaker": entry.speaker,
                "message": entry.message,
                "timestamp": entry.timestamp.isoformat(),
            }
            for entry in conversation.dialogueEntries
        ]

        return {
            "conversation": {
                "id": conversation.id,
                "player_name": conversation.player.name,
                "npc_name": conversation.npc.name,
                "start_time": conversation.startTime.isoformat(),
                "end_time": conversation.endTime.isoformat()
                if conversation.endTime
                else None,
                "location": conversation.playerLocation,
                "season": conversation.season,
                "friendship_hearts": conversation.friendshipHearts,
                "dialogue_entries": dialogue_entries,
            },
            "context": {
                "personality_profile": personality_profile,
                "emotional_state": emotional_state,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/stats/overview")
async def get_overview_stats():
    """Get overall system statistics"""
    try:
        # Count total entities
        total_players = await db.player.count()
        total_npcs = await db.npc.count()
        total_conversations = await db.conversation.count()
        total_dialogue_entries = await db.dialogueentry.count()

        # Count active conversations
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        active_conversations = await db.conversation.count(
            where={"endTime": None, "startTime": {"gte": cutoff_time}}
        )

        # Get conversations today
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        conversations_today = await db.conversation.count(
            where={"startTime": {"gte": today_start}}
        )

        return {
            "total_players": total_players,
            "total_npcs": total_npcs,
            "total_conversations": total_conversations,
            "total_dialogue_entries": total_dialogue_entries,
            "active_conversations": active_conversations,
            "conversations_today": conversations_today,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/memories/search")
async def search_memories(
    player_name: str = Query(..., description="Player name"),
    npc_name: str = Query(..., description="NPC name"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, le=20),
):
    """Search memories between a player and NPC"""
    try:
        player_id = await memory_service.get_or_create_player(player_name)
        npc_id = await memory_service.get_or_create_npc(npc_name)

        memories = await vector_service.search_relevant_memories(
            player_id, npc_id, query, max_memories=limit
        )

        return {
            "query": query,
            "player_name": player_name,
            "npc_name": npc_name,
            "memories": memories,
        }
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/players")
async def get_all_players():
    """Get all players in the system"""
    try:
        players = await db.player.find_many(order={"name": "asc"})
        return {
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "created_at": player.createdAt.isoformat(),
                }
                for player in players
            ]
        }
    except Exception as e:
        logger.error(f"Error getting all players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/npcs")
async def get_all_npcs():
    """Get all NPCs in the system"""
    try:
        npcs = await db.npc.find_many(order={"name": "asc"})
        return {
            "npcs": [
                {
                    "id": npc.id,
                    "name": npc.name,
                    "location": npc.location,
                    "created_at": npc.createdAt.isoformat(),
                }
                for npc in npcs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting all NPCs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/emotional-states")
async def get_all_emotional_states():
    """Get emotional states for all NPC-Player relationships"""
    try:
        # Get all emotional states from the database (now per player-NPC pair)
        emotional_states_db = await db.emotionalstate.find_many(
            include={"npc": True, "player": True}, order={"npc": {"name": "asc"}}
        )

        emotional_states = []
        for state_record in emotional_states_db:
            try:
                # Get the full emotional state data using the service
                state = await emotional_state_service.get_emotional_state(
                    state_record.npcId, state_record.playerId
                )

                emotional_states.append(
                    {
                        "npc_id": state_record.npcId,
                        "npc_name": state_record.npc.name,
                        "npc_location": state_record.npc.location,
                        "player_id": state_record.playerId,
                        "player_name": state_record.player.name,
                        "emotional_state": state,
                        "data_context": "⚠️ DATOS DE PERCEPCIÓN: Estado emocional del NPC hacia este jugador específico",
                    }
                )
            except Exception as e:
                logger.error(
                    f"Error processing emotional state for {state_record.npc.name} towards {state_record.player.name}: {e}"
                )
                continue

        return {
            "emotional_states": emotional_states,
            "total_relationships": len(emotional_states),
            "note": "Cada estado emocional es específico por relación jugador-NPC, no global",
        }
    except Exception as e:
        logger.error(f"Error getting all emotional states: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/health/timezone")
async def test_timezone_fix():
    """Test endpoint to verify timezone fixes are working"""
    try:
        now_utc = datetime.now(timezone.utc)

        # Test active conversations query
        cutoff_time = now_utc - timedelta(minutes=30)
        active_count = await db.conversation.count(
            where={"endTime": None, "startTime": {"gte": cutoff_time}}
        )

        # Test today conversations query
        today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await db.conversation.count(
            where={"startTime": {"gte": today_start}}
        )

        return {
            "status": "✅ All timezone operations working correctly",
            "current_time_utc": now_utc.isoformat(),
            "cutoff_time": cutoff_time.isoformat(),
            "today_start": today_start.isoformat(),
            "active_conversations": active_count,
            "conversations_today": today_count,
            "timestamp": now_utc.isoformat(),
        }

    except Exception as e:
        return {
            "status": "❌ Error in timezone operations",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/api/debug/conversations")
async def debug_conversations():
    """Debug endpoint to check conversation status"""
    try:
        total_conversations = await db.conversation.count()
        completed_conversations = await db.conversation.count(
            where={"endTime": {"not": None}}
        )
        active_conversations = await db.conversation.count(where={"endTime": None})

        # Get recent conversations for debugging
        recent_all = await db.conversation.find_many(
            include={"player": True, "npc": True, "dialogueEntries": True},
            order={"startTime": "desc"},
            take=5,
        )

        conversations_debug = []
        for conv in recent_all:
            conversations_debug.append(
                {
                    "id": conv.id,
                    "player_name": conv.player.name,
                    "npc_name": conv.npc.name,
                    "start_time": conv.startTime.isoformat(),
                    "end_time": conv.endTime.isoformat() if conv.endTime else None,
                    "is_completed": conv.endTime is not None,
                    "message_count": len(conv.dialogueEntries),
                    "location": conv.playerLocation,
                    "season": conv.season,
                    "friendship_hearts": conv.friendshipHearts,
                }
            )

        return {
            "summary": {
                "total_conversations": total_conversations,
                "completed_conversations": completed_conversations,
                "active_conversations": active_conversations,
            },
            "recent_conversations": conversations_debug,
            "status": "healthy"
            if completed_conversations > 0
            else "no_completed_conversations",
        }

    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/conversation/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Get detailed conversation history with timeline and analysis"""
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
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get personality changes during conversation (if we had historical data)
        personality_profile = await personality_service.get_personality_profile(
            conversation.playerId, conversation.npcId
        )

        # Get emotional state
        emotional_state = await emotional_state_service.get_emotional_state(
            conversation.npcId
        )

        # Build detailed dialogue history with timestamps and context
        dialogue_timeline = []
        for entry in conversation.dialogueEntries:
            dialogue_timeline.append(
                {
                    "id": entry.id,
                    "speaker": entry.speaker,
                    "speaker_display_name": conversation.player.name
                    if entry.speaker == "player"
                    else conversation.npc.name,
                    "message": entry.message,
                    "timestamp": entry.timestamp.isoformat(),
                    "time_elapsed": (
                        entry.timestamp - conversation.startTime
                    ).total_seconds(),
                }
            )

        return {
            "conversation": {
                "id": conversation.id,
                "player_name": conversation.player.name,
                "npc_name": conversation.npc.name,
                "start_time": conversation.startTime.isoformat(),
                "end_time": conversation.endTime.isoformat()
                if conversation.endTime
                else None,
                "duration_seconds": (
                    (conversation.endTime or datetime.now(timezone.utc))
                    - conversation.startTime
                ).total_seconds(),
                "location": conversation.playerLocation,
                "season": conversation.season,
                "day_of_week": conversation.dayOfWeek,
                "day_of_month": conversation.dayOfMonth,
                "time_of_day": conversation.timeOfDay,
                "weather": conversation.weather,
                "friendship_hearts": conversation.friendshipHearts,
                "total_messages": len(conversation.dialogueEntries),
            },
            "dialogue_timeline": dialogue_timeline,
            "relationship_context": {
                "personality_profile": personality_profile,
                "emotional_state": emotional_state,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reset-personality")
async def reset_npc_personality(
    npc_name: str = None, player_name: str = None, reset_all: bool = False
):
    """Reset NPC personality profiles"""
    try:
        if reset_all:
            # Reset all personality profiles
            deleted_count = await db.playerpersonalityprofile.delete_many({})
            deleted_emotional = await db.emotionalstate.delete_many({})

            logger.info(
                f"Reset all personality profiles: {deleted_count} profiles, {deleted_emotional} emotional states"
            )

            return {
                "message": "All personality profiles and emotional states have been reset",
                "reset_personalities": deleted_count,
                "reset_emotional_states": deleted_emotional,
            }

        elif npc_name and player_name:
            # Reset specific NPC-Player relationship
            player = await db.player.find_unique(where={"name": player_name})
            npc = await db.npc.find_unique(where={"name": npc_name})

            if not player or not npc:
                raise HTTPException(status_code=404, detail="Player or NPC not found")

            # Delete personality profile
            await db.playerpersonalityprofile.delete_many(
                where={"playerId": player.id, "npcId": npc.id}
            )

            # Delete emotional state
            await db.emotionalstate.delete_many(
                where={"npcId": npc.id, "playerId": player.id}
            )

            logger.info(f"Reset personality for {npc_name} towards {player_name}")

            return {
                "message": f"Reset personality of {npc_name} towards {player_name}",
                "npc_name": npc_name,
                "player_name": player_name,
            }

        elif npc_name:
            # Reset all relationships for specific NPC
            npc = await db.npc.find_unique(where={"name": npc_name})

            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")

            # Delete all personality profiles for this NPC
            deleted_personalities = await db.playerpersonalityprofile.delete_many(
                where={"npcId": npc.id}
            )

            # Delete all emotional states for this NPC
            deleted_emotional = await db.emotionalstate.delete_many(
                where={"npcId": npc.id}
            )

            logger.info(f"Reset all relationships for NPC {npc_name}")

            return {
                "message": f"Reset all relationships for {npc_name}",
                "npc_name": npc_name,
                "reset_personalities": deleted_personalities,
                "reset_emotional_states": deleted_emotional,
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either reset_all=true, npc_name, or both npc_name and player_name",
            )

    except Exception as e:
        logger.error(f"Error resetting personality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics for dashboard"""
    try:
        # Get database statistics
        total_conversations = await db.conversation.count()
        total_dialogue_entries = await db.dialogueentry.count()
        total_players = await db.player.count()
        total_npcs = await db.npc.count()
        total_personalities = await db.playerpersonalityprofile.count()
        total_emotional_states = await db.emotionalstate.count()

        # Get recent activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        conversations_today = await db.conversation.count(
            where={"startTime": {"gte": yesterday}}
        )

        # Get active conversations
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        active_conversations = await db.conversation.count(
            where={"endTime": None, "startTime": {"gte": cutoff_time}}
        )

        # Get conversations by hour for chart data
        last_24h = []
        for i in range(24):
            hour_start = datetime.now(timezone.utc) - timedelta(hours=i + 1)
            hour_end = datetime.now(timezone.utc) - timedelta(hours=i)

            hour_conversations = await db.conversation.count(
                where={"startTime": {"gte": hour_start, "lt": hour_end}}
            )

            last_24h.append(
                {
                    "hour": hour_start.strftime("%H:00"),
                    "conversations": hour_conversations,
                }
            )

        last_24h.reverse()  # Show chronologically

        # Get NPC popularity data using Prisma aggregations (safer)
        npc_popularity = []
        try:
            # Get all NPCs with their conversation counts
            npcs_with_conversations = await db.npc.find_many(
                include={"conversations": True}
            )

            # Calculate conversation counts and format for frontend
            npc_counts = []
            for npc in npcs_with_conversations:
                conversation_count = len(npc.conversations) if npc.conversations else 0
                if conversation_count > 0:  # Only include NPCs with conversations
                    npc_counts.append(
                        {"name": npc.name, "conversation_count": conversation_count}
                    )

            # Sort by conversation count (descending) and take top 10
            npc_popularity = sorted(
                npc_counts, key=lambda x: x["conversation_count"], reverse=True
            )[:10]

        except Exception as popularity_error:
            logger.warning(f"Error getting NPC popularity data: {popularity_error}")
            # Fallback: just get a list of NPCs with 0 counts
            try:
                all_npcs = await db.npc.find_many(take=10)
                npc_popularity = [
                    {"name": npc.name, "conversation_count": 0} for npc in all_npcs
                ]
            except Exception as fallback_error:
                logger.error(f"Fallback NPC query failed: {fallback_error}")
                npc_popularity = []

        return {
            "database_stats": {
                "total_conversations": total_conversations,
                "total_dialogue_entries": total_dialogue_entries,
                "total_players": total_players,
                "total_npcs": total_npcs,
                "total_personalities": total_personalities,
                "total_emotional_states": total_emotional_states,
                "conversations_today": conversations_today,
                "active_conversations": active_conversations,
            },
            "chart_data": {
                "conversations_24h": last_24h,
                "npc_popularity": npc_popularity,
            },
        }

    except Exception as e:
        logger.error(f"Critical error getting system stats: {e}")
        # Return minimal safe response instead of 500 error
        return {
            "database_stats": {
                "total_conversations": 0,
                "total_dialogue_entries": 0,
                "total_players": 0,
                "total_npcs": 0,
                "total_personalities": 0,
                "total_emotional_states": 0,
                "conversations_today": 0,
                "active_conversations": 0,
            },
            "chart_data": {
                "conversations_24h": [],
                "npc_popularity": [],
            },
            "error": f"Error loading statistics: {str(e)}",
        }


@router.delete("/api/admin/clear-data")
async def clear_all_data(confirm: bool = False):
    """Clear all monitoring data (admin only)"""
    if not confirm:
        raise HTTPException(
            status_code=400, detail="Must set confirm=true to clear all data"
        )

    try:
        # Delete all data in reverse dependency order
        deleted_dialogue = await db.dialogueentry.delete_many({})
        deleted_conversations = await db.conversation.delete_many({})
        deleted_personalities = await db.playerpersonalityprofile.delete_many({})
        deleted_emotional = await db.emotionalstate.delete_many({})
        deleted_players = await db.player.delete_many({})
        deleted_npcs = await db.npc.delete_many({})

        logger.warning("All monitoring data has been cleared!")

        return {
            "message": "All monitoring data has been cleared",
            "deleted": {
                "dialogue_entries": deleted_dialogue,
                "conversations": deleted_conversations,
                "personality_profiles": deleted_personalities,
                "emotional_states": deleted_emotional,
                "players": deleted_players,
                "npcs": deleted_npcs,
            },
        }

    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
