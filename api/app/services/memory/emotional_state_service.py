import logging
from typing import Dict, Any
from datetime import datetime
from enum import Enum

from app.db import db
from app.config import settings
from google import genai

logger = logging.getLogger(__name__)


class Mood(str, Enum):
    """Enum for different mood states NPCs can be in."""

    VERY_HAPPY = "VERY_HAPPY"
    HAPPY = "HAPPY"
    CONTENT = "CONTENT"
    NEUTRAL = "NEUTRAL"
    WORRIED = "WORRIED"
    SAD = "SAD"
    ANGRY = "ANGRY"
    EXCITED = "EXCITED"
    ROMANTIC = "ROMANTIC"
    NOSTALGIC = "NOSTALGIC"
    STRESSED = "STRESSED"


class EmotionalStateService:
    """
    Service for managing NPCs' dynamic emotional states.
    Makes NPCs feel more human by tracking their current mood and emotional responses.
    """

    def __init__(self):
        if settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        else:
            self.client = None

    async def get_emotional_state(self, npc_id: str) -> Dict[str, Any]:
        """Get the current emotional state for an NPC."""
        try:
            # For now, return a default emotional state since we don't have the EmotionalState model yet
            # TODO: Once EmotionalState model is implemented in schema, use actual database

            # Check if we have an emotional state stored (mock for now)
            state = await self._get_or_create_emotional_state(npc_id)

            return {
                "npc_id": npc_id,
                "current_mood": state.get("current_mood", "NEUTRAL"),
                "mood_intensity": state.get("mood_intensity", 5.0),
                "recent_joy": state.get("recent_joy", 0.0),
                "recent_sadness": state.get("recent_sadness", 0.0),
                "recent_anger": state.get("recent_anger", 0.0),
                "recent_anxiety": state.get("recent_anxiety", 0.0),
                "recent_excitement": state.get("recent_excitement", 0.0),
                "last_interaction_effect": state.get("last_interaction_effect", ""),
                "external_factors": state.get("external_factors", ""),
                "last_updated": state.get("last_updated", datetime.now()),
            }
        except Exception as e:
            logger.error(f"Error getting emotional state for NPC {npc_id}: {e}")
            return self._get_default_emotional_state(npc_id)

    async def update_emotional_state_from_interaction(
        self,
        npc_id: str,
        conversation_transcript: str,
        player_response_tone: str = "neutral",
    ):
        """
        Update NPC's emotional state based on a recent interaction.

        Args:
            npc_id: The NPC whose emotional state to update
            conversation_transcript: Recent conversation to analyze
            player_response_tone: "friendly", "neutral", or "provocative"
        """
        try:
            if not self.client:
                logger.warning("Gemini client not available for emotional analysis")
                return

            # Get current emotional state
            current_state = await self.get_emotional_state(npc_id)

            # Get NPC info for context
            npc = await db.npc.find_unique(where={"id": npc_id})
            npc_name = npc.name if npc else "Unknown"

            # Analyze the interaction's emotional impact
            emotional_analysis = await self._analyze_interaction_emotion(
                npc_name, conversation_transcript, player_response_tone, current_state
            )

            # Update the emotional state
            await self._update_emotional_state(npc_id, emotional_analysis)

            logger.info(
                f"Updated emotional state for {npc_name} - New mood: {emotional_analysis.get('new_mood', 'NEUTRAL')}"
            )

        except Exception as e:
            logger.error(f"Error updating emotional state for NPC {npc_id}: {e}")

    async def _analyze_interaction_emotion(
        self,
        npc_name: str,
        conversation_transcript: str,
        player_response_tone: str,
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use LLM to analyze the emotional impact of an interaction."""

        valid_moods = ", ".join([mood.value for mood in Mood])

        prompt = f"""You are an AI specialized in emotional psychology. Analyze how this conversation would affect {npc_name}'s emotional state.

**{npc_name}'s Current Emotional State:**
- Current Mood: {current_state["current_mood"]}
- Mood Intensity: {current_state["mood_intensity"]}/10
- Recent Joy: {current_state["recent_joy"]}/5
- Recent Sadness: {current_state["recent_sadness"]}/5
- Recent Anger: {current_state["recent_anger"]}/5
- Recent Anxiety: {current_state["recent_anxiety"]}/5
- Recent Excitement: {current_state["recent_excitement"]}/5

**Recent Conversation:**
{conversation_transcript}

**Player's Response Tone:** {player_response_tone}

**Instructions:**
Analyze how this interaction would realistically affect {npc_name}'s emotional state. Consider:
1. The specific words and tone used
2. {npc_name}'s personality from Stardew Valley
3. How humans emotionally respond to different types of interactions
4. The cumulative effect on their current emotional state

Provide your analysis in this exact JSON format. The "new_mood" MUST be one of these exact values: {valid_moods}
{{
  "new_mood": "A_VALID_MOOD_FROM_THE_LIST",
  "new_mood_intensity": 6.5,
  "joy_change": 1.5,
  "sadness_change": -0.5,
  "anger_change": 0.0,
  "anxiety_change": 0.0,
  "excitement_change": 2.0,
  "interaction_summary": "Brief description of the emotional impact",
  "mood_reason": "Why the mood changed to this state"
}}

All emotion changes should be between -3.0 and +3.0 (how much to adjust the current level).
"""

        try:
            response = self.client.models.generate_content(
                model=settings.emotional_model, contents=prompt
            )

            response_text = getattr(response, "text", "") or str(response)

            # Debug: Log the actual response
            logger.debug(
                f"Raw LLM response for emotional analysis: {response_text[:200]}..."
            )

            # Clean response text - sometimes LLM adds extra text around JSON
            response_text = response_text.strip()

            # Try to find JSON in the response
            import json

            # Look for JSON block if wrapped in markdown
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end]
            elif "{" in response_text and "}" in response_text:
                # Extract just the JSON part
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                response_text = response_text[start:end]

            analysis = json.loads(response_text.strip())

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse emotional analysis JSON: {e}")
            logger.error(f"Raw response that failed to parse: {response_text}")
            return self._get_default_emotional_change(player_response_tone)
        except Exception as e:
            logger.error(f"Error in emotional analysis: {e}")
            return self._get_default_emotional_change(player_response_tone)

    def _get_default_emotional_change(
        self, player_response_tone: str
    ) -> Dict[str, Any]:
        """Fallback emotional changes based on player tone."""
        if player_response_tone == "friendly":
            return {
                "new_mood": "HAPPY",
                "new_mood_intensity": 6.0,
                "joy_change": 1.0,
                "sadness_change": -0.5,
                "anger_change": -0.5,
                "anxiety_change": -0.3,
                "excitement_change": 0.5,
                "interaction_summary": "Player was friendly and kind",
                "mood_reason": "Positive interaction made me feel happier",
            }
        elif player_response_tone == "provocative":
            return {
                "new_mood": "ANGRY",
                "new_mood_intensity": 6.5,
                "joy_change": -1.0,
                "sadness_change": 0.0,
                "anger_change": 1.5,
                "anxiety_change": 0.5,
                "excitement_change": -0.5,
                "interaction_summary": "Player was provocative or rude",
                "mood_reason": "Their attitude was irritating",
            }
        else:  # neutral
            return {
                "new_mood": "NEUTRAL",
                "new_mood_intensity": 5.0,
                "joy_change": 0.0,
                "sadness_change": 0.0,
                "anger_change": 0.0,
                "anxiety_change": 0.0,
                "excitement_change": 0.0,
                "interaction_summary": "Normal, polite conversation",
                "mood_reason": "Standard interaction, nothing special",
            }

    async def _get_or_create_emotional_state(self, npc_id: str) -> Dict[str, Any]:
        """Get or create emotional state for an NPC from database."""
        try:
            # Try to get existing emotional state from database
            emotional_state = await db.emotionalstate.find_unique(
                where={"npcId": npc_id}
            )

            if emotional_state:
                return {
                    "npc_id": npc_id,
                    "current_mood": emotional_state.currentMood,
                    "mood_intensity": float(emotional_state.moodIntensity),
                    "recent_joy": float(emotional_state.recentJoy),
                    "recent_sadness": float(emotional_state.recentSadness),
                    "recent_anger": float(emotional_state.recentAnger),
                    "recent_anxiety": float(emotional_state.recentAnxiety),
                    "recent_excitement": float(emotional_state.recentExcitement),
                    "last_interaction_effect": emotional_state.lastInteractionEffect
                    or "",
                    "external_factors": emotional_state.externalFactors or "",
                    "last_updated": emotional_state.lastUpdated,
                }
            else:
                # Create new emotional state with defaults
                default_state = self._get_default_emotional_state(npc_id)
                created_state = await db.emotionalstate.create(
                    data={
                        "npcId": npc_id,
                        "currentMood": default_state["current_mood"],
                        "moodIntensity": default_state["mood_intensity"],
                        "recentJoy": default_state["recent_joy"],
                        "recentSadness": default_state["recent_sadness"],
                        "recentAnger": default_state["recent_anger"],
                        "recentAnxiety": default_state["recent_anxiety"],
                        "recentExcitement": default_state["recent_excitement"],
                        "lastInteractionEffect": default_state[
                            "last_interaction_effect"
                        ],
                        "externalFactors": default_state["external_factors"],
                    }
                )
                logger.info(f"Created new emotional state for NPC {npc_id}")
                return default_state

        except Exception as e:
            logger.error(
                f"Error getting/creating emotional state for NPC {npc_id}: {e}"
            )
            return self._get_default_emotional_state(npc_id)

    def _get_default_emotional_state(self, npc_id: str) -> Dict[str, Any]:
        """Get default emotional state for an NPC."""
        return {
            "npc_id": npc_id,
            "current_mood": "NEUTRAL",
            "mood_intensity": 5.0,
            "recent_joy": 0.0,
            "recent_sadness": 0.0,
            "recent_anger": 0.0,
            "recent_anxiety": 0.0,
            "recent_excitement": 0.0,
            "last_interaction_effect": "",
            "external_factors": "",
            "last_updated": datetime.now(),
        }

    async def _update_emotional_state(
        self, npc_id: str, emotional_analysis: Dict[str, Any]
    ):
        """Update the emotional state in the database."""
        try:
            # Get current state
            current_state = await self.get_emotional_state(npc_id)

            # Calculate new values
            new_joy = max(
                -5.0,
                min(
                    5.0,
                    current_state["recent_joy"]
                    + emotional_analysis.get("joy_change", 0),
                ),
            )
            new_sadness = max(
                -5.0,
                min(
                    5.0,
                    current_state["recent_sadness"]
                    + emotional_analysis.get("sadness_change", 0),
                ),
            )
            new_anger = max(
                -5.0,
                min(
                    5.0,
                    current_state["recent_anger"]
                    + emotional_analysis.get("anger_change", 0),
                ),
            )
            new_anxiety = max(
                -5.0,
                min(
                    5.0,
                    current_state["recent_anxiety"]
                    + emotional_analysis.get("anxiety_change", 0),
                ),
            )
            new_excitement = max(
                -5.0,
                min(
                    5.0,
                    current_state["recent_excitement"]
                    + emotional_analysis.get("excitement_change", 0),
                ),
            )

            # Update the emotional state in database
            await db.emotionalstate.upsert(
                where={"npcId": npc_id},
                data={
                    "update": {
                        "currentMood": emotional_analysis.get("new_mood", "NEUTRAL"),
                        "moodIntensity": float(
                            emotional_analysis.get("new_mood_intensity", 5.0)
                        ),
                        "recentJoy": new_joy,
                        "recentSadness": new_sadness,
                        "recentAnger": new_anger,
                        "recentAnxiety": new_anxiety,
                        "recentExcitement": new_excitement,
                        "lastInteractionEffect": emotional_analysis.get(
                            "interaction_summary", ""
                        ),
                        "lastUpdated": datetime.now(),
                    },
                    "create": {
                        "npcId": npc_id,
                        "currentMood": emotional_analysis.get("new_mood", "NEUTRAL"),
                        "moodIntensity": float(
                            emotional_analysis.get("new_mood_intensity", 5.0)
                        ),
                        "recentJoy": new_joy,
                        "recentSadness": new_sadness,
                        "recentAnger": new_anger,
                        "recentAnxiety": new_anxiety,
                        "recentExcitement": new_excitement,
                        "lastInteractionEffect": emotional_analysis.get(
                            "interaction_summary", ""
                        ),
                        "externalFactors": "",
                    },
                },
            )

            logger.info(
                f"Successfully updated emotional state for NPC {npc_id}: {emotional_analysis.get('new_mood', 'NEUTRAL')} (intensity: {emotional_analysis.get('new_mood_intensity', 5.0)})"
            )

        except Exception as e:
            logger.error(
                f"Error updating emotional state in database for NPC {npc_id}: {e}"
            )
            # Log the change even if database update fails
            logger.info(
                f"Would update emotional state for NPC {npc_id}: {emotional_analysis}"
            )

    def generate_mood_context_for_dialogue(
        self, emotional_state: Dict[str, Any]
    ) -> str:
        """Generate context string about NPC's current emotional state for dialogue generation."""

        mood = emotional_state["current_mood"]
        intensity = emotional_state["mood_intensity"]

        mood_descriptions = {
            "VERY_HAPPY": f"You are in an excellent mood (intensity {intensity}/10). You feel joyful, optimistic, and want to share your happiness.",
            "HAPPY": f"You are feeling good (intensity {intensity}/10). You're in a pleasant, positive mood.",
            "CONTENT": f"You are feeling peaceful and satisfied (intensity {intensity}/10). Life feels stable and good.",
            "NEUTRAL": f"You are in a normal, balanced mood (intensity {intensity}/10). Nothing particular is affecting your emotions.",
            "WORRIED": f"You are feeling anxious or concerned about something (intensity {intensity}/10). Your mind is preoccupied.",
            "SAD": f"You are feeling down or melancholy (intensity {intensity}/10). Things feel a bit heavy emotionally.",
            "ANGRY": f"You are feeling irritated or frustrated (intensity {intensity}/10). Your patience is shorter than usual.",
            "EXCITED": f"You are feeling energetic and enthusiastic (intensity {intensity}/10). You're eager and animated.",
            "ROMANTIC": f"You are feeling affectionate and romantic (intensity {intensity}/10). Your heart feels warm.",
            "NOSTALGIC": f"You are feeling wistful and reflective (intensity {intensity}/10). Old memories are on your mind.",
            "STRESSED": f"You are feeling overwhelmed or under pressure (intensity {intensity}/10). Everything feels like a lot right now.",
        }

        base_description = mood_descriptions.get(mood, "You are in a normal mood.")

        # Add recent emotional modifiers
        modifiers = []
        if emotional_state["recent_joy"] > 1.0:
            modifiers.append("with recent moments of happiness")
        if emotional_state["recent_sadness"] > 1.0:
            modifiers.append("but also dealing with some sadness")
        if emotional_state["recent_anger"] > 1.0:
            modifiers.append("with some underlying frustration")
        if emotional_state["recent_excitement"] > 1.0:
            modifiers.append("with bursts of excitement")

        if modifiers:
            base_description += " " + ", ".join(modifiers) + "."

        if emotional_state.get("last_interaction_effect"):
            base_description += (
                f" Recent interaction: {emotional_state['last_interaction_effect']}"
            )

        return base_description


# Global instance
emotional_state_service = EmotionalStateService()
