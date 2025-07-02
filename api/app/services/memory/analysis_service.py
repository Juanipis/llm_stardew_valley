import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.db import db
from app.config import settings
from app.services.llm_service import llm_service
from app.services.memory.vector_service import vector_service
from app.services.memory.personality_service import personality_service
from app.services.memory.emotional_state_service import emotional_state_service, Mood

# Import realtime monitor for WebSocket notifications
try:
    from app.websockets.realtime import realtime_monitor

    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    A unified service to perform all post-conversation analysis in a single LLM call.
    This service consolidates the work of:
    - EmotionalStateService (final update)
    - MemoryConsolidationService
    - PersonalityService
    """

    def __init__(self):
        pass

    async def analyze_conversation_and_update_memory(self, conversation_id: str):
        """
        The main method to orchestrate post-conversation analysis and updates.
        """
        logger.info(f"Starting unified analysis for conversation {conversation_id}")
        try:
            # 1. Get all necessary data for the prompt
            analysis_data = await self._get_data_for_analysis(conversation_id)
            if not analysis_data:
                logger.warning(
                    f"Could not gather analysis data for conversation {conversation_id}. Aborting."
                )
                return

            # 2. Build the unified prompt
            prompt = self._build_unified_analysis_prompt(analysis_data)

            # 3. Call the LLM
            messages = [{"role": "user", "content": prompt}]
            response = await llm_service.acompletion(
                model=settings.memory_consolidation_model, messages=messages
            )
            response_text = response.choices[0].message.content

            # 4. Parse and process the response
            analysis_results = json.loads(response_text.strip())
            logger.info(f"🔍 ANALYSIS COMPLETE for conversation {conversation_id}")
            logger.info(f"🔍 Analysis results keys: {list(analysis_results.keys())}")

            # 5. Process the results and update the database
            logger.info("🔄 PROCESSING ANALYSIS RESULTS...")
            await self._process_analysis_results(analysis_data, analysis_results)

            logger.info(
                f"Unified analysis for conversation {conversation_id} complete."
            )

        except Exception as e:
            logger.error(
                f"Error during unified analysis for conversation {conversation_id}: {e}"
            )

    async def _get_data_for_analysis(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Gathers all data needed for the unified analysis prompt."""
        try:
            # Get conversation data (based on memory_consolidation_service)
            conversation = await db.conversation.find_unique(
                where={"id": conversation_id},
                include={
                    "player": True,
                    "npc": True,
                    "dialogueEntries": {"order_by": {"timestamp": "asc"}},
                },
            )
            if not conversation:
                logger.warning(
                    f"Conversation {conversation_id} not found for analysis."
                )
                return None

            dialogue_transcript = "\n".join(
                f"{'Player' if entry.speaker == 'player' else conversation.npc.name}: {entry.message}"
                for entry in conversation.dialogueEntries
            )

            player_id = conversation.playerId
            npc_id = conversation.npcId

            # Get current personality, emotional state, and memories
            personality_profile = await personality_service.get_personality_profile(
                player_id, npc_id
            )
            emotional_state = await emotional_state_service.get_emotional_state(npc_id)
            relevant_memories = await vector_service.search_relevant_memories(
                player_id, npc_id, "our past interactions"
            )

            return {
                "conversation_id": conversation_id,
                "player_id": player_id,
                "npc_id": npc_id,
                "player_name": conversation.player.name,
                "npc_name": conversation.npc.name,
                "transcript": dialogue_transcript,
                "context": {
                    "season": conversation.season,
                    "location": conversation.playerLocation,
                    "friendship_hearts": conversation.friendshipHearts,
                },
                "current_personality": personality_profile,
                "current_emotional_state": emotional_state,
                "long_term_memories": relevant_memories,
            }
        except Exception as e:
            logger.error(f"Failed to gather data for analysis: {e}")
            return None

    def _build_unified_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Builds the single, comprehensive prompt for the LLM."""

        memories_str = (
            "\n".join(
                f"- {'You said' if m['speaker'] == data['npc_name'] else 'They said'}: '{m['message']}'"
                for m in data["long_term_memories"]
            )
            if data["long_term_memories"]
            else "No specific long-term memories stand out right now."
        )

        valid_moods = ", ".join([mood.value for mood in Mood])

        prompt = f"""You are an AI specialized in psychology, memory, and character simulation. Your task is to analyze a conversation from the perspective of {data["npc_name"]} from Stardew Valley and update their internal state.

**NPC Profile: {data["npc_name"]}**
**Player Profile: {data["player_name"]}**

**Current Emotional State (before this conversation):**
- Mood: {data["current_emotional_state"]["current_mood"]} (Intensity: {data["current_emotional_state"]["mood_intensity"]}/10)

**Current Personality Profile of {data["player_name"]} (from {data["npc_name"]}'s perspective):**
- Summary: {data["current_personality"]["summary"]}
- Trust: {data["current_personality"]["trust"]}/10
- Affection: {data["current_personality"]["affection"]}/10
- Annoyance: {data["current_personality"]["annoyance"]}/10
- (Other metrics exist but these are key for the summary)

**Key Long-Term Memories:**
{memories_str}

**Conversation Transcript to Analyze:**
{data["transcript"]}

**ANALYSIS INSTRUCTIONS**
Based on EVERYTHING above, perform a comprehensive analysis and provide the output in a single, clean JSON object.

1.  **Sentiment of Final Player Response**: Analyze the sentiment of the last message from the player.
2.  **Memory Consolidation**: Extract key memories, learned facts, and relationship milestones.
3.  **Emotional State Update**: Determine the NPC's new emotional state after the conversation.
4.  **Personality Profile Update**: Adjust the NPC's personality perception of the player.

**JSON OUTPUT FORMAT (Strictly Adhere to this):**
{{
  "final_player_sentiment": {{
    "score": "A float from -1.0 (very negative) to 1.0 (very positive) based on the last player message"
  }},
  "memory_consolidation": {{
    "episodic_memories": [
      {{
        "title": "Brief memorable title",
        "description": "Detailed description of what happened",
        "emotional_impact": 7.5,
        "importance": 8.0,
        "memory_type": "GIFT_RECEIVED/SHARED_ACTIVITY/EMOTIONAL_MOMENT/etc"
      }}
    ],
    "learned_preferences": [
      {{
        "category": "GIFTS/ACTIVITIES/TOPICS/FOODS",
        "item": "Specific thing learned about",
        "preference_level": 8.0,
        "evidence": "What the player said/did that revealed this"
      }}
    ]
  }},
  "emotional_state_update": {{
    "new_mood": "A mood from this list: {valid_moods}",
    "new_mood_intensity": 7.0,
    "mood_reason": "Briefly explain why their mood changed.",
    "interaction_summary": "A one-sentence summary of the interaction's emotional effect."
  }},
  "personality_profile_update": {{
    "new_summary": "A new, concise (max 60 words) summary of your feelings towards the player.",
    "new_trust": 7.5,
    "new_affection": 6.0,
    "new_annoyance": 2.5,
    "new_friendliness": 7.0,
    "new_sincerity": 8.0,
    "new_romantic_interest": 3.0
  }}
}}

**Guidelines:**
- If nothing significant happened for a section (e.g., no new memories), return an empty array `[]`.
- All numeric scores are out of 10.
- Make meaningful adjustments. Be bold in your analysis. A rude conversation should tank relationship scores. A heartfelt one should boost them significantly.
"""
        return prompt

    async def _process_analysis_results(
        self, analysis_data: Dict[str, Any], analysis_results: Dict[str, Any]
    ):
        """Processes the LLM's analysis and updates the database."""
        logger.info(
            f"Processing analysis results for conversation {analysis_data['conversation_id']}"
        )

        player_id = analysis_data["player_id"]
        npc_id = analysis_data["npc_id"]

        # 1. Process memory consolidation
        if "memory_consolidation" in analysis_results:
            mem_con = analysis_results["memory_consolidation"]
            await self._create_episodic_memories_in_db(
                player_id, npc_id, analysis_data, mem_con.get("episodic_memories", [])
            )
            await self._update_player_preferences_in_db(
                player_id, npc_id, mem_con.get("learned_preferences", [])
            )

        # 2. Process emotional state update
        if "emotional_state_update" in analysis_results:
            emo_update = analysis_results["emotional_state_update"]
            await self._update_emotional_state_in_db(npc_id, player_id, emo_update)

        # 3. Process personality profile update
        if "personality_profile_update" in analysis_results:
            pers_update = analysis_results["personality_profile_update"]
            await self._update_personality_in_db(player_id, npc_id, pers_update)

        # 4. Process sentiment and update friendship points
        if "final_player_sentiment" in analysis_results:
            sentiment_score = float(
                analysis_results["final_player_sentiment"].get("score", 0.0)
            )
            await self._update_friendship_points_in_db(
                player_id, npc_id, sentiment_score
            )

    async def _update_personality_in_db(
        self, player_id: str, npc_id: str, update_data: Dict[str, Any]
    ):
        """Updates the player personality profile in the database."""
        try:
            # Get old profile for comparison if realtime notifications are enabled
            old_profile = None
            if REALTIME_AVAILABLE:
                try:
                    old_profile = await personality_service.get_personality_profile(
                        player_id, npc_id
                    )
                except Exception as e:
                    logger.error(
                        f"Error getting old personality profile for notification: {e}"
                    )

            db_update_data = {
                "summary": update_data.get("new_summary"),
                "trust": float(update_data.get("new_trust")),
                "affection": float(update_data.get("new_affection")),
                "annoyance": float(update_data.get("new_annoyance")),
                "friendliness": float(update_data.get("new_friendliness")),
                "sincerity": float(update_data.get("new_sincerity")),
                "romantic_interest": float(update_data.get("new_romantic_interest")),
            }
            # Remove None values so we don't overwrite existing values with nulls if keys are missing
            db_update_data = {k: v for k, v in db_update_data.items() if v is not None}

            if not db_update_data:
                logger.warning("No personality data to update.")
                return

            logger.info(
                f"🧠 UPDATING PERSONALITY PROFILE: Player {player_id} -> NPC {npc_id}"
            )
            logger.info(f"🧠 Changes: {db_update_data}")

            await db.playerpersonalityprofile.update(
                where={"playerId_npcId": {"playerId": player_id, "npcId": npc_id}},
                data=db_update_data,
            )
            logger.info(
                f"✅ Successfully updated personality profile for player {player_id} with NPC {npc_id}"
            )

            # Send real-time notification for personality update
            if REALTIME_AVAILABLE and old_profile:
                try:
                    # Get player and NPC names
                    player = await db.player.find_unique(where={"id": player_id})
                    npc = await db.npc.find_unique(where={"id": npc_id})

                    if player and npc:
                        # Get new profile
                        new_profile = await personality_service.get_personality_profile(
                            player_id, npc_id
                        )

                        await realtime_monitor.notify_personality_update(
                            player.name, npc.name, old_profile, new_profile
                        )
                except Exception as e:
                    logger.error(f"Error sending personality update notification: {e}")

        except Exception as e:
            logger.error(f"Error updating personality profile in DB: {e}")

    async def _update_emotional_state_in_db(
        self, npc_id: str, player_id: str, update_data: Dict[str, Any]
    ):
        """Updates the NPC's emotional state in the database."""
        try:
            # Get old emotional state for comparison if realtime notifications are enabled
            old_emotional_state = None
            if REALTIME_AVAILABLE:
                try:
                    old_emotional_state = (
                        await emotional_state_service.get_emotional_state(
                            npc_id, player_id
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Error getting old emotional state for notification: {e}"
                    )

            db_update_data = {
                "currentMood": update_data.get("new_mood"),
                "moodIntensity": float(update_data.get("new_mood_intensity")),
                "lastInteractionEffect": update_data.get("interaction_summary"),
                "lastUpdated": datetime.now(),
            }
            db_update_data = {k: v for k, v in db_update_data.items() if v is not None}

            if not db_update_data:
                logger.warning("No emotional state data to update.")
                return

            await db.emotionalstate.upsert(
                where={"npcId_playerId": {"npcId": npc_id, "playerId": player_id}},
                data={
                    "update": db_update_data,
                    "create": {
                        "npcId": npc_id,
                        "playerId": player_id,
                        "currentMood": update_data.get("new_mood", "NEUTRAL"),
                        "moodIntensity": float(
                            update_data.get("new_mood_intensity", 5.0)
                        ),
                        "lastInteractionEffect": update_data.get(
                            "interaction_summary", ""
                        ),
                    },
                },
            )
            logger.info(
                f"Updated emotional state for NPC {npc_id} towards player {player_id}"
            )

            # Send real-time notification for emotional state change
            if REALTIME_AVAILABLE and old_emotional_state:
                try:
                    # Get NPC name
                    npc = await db.npc.find_unique(where={"id": npc_id})

                    if npc:
                        # Get new emotional state
                        new_emotional_state = (
                            await emotional_state_service.get_emotional_state(
                                npc_id, player_id
                            )
                        )

                        await realtime_monitor.notify_emotional_state_change(
                            npc.name, old_emotional_state, new_emotional_state
                        )
                except Exception as e:
                    logger.error(
                        f"Error sending emotional state change notification: {e}"
                    )

        except Exception as e:
            logger.error(f"Error updating emotional state in DB: {e}")

    async def _create_episodic_memories_in_db(
        self,
        player_id: str,
        npc_id: str,
        analysis_data: Dict[str, Any],
        memories: List[Dict[str, Any]],
    ):
        """Creates episodic memory entries in the database."""
        try:
            for memory in memories:
                logger.info(f"Creating episodic memory: {memory.get('title')}")
                memory_text = (
                    f"{memory.get('title', '')} - {memory.get('description', '')}"
                )
                embedding = await vector_service.generate_embedding(memory_text)

                # TODO: This depends on a 'MemoryEpisode' model in prisma.schema
                # For now, this will just log. Once the model exists, un-comment the DB call.
                logger.info(
                    f"Would create memory episode for player {player_id}: {memory.get('title')}"
                )
                # await db.memoryepisode.create(data={...})
        except Exception as e:
            logger.error(f"Error creating episodic memories in DB: {e}")

    async def _update_player_preferences_in_db(
        self, player_id: str, npc_id: str, preferences: List[Dict[str, Any]]
    ):
        """Updates player preferences learned by the NPC in the database."""
        try:
            for pref in preferences:
                logger.info(f"Updating player preference: {pref.get('item')}")
                # TODO: This depends on a 'PlayerPreference' model in prisma.schema
                # For now, this will just log. Once the model exists, un-comment the DB call.
                logger.info(
                    f"Would update preference for player {player_id}: {pref.get('item')} -> {pref.get('preference_level')}"
                )
                # await db.playerpreference.upsert(where={...}, data={...}, create={...})
        except Exception as e:
            logger.error(f"Error updating player preferences in DB: {e}")

    async def _update_friendship_points_in_db(
        self, player_id: str, npc_id: str, sentiment_score: float
    ):
        """
        Updates the friendship points between player and NPC based on sentiment.
        This logic was moved from the dialogue router.
        """
        try:
            # A heart is 250 points. A score of 1.0 gives 20 points, -1.0 gives -20.
            # It takes about 12-13 max-positive interactions to gain a heart.
            friendship_change = int(round(sentiment_score * 20))

            if friendship_change == 0:
                return

            # We need to get the current friendship and update it.
            # This assumes the 'friendship_hearts' is a proxy for points.
            # A more robust system would store the raw points value.
            # For now, we'll work with what we have.
            # Let's assume the friendship change is stored somewhere else or we simulate it here.
            # This part of the logic needs to be connected to the actual friendship model.
            logger.info(
                f"Friendship change of {friendship_change} points for player {player_id} with NPC {npc_id} would be applied here."
            )
            # Example DB call (if raw friendship points were stored on the Conversation or a dedicated model):
            # await db.friendship.update(
            #     where={"playerId": player_id, "npcId": npc_id},
            #     data={"points": {"increment": friendship_change}}
            # )
        except Exception as e:
            logger.error(f"Error updating friendship points in DB: {e}")


analysis_service = AnalysisService()
