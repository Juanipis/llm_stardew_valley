import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from google import genai
from app.db import db
from app.config import settings
from app.services.memory.vector_service import vector_service

logger = logging.getLogger(__name__)


class MemoryConsolidationService:
    """
    Service that processes raw conversations into meaningful, human-like memories.

    Mimics human memory consolidation by:
    1. Extracting important events from conversations
    2. Learning player preferences
    3. Identifying relationship milestones
    4. Creating episodic memories with emotional weight
    """

    def __init__(self):
        if settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        else:
            self.client = None

    async def consolidate_conversation(self, conversation_id: str):
        """
        Main consolidation method - processes a completed conversation.

        Extracts:
        1. Important events/moments (MemoryEpisodes)
        2. Learned preferences about the player
        3. Relationship milestones reached
        4. Emotional impact assessment
        """
        try:
            if not self.client:
                logger.warning("Gemini client not available for memory consolidation")
                return

            # Get conversation data
            conversation_data = await self._get_conversation_data(conversation_id)
            if not conversation_data:
                logger.warning(f"No conversation data found for {conversation_id}")
                return

            logger.info(
                f"Consolidating memories for conversation between {conversation_data['player_name']} and {conversation_data['npc_name']}"
            )

            # Extract meaningful memories using LLM
            memory_analysis = await self._analyze_conversation_for_memories(
                conversation_data
            )

            # Process the analysis into database updates
            await self._process_memory_analysis(conversation_data, memory_analysis)

            logger.info(
                f"Memory consolidation completed for conversation {conversation_id}"
            )

        except Exception as e:
            logger.error(f"Error consolidating conversation {conversation_id}: {e}")

    async def _get_conversation_data(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve conversation data with all dialogue entries."""
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
                return None

            # Format the conversation for analysis
            dialogue_transcript = []
            for entry in conversation.dialogueEntries:
                speaker = (
                    "Player" if entry.speaker == "player" else conversation.npc.name
                )
                dialogue_transcript.append(f"{speaker}: {entry.message}")

            return {
                "conversation_id": conversation_id,
                "player_id": conversation.playerId,
                "npc_id": conversation.npcId,
                "player_name": conversation.player.name,
                "npc_name": conversation.npc.name,
                "transcript": "\n".join(dialogue_transcript),
                "context": {
                    "season": conversation.season,
                    "location": conversation.playerLocation,
                    "friendship_hearts": conversation.friendshipHearts,
                    "game_date": f"{conversation.season} {conversation.dayOfMonth}, Year {conversation.year}"
                    if conversation.season
                    else None,
                },
                "start_time": conversation.startTime,
                "end_time": conversation.endTime or datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error retrieving conversation data: {e}")
            return None

    async def _analyze_conversation_for_memories(
        self, conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze conversation and extract meaningful memories."""

        prompt = f"""You are an AI specialized in human memory and psychology. Analyze this conversation from {conversation_data["npc_name"]}'s perspective to extract meaningful memories.

**Conversation Context:**
- NPCs: {conversation_data["npc_name"]} talking with {conversation_data["player_name"]}
- Location: {conversation_data["context"].get("location", "Unknown")}
- Season: {conversation_data["context"].get("season", "Unknown")}
- Friendship Level: {conversation_data["context"].get("friendship_hearts", 0)} hearts
- Date: {conversation_data["context"].get("game_date", "Unknown")}

**Conversation Transcript:**
{conversation_data["transcript"]}

**Analysis Instructions:**
As {conversation_data["npc_name"]}, identify:

1. **Episodic Memories**: Specific events or moments worth remembering
2. **Player Preferences**: What you learned about what the player likes/dislikes  
3. **Relationship Milestones**: Any significant relationship developments
4. **Emotional Impact**: How this conversation affected your feelings about the player

Provide your analysis in this exact JSON format:
{{
  "episodic_memories": [
    {{
      "title": "Brief memorable title",
      "description": "Detailed description of what happened",
      "emotional_impact": 2.5,
      "importance": 7.0,
      "memory_type": "GIFT_RECEIVED/SHARED_ACTIVITY/EMOTIONAL_MOMENT/etc"
    }}
  ],
  "learned_preferences": [
    {{
      "category": "GIFTS/ACTIVITIES/PEOPLE/PLACES/TOPICS/FOODS",
      "item": "Specific thing learned about",
      "preference_level": 3.5,
      "confidence": 8.0,
      "evidence": "What the player said/did that revealed this"
    }}
  ],
  "relationship_milestones": [
    {{
      "milestone": "FIRST_GIFT/BECAME_FRIENDS/FIRST_SECRET_SHARED/etc",
      "description": "What milestone was reached"
    }}
  ],
  "overall_emotional_impact": {{
    "joy_change": 1.5,
    "trust_change": 0.5,
    "affection_change": 1.0,
    "annoyance_change": -0.5,
    "summary": "How this conversation changed your feelings about the player"
  }}
}}

**Important Guidelines:**
- Only include memories that are genuinely significant or meaningful
- Emotional impact: -10 to +10 (how much this affected the NPC emotionally)
- Importance: 1-10 (how memorable/significant this event is)
- Preference level: -10 to +10 (how much player likes/dislikes something)
- Confidence: 0-10 (how sure you are about the preference)
- Emotion changes: -3 to +3 (how much to adjust current personality metrics)
- If nothing significant happened, use empty arrays
"""

        try:
            response = self.client.models.generate_content(
                model=settings.memory_consolidation_model, contents=prompt
            )

            response_text = getattr(response, "text", "") or str(response)
            analysis = json.loads(response_text.strip())

            logger.debug(
                f"Memory analysis completed - Found {len(analysis.get('episodic_memories', []))} memories, {len(analysis.get('learned_preferences', []))} preferences"
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse memory analysis JSON: {e}")
            return self._get_empty_analysis()
        except Exception as e:
            logger.error(f"Error in memory analysis: {e}")
            return self._get_empty_analysis()

    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure if LLM analysis fails."""
        return {
            "episodic_memories": [],
            "learned_preferences": [],
            "relationship_milestones": [],
            "overall_emotional_impact": {
                "joy_change": 0.0,
                "trust_change": 0.0,
                "affection_change": 0.0,
                "annoyance_change": 0.0,
                "summary": "Normal conversation with no significant impact",
            },
        }

    async def _process_memory_analysis(
        self, conversation_data: Dict[str, Any], analysis: Dict[str, Any]
    ):
        """Process the LLM analysis into database updates."""

        # 1. Create episodic memories
        await self._create_episodic_memories(
            conversation_data, analysis.get("episodic_memories", [])
        )

        # 2. Update player preferences
        await self._update_player_preferences(
            conversation_data, analysis.get("learned_preferences", [])
        )

        # 3. Record relationship milestones
        await self._record_relationship_milestones(
            conversation_data, analysis.get("relationship_milestones", [])
        )

        # 4. Apply emotional impact to personality profile
        await self._apply_emotional_impact(
            conversation_data, analysis.get("overall_emotional_impact", {})
        )

    async def _create_episodic_memories(
        self, conversation_data: Dict[str, Any], memories: List[Dict[str, Any]]
    ):
        """Create episodic memory entries."""
        try:
            for memory in memories:
                # TODO: Once MemoryEpisode model is implemented, create actual database entries
                logger.info(
                    f"Would create memory episode: {memory['title']} (impact: {memory.get('emotional_impact', 0)})"
                )

                # Generate embedding for the memory
                memory_text = f"{memory['title']} - {memory['description']}"
                embedding = await vector_service.generate_embedding(memory_text)

                # This is where we would create the MemoryEpisode:
                # await db.memoryepisode.create(
                #     data={
                #         "playerId": conversation_data["player_id"],
                #         "npcId": conversation_data["npc_id"],
                #         "eventType": memory["memory_type"],
                #         "title": memory["title"],
                #         "description": memory["description"],
                #         "emotionalImpact": memory["emotional_impact"],
                #         "importance": memory["importance"],
                #         "location": conversation_data["context"].get("location"),
                #         "season": conversation_data["context"].get("season"),
                #         "gameDate": conversation_data["context"].get("game_date"),
                #         "embedding": embedding
                #     }
                # )

        except Exception as e:
            logger.error(f"Error creating episodic memories: {e}")

    async def _update_player_preferences(
        self, conversation_data: Dict[str, Any], preferences: List[Dict[str, Any]]
    ):
        """Update what the NPC has learned about player preferences."""
        try:
            for pref in preferences:
                logger.info(
                    f"Learned preference: {conversation_data['player_name']} has {pref['preference_level']}/10 preference for {pref['item']} in {pref['category']}"
                )

                # TODO: Once PlayerPreference model is implemented:
                # await db.playerpreference.upsert(
                #     where={
                #         "playerId_npcId_category_item": {
                #             "playerId": conversation_data["player_id"],
                #             "npcId": conversation_data["npc_id"],
                #             "category": pref["category"],
                #             "item": pref["item"]
                #         }
                #     },
                #     data={
                #         "preference": pref["preference_level"],
                #         "confidence": pref["confidence"],
                #         "evidenceSource": pref["evidence"],
                #         "lastObserved": datetime.now()
                #     },
                #     create={...}
                # )

        except Exception as e:
            logger.error(f"Error updating player preferences: {e}")

    async def _record_relationship_milestones(
        self, conversation_data: Dict[str, Any], milestones: List[Dict[str, Any]]
    ):
        """Record relationship milestone achievements."""
        try:
            for milestone in milestones:
                logger.info(
                    f"Relationship milestone reached: {milestone['milestone']} between {conversation_data['player_name']} and {conversation_data['npc_name']}"
                )

                # TODO: Once RelationshipMilestone model is implemented:
                # await db.relationshipmilestone.upsert(
                #     where={
                #         "playerId_npcId_milestone": {
                #             "playerId": conversation_data["player_id"],
                #             "npcId": conversation_data["npc_id"],
                #             "milestone": milestone["milestone"]
                #         }
                #     },
                #     data={
                #         "description": milestone["description"],
                #         "gameDate": conversation_data["context"].get("game_date"),
                #         "heartLevel": conversation_data["context"].get("friendship_hearts"),
                #         "achieved": True
                #     },
                #     create={...}
                # )

        except Exception as e:
            logger.error(f"Error recording relationship milestones: {e}")

    async def _apply_emotional_impact(
        self, conversation_data: Dict[str, Any], emotional_impact: Dict[str, Any]
    ):
        """Apply emotional changes to the personality profile."""
        try:
            if not emotional_impact or not any(
                abs(emotional_impact.get(key, 0)) > 0.1
                for key in [
                    "joy_change",
                    "trust_change",
                    "affection_change",
                    "annoyance_change",
                ]
            ):
                logger.debug("No significant emotional impact to apply")
                return

            logger.info(f"Applying emotional impact: {emotional_impact['summary']}")

            # Get current personality profile
            current_profile = await db.playerpersonalityprofile.find_unique(
                where={
                    "playerId_npcId": {
                        "playerId": conversation_data["player_id"],
                        "npcId": conversation_data["npc_id"],
                    }
                }
            )

            if current_profile:
                # Apply gradual emotional changes
                new_trust = max(
                    0,
                    min(
                        10,
                        current_profile.trust + emotional_impact.get("trust_change", 0),
                    ),
                )
                new_affection = max(
                    0,
                    min(
                        10,
                        current_profile.affection
                        + emotional_impact.get("affection_change", 0),
                    ),
                )
                new_annoyance = max(
                    0,
                    min(
                        10,
                        current_profile.annoyance
                        + emotional_impact.get("annoyance_change", 0),
                    ),
                )

                # Update personality profile
                await db.playerpersonalityprofile.update(
                    where={
                        "playerId_npcId": {
                            "playerId": conversation_data["player_id"],
                            "npcId": conversation_data["npc_id"],
                        }
                    },
                    data={
                        "trust": new_trust,
                        "affection": new_affection,
                        "annoyance": new_annoyance,
                        "summary": f"{current_profile.summary}. {emotional_impact.get('summary', '')}"[
                            :500
                        ],  # Limit length
                    },
                )

                logger.info(
                    f"Updated personality metrics - Trust: {current_profile.trust} -> {new_trust}, Affection: {current_profile.affection} -> {new_affection}"
                )

        except Exception as e:
            logger.error(f"Error applying emotional impact: {e}")

    async def decay_memories_daily(self):
        """
        Daily background task to decay old memories and strengthen important ones.
        Mimics how human memory works - frequently accessed memories get stronger,
        unimportant ones fade.
        """
        try:
            logger.info("Starting daily memory decay process")

            # TODO: Once MemoryEpisode model is implemented:
            # 1. Reduce importance of old, unaccessed memories
            # 2. Strengthen frequently recalled memories
            # 3. Delete memories below importance threshold
            # 4. Update access patterns

            logger.info("Memory decay process completed")

        except Exception as e:
            logger.error(f"Error in daily memory decay: {e}")


# Global instance
memory_consolidation_service = MemoryConsolidationService()
