import logging
from typing import Dict, Any
from datetime import datetime
from enum import Enum

from app.db import db

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
        pass

    async def get_emotional_state(
        self, npc_id: str, player_id: str = None
    ) -> Dict[str, Any]:
        """Get the current emotional state for an NPC towards a specific player."""
        try:
            if not player_id:
                # Return a default state if no player specified
                return self._get_default_emotional_state(npc_id)

            # Get the emotional state for this specific NPC-Player relationship
            state = await self._get_or_create_emotional_state(npc_id, player_id)

            return {
                "npc_id": npc_id,
                "player_id": player_id,
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
                "relationship_context": "⚠️ DATOS DE PERCEPCIÓN: Estado emocional del NPC hacia este jugador específico",
            }
        except Exception as e:
            logger.error(
                f"Error getting emotional state for NPC {npc_id} towards player {player_id}: {e}"
            )
            return self._get_default_emotional_state(npc_id, player_id)

    async def _get_or_create_emotional_state(
        self, npc_id: str, player_id: str
    ) -> Dict[str, Any]:
        """Get or create emotional state for an NPC towards a specific player."""
        try:
            # Try to get existing emotional state from database using the new schema
            emotional_state = await db.emotionalstate.find_unique(
                where={"npcId_playerId": {"npcId": npc_id, "playerId": player_id}}
            )

            if emotional_state:
                return {
                    "npc_id": npc_id,
                    "player_id": player_id,
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
                default_state = self._get_default_emotional_state(npc_id, player_id)
                created_state = await db.emotionalstate.create(
                    data={
                        "npcId": npc_id,
                        "playerId": player_id,
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
                logger.info(
                    f"Created new emotional state for NPC {npc_id} towards player {player_id}"
                )
                return default_state

        except Exception as e:
            logger.error(
                f"Error getting/creating emotional state for NPC {npc_id} towards player {player_id}: {e}"
            )
            return self._get_default_emotional_state(npc_id, player_id)

    def _get_default_emotional_state(
        self, npc_id: str, player_id: str = None
    ) -> Dict[str, Any]:
        """Get default emotional state for an NPC towards a player."""
        return {
            "npc_id": npc_id,
            "player_id": player_id,
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
            "relationship_context": "📊 DATOS BASE: Estado emocional neutro por defecto"
            if player_id
            else "📊 DATOS BASE: Estado emocional global",
        }

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
