import logging
import json
from typing import Dict, Any

from google import genai

from app.db import db
from app.config import settings
from app.services.memory.vector_service import vector_service

logger = logging.getLogger(__name__)


class PersonalityService:
    def __init__(self):
        if settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        else:
            self.client = None

    async def get_personality_profile(
        self, player_id: str, npc_id: str
    ) -> Dict[str, Any]:
        """Obtiene el perfil de personalidad que un NPC tiene de un jugador, usando Prisma."""
        try:
            profile = await db.playerpersonalityprofile.find_unique(
                where={"playerId_npcId": {"playerId": player_id, "npcId": npc_id}}
            )

            if profile:
                return {
                    "summary": profile.summary,
                    "friendliness": float(profile.friendliness),
                    "extroversion": float(profile.extroversion),
                    "sincerity": float(profile.sincerity),
                    "curiosity": float(profile.curiosity),
                    "trust": float(profile.trust),
                    "respect": float(profile.respect),
                    "affection": float(profile.affection),
                    "annoyance": float(profile.annoyance),
                    "admiration": float(profile.admiration),
                    "romantic_interest": float(profile.romantic_interest),
                    "humor_compatibility": float(profile.humor_compatibility),
                }

            # Perfil no encontrado, crear uno por defecto
            npc = await db.npc.find_unique(where={"id": npc_id})
            npc_name = npc.name if npc else "Unknown"

            default_values = self._get_default_personality_for_npc(npc_name)

            await db.playerpersonalityprofile.create(
                data={
                    "playerId": player_id,
                    "npcId": npc_id,
                    **default_values,
                }
            )
            logger.info(
                f"Created default personality profile for player {player_id} with NPC {npc_id}"
            )
            return default_values

        except Exception as e:
            logger.error(f"Error en get_personality_profile: {e}")
            # Fallback a un perfil genérico en caso de error grave
            return self._get_default_personality_for_npc("Unknown")

    async def update_personality_profile_async(self, conversation_id: str):
        """
        Actualiza el perfil de personalidad en segundo plano, incorporando memoria a largo plazo.
        """
        if not self.client:
            logger.warning(
                "Cliente de Gemini no disponible, no se puede actualizar la personalidad."
            )
            return

        try:
            # 1. Obtener datos de la conversación
            conv = await db.conversation.find_unique(
                where={"id": conversation_id},
                include={
                    "player": True,
                    "npc": True,
                    "dialogueEntries": {"order_by": {"timestamp": "asc"}},
                },
            )

            if not conv or not conv.dialogueEntries:
                logger.warning(
                    f"No se encontró la conversación {conversation_id} o no tiene diálogos."
                )
                return

            player_name, npc_name = conv.player.name, conv.npc.name

            # 2. Obtener perfil actual y recuerdos a largo plazo
            current_profile = await self.get_personality_profile(
                conv.playerId, conv.npcId
            )
            long_term_memories = await vector_service.search_relevant_memories(
                conv.playerId, conv.npcId, "summary of our relationship"
            )

            # 3. Construir el prompt mejorado
            transcript = "\n".join(
                f"{'Player' if entry.speaker == 'player' else npc_name}: {entry.message}"
                for entry in conv.dialogueEntries
            )

            memories_str = "\n".join(
                f"- {'You said' if m['speaker'] == npc_name else 'They said'}: '{m['message']}'"
                for m in long_term_memories
            )

            prompt = self._build_personality_update_prompt(
                player_name, npc_name, current_profile, transcript, memories_str
            )

            # 4. Llamar al LLM para el análisis
            response = self.client.models.generate_content(
                model=settings.personality_model, contents=prompt
            )
            response_text = getattr(response, "text", "") or str(response)

            # 5. Parsear y actualizar la base de datos
            new_profile_data = json.loads(response_text.strip())

            update_data = {
                "summary": new_profile_data["new_summary"],
                "friendliness": float(new_profile_data["new_friendliness"]),
                "extroversion": float(new_profile_data["new_extroversion"]),
                "sincerity": float(new_profile_data["new_sincerity"]),
                "curiosity": float(new_profile_data["new_curiosity"]),
                "trust": float(new_profile_data["new_trust"]),
                "respect": float(new_profile_data["new_respect"]),
                "affection": float(new_profile_data["new_affection"]),
                "annoyance": float(new_profile_data["new_annoyance"]),
                "admiration": float(new_profile_data["new_admiration"]),
                "romantic_interest": float(new_profile_data["new_romantic_interest"]),
                "humor_compatibility": float(
                    new_profile_data["new_humor_compatibility"]
                ),
            }

            await db.playerpersonalityprofile.update(
                where={
                    "playerId_npcId": {"playerId": conv.playerId, "npcId": conv.npcId}
                },
                data=update_data,
            )

            logger.info(
                f"Perfil de personalidad de {player_name} -> {npc_name} actualizado."
            )

        except json.JSONDecodeError:
            logger.error(
                f"Error al parsear JSON de la respuesta del LLM: {response_text}"
            )
        except Exception as e:
            logger.error(
                f"Error al actualizar el perfil de personalidad para la conversación {conversation_id}: {e}"
            )

    def _build_personality_update_prompt(
        self, player_name, npc_name, profile, transcript, memories
    ) -> str:
        return f"""You are an AI assistant specialized in psychological analysis of dialogue.
Your task is to update the personality profile that NPC {npc_name} has of player {player_name}.

**Analysis Instructions:**
- Analyze the **latest conversation** in the context of the **current relationship** and **past memories**.
- Make **significant, meaningful adjustments** to the metrics. Be bold.
- The player's choices (friendly, neutral, provocative) are a strong signal. React to them.
- Rude or provocative behavior should notably increase **annoyance** and decrease **trust, respect, and affection**.
- Kind and friendly behavior should do the opposite.
- Update the **summary** to reflect the new emotional state of the relationship.

**Current Profile of {player_name} (from {npc_name}'s perspective):**
- Summary: {profile["summary"]}
- Friendliness: {profile["friendliness"]}/10
- Extroversion: {profile["extroversion"]}/10
- Sincerity: {profile["sincerity"]}/10
- Curiosity: {profile["curiosity"]}/10
- Trust: {profile["trust"]}/10
- Respect: {profile["respect"]}/10
- Affection: {profile["affection"]}/10
- Annoyance: {profile["annoyance"]}/10
- Admiration: {profile["admiration"]}/10
- Romantic Interest: {profile["romantic_interest"]}/10
- Humor Compatibility: {profile["humor_compatibility"]}/10

**Key Long-Term Memories You Have of Them:**
{memories if memories else "No specific long-term memories stand out right now."}

**Transcript of the Most Recent Conversation:**
{transcript}

**Your Task:**
Based on all the above, provide a new personality profile in JSON format.
- Adjust ALL scores. Scores must be between 0 and 10.
- The summary must be a concise (max 60 words) reflection of your UPDATED feelings.

Format the response as a single, clean JSON object with these exact keys:
{{
  "new_summary": "Updated summary here",
  "new_friendliness": 7.5,
  "new_extroversion": 6.0,
  "new_sincerity": 5.0,
  "new_curiosity": 8.0,
  "new_trust": 6.5,
  "new_respect": 7.0,
  "new_affection": 4.5,
  "new_annoyance": 3.0,
  "new_admiration": 5.5,
  "new_romantic_interest": 2.0,
  "new_humor_compatibility": 7.5
}}"""

    async def generate_relationship_insight(
        self,
        personality_profile: Dict[str, Any],
        player_name: str,
        npc_name: str,
        npc_id: str = None,
    ) -> str:
        """
        Generate relationship insight including current emotional state.
        """
        # Get current emotional state if npc_id is provided
        emotional_context = ""
        if npc_id:
            try:
                # Import here to avoid circular imports
                from app.services.memory.emotional_state_service import (
                    emotional_state_service,
                )

                emotional_state = await emotional_state_service.get_emotional_state(
                    npc_id
                )
                current_mood = emotional_state.get("current_mood", "NEUTRAL")
                mood_intensity = emotional_state.get("mood_intensity", 5.0)

                mood_emojis = {
                    "VERY_HAPPY": "😄✨",
                    "HAPPY": "😊",
                    "CONTENT": "😌",
                    "NEUTRAL": "😐",
                    "WORRIED": "😟",
                    "SAD": "😢",
                    "ANGRY": "😠",
                    "EXCITED": "🤩",
                    "ROMANTIC": "🥰",
                    "NOSTALGIC": "🤔💭",
                    "STRESSED": "😰",
                }

                mood_emoji = mood_emojis.get(current_mood, "😐")
                emotional_context = f"\n🎭 ESTADO EMOCIONAL ACTUAL: {current_mood} {mood_emoji} (Intensidad: {mood_intensity:.1f}/10)\n"

                # Add recent emotional effects if available
                last_interaction = emotional_state.get("last_interaction_effect", "")
                if last_interaction:
                    emotional_context += f"💭 Última interacción: {last_interaction}\n"

            except Exception as e:
                logger.error(f"Error getting emotional state for insight: {e}")

        # Calculate relationship score and level
        friendliness = personality_profile.get("friendliness", 5.0)
        trust = personality_profile.get("trust", 5.0)
        respect = personality_profile.get("respect", 5.0)
        affection = personality_profile.get("affection", 3.0)
        annoyance = personality_profile.get("annoyance", 2.0)
        admiration = personality_profile.get("admiration", 3.0)
        humor_compatibility = personality_profile.get("humor_compatibility", 5.0)
        romantic_interest = personality_profile.get("romantic_interest", 1.0)
        sincerity = personality_profile.get("sincerity", 5.0)
        extroversion = personality_profile.get("extroversion", 5.0)
        curiosity = personality_profile.get("curiosity", 5.0)
        summary = personality_profile.get("summary", "...")

        weighted_score = (
            (friendliness * 1.2)
            + (trust * 1.3)
            + (respect * 1.0)
            + (affection * 1.5)
            + (admiration * 0.8)
            + (humor_compatibility * 0.7)
            - (annoyance * 2.0)
        ) / 7.5
        relationship_score = max(0, min(10, weighted_score))

        level_map = {
            8.5: "EXTRAORDINARIA ✨💕",
            7.5: "EXCELENTE 😊",
            6.5: "MUY BUENA 🙂",
            5.5: "BUENA 👍",
            4.5: "NEUTRAL 😐",
            3.5: "TENSA 😒",
            2.5: "MALA 😠",
            1.5: "MUY MALA 💢",
            0: "ODIO 🤬",
        }
        relationship_level = next(
            (
                v
                for k, v in sorted(level_map.items(), reverse=True)
                if relationship_score >= k
            ),
            "NEUTRAL 😐",
        )

        insight = f"""{emotional_context}
🎭 RELACIÓN {npc_name} → {player_name}: {relationship_level}
📝 Percepción: "{summary}"
📊 Perfil Completo de Personalidad (perspectiva de {npc_name}):
   • Amistad: {friendliness:.1f}/10
   • Confianza: {trust:.1f}/10
   • Respeto: {respect:.1f}/10
   • Afecto: {affection:.1f}/10
   • Interés Romántico: {romantic_interest:.1f}/10
   • Irritación: {annoyance:.1f}/10
   • Admiración: {admiration:.1f}/10
   • Sinceridad Percibida: {sincerity:.1f}/10
   • Compatibilidad de Humor: {humor_compatibility:.1f}/10
   • Curiosidad sobre ell@s: {curiosity:.1f}/10
   • Extroversión Percibida: {extroversion:.1f}/10"""
        return insight.strip()

    def _get_default_personality_for_npc(self, npc_name: str) -> Dict[str, Any]:
        """Obtiene valores de personalidad por defecto personalizados según el NPC."""
        npc_defaults = {
            # Existing NPCs
            "Haley": {
                "summary": "A new person... they look like they don't know much about fashion. Probably another boring farmer.",
                "friendliness": 3.0,
                "extroversion": 6.0,
                "sincerity": 4.0,
                "curiosity": 3.0,
                "trust": 3.5,
                "respect": 2.5,
                "affection": 1.5,
                "annoyance": 4.0,
                "admiration": 2.0,
                "romantic_interest": 1.0,
                "humor_compatibility": 3.0,
            },
            "Abigail": {
                "summary": "Someone new! I wonder if they're into adventure and fun stuff.",
                "friendliness": 6.0,
                "extroversion": 7.0,
                "sincerity": 6.5,
                "curiosity": 7.5,
                "trust": 5.5,
                "respect": 5.0,
                "affection": 4.0,
                "annoyance": 2.5,
                "admiration": 4.0,
                "romantic_interest": 2.0,
                "humor_compatibility": 6.5,
            },
            "Sebastian": {
                "summary": "Another person... probably wants to chat about boring small-town stuff. Hope they leave me alone.",
                "friendliness": 3.5,
                "extroversion": 2.5,
                "sincerity": 6.0,
                "curiosity": 4.0,
                "trust": 4.0,
                "respect": 4.5,
                "affection": 2.0,
                "annoyance": 3.5,
                "admiration": 3.0,
                "romantic_interest": 1.0,
                "humor_compatibility": 4.0,
            },
            "Penny": {
                "summary": "A new face in town. They seem nice... I hope they're not judgmental about my family situation.",
                "friendliness": 6.5,
                "extroversion": 4.0,
                "sincerity": 7.5,
                "curiosity": 5.5,
                "trust": 4.5,
                "respect": 5.5,
                "affection": 4.5,
                "annoyance": 1.5,
                "admiration": 4.5,
                "romantic_interest": 1.5,
                "humor_compatibility": 5.0,
            },
            "Alex": {
                "summary": "New person. Wonder if they're into sports or if they're one of those bookworm types.",
                "friendliness": 5.5,
                "extroversion": 7.5,
                "sincerity": 5.0,
                "curiosity": 4.0,
                "trust": 5.0,
                "respect": 4.0,
                "affection": 3.5,
                "annoyance": 3.0,
                "admiration": 3.5,
                "romantic_interest": 1.5,
                "humor_compatibility": 5.5,
            },
            "Elliott": {
                "summary": "A new soul graces our valley! Perhaps they possess an appreciation for the finer arts.",
                "friendliness": 7.0,
                "extroversion": 6.0,
                "sincerity": 6.5,
                "curiosity": 7.0,
                "trust": 5.5,
                "respect": 6.0,
                "affection": 4.5,
                "annoyance": 2.0,
                "admiration": 5.0,
                "romantic_interest": 2.0,
                "humor_compatibility": 6.0,
            },
            # New Bachelors
            "Harvey": {
                "summary": "Oh, a new patient... I mean, a new neighbor. I should probably introduce myself.",
                "friendliness": 6.0,
                "extroversion": 3.5,
                "sincerity": 7.0,
                "curiosity": 6.5,
                "trust": 6.0,
                "respect": 6.5,
                "affection": 4.0,
                "annoyance": 1.5,
                "admiration": 5.0,
                "romantic_interest": 1.5,
                "humor_compatibility": 4.5,
            },
            "Sam": {
                "summary": "Whoa, a new person! Hope they like music. Maybe they'll come to one of our band's shows.",
                "friendliness": 7.0,
                "extroversion": 8.0,
                "sincerity": 6.0,
                "curiosity": 6.5,
                "trust": 5.5,
                "respect": 5.0,
                "affection": 5.0,
                "annoyance": 2.0,
                "admiration": 4.5,
                "romantic_interest": 2.0,
                "humor_compatibility": 7.0,
            },
            "Shane": {
                "summary": "Ugh, another person. Just what I needed. Don't they have anything better to do than bother me?",
                "friendliness": 2.5,
                "extroversion": 3.0,
                "sincerity": 5.5,
                "curiosity": 3.0,
                "trust": 2.0,
                "respect": 2.5,
                "affection": 1.0,
                "annoyance": 6.0,
                "admiration": 2.0,
                "romantic_interest": 0.5,
                "humor_compatibility": 3.0,
            },
            # New Bachelorettes
            "Emily": {
                "summary": "Ooh, a new friend! Their aura seems interesting. I wonder what their favorite gemstone is.",
                "friendliness": 7.5,
                "extroversion": 7.0,
                "sincerity": 7.0,
                "curiosity": 7.5,
                "trust": 6.0,
                "respect": 6.5,
                "affection": 6.0,
                "annoyance": 1.0,
                "admiration": 6.0,
                "romantic_interest": 2.0,
                "humor_compatibility": 6.5,
            },
            "Leah": {
                "summary": "A new person in town. It's nice to see a new face, but I hope they respect an artist's need for solitude.",
                "friendliness": 5.5,
                "extroversion": 5.0,
                "sincerity": 6.5,
                "curiosity": 6.0,
                "trust": 5.0,
                "respect": 5.5,
                "affection": 4.0,
                "annoyance": 2.0,
                "admiration": 5.5,
                "romantic_interest": 1.5,
                "humor_compatibility": 5.0,
            },
            "Maru": {
                "summary": "A new variable in the town's social equation. I'm interested to observe their impact. And their knowledge of technology.",
                "friendliness": 5.0,
                "extroversion": 4.5,
                "sincerity": 7.0,
                "curiosity": 8.5,
                "trust": 5.5,
                "respect": 6.0,
                "affection": 3.5,
                "annoyance": 2.0,
                "admiration": 6.5,
                "romantic_interest": 1.5,
                "humor_compatibility": 4.0,
            },
            # Other Villagers from Characters.md
            "Caroline": {
                "summary": "Oh, the new farmer. They seem pleasant. I wonder if they appreciate a good sunroom.",
                "friendliness": 6.5,
                "extroversion": 6.0,
                "sincerity": 6.5,
                "curiosity": 6.0,
                "trust": 6.0,
                "respect": 6.0,
                "affection": 5.0,
                "annoyance": 2.0,
                "admiration": 5.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 6.0,
            },
            "Pierre": {
                "summary": "A potential new customer! I hope they appreciate the value of a local business over that Joja corporation.",
                "friendliness": 5.0,
                "extroversion": 5.5,
                "sincerity": 4.0,
                "curiosity": 5.0,
                "trust": 4.5,
                "respect": 4.5,
                "affection": 3.0,
                "annoyance": 3.5,
                "admiration": 3.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 4.0,
            },
            "Demetrius": {
                "summary": "A new variable has entered the local ecosystem. I must observe their habits objectively.",
                "friendliness": 5.0,
                "extroversion": 3.0,
                "sincerity": 6.5,
                "curiosity": 8.0,
                "trust": 5.0,
                "respect": 5.5,
                "affection": 3.0,
                "annoyance": 3.0,
                "admiration": 5.5,
                "romantic_interest": 0.0,
                "humor_compatibility": 3.5,
            },
            "Lewis": {
                "summary": "The newcomer who inherited their grandfather's farm. I hope they have what it takes to uphold the town's values.",
                "friendliness": 6.0,
                "extroversion": 6.5,
                "sincerity": 5.5,
                "curiosity": 5.0,
                "trust": 6.5,
                "respect": 7.0,
                "affection": 4.0,
                "annoyance": 2.0,
                "admiration": 5.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 5.0,
            },
            "Gus": {
                "summary": "A new face! I hope they enjoy a good meal and a friendly atmosphere. Everyone is welcome at the Saloon.",
                "friendliness": 8.0,
                "extroversion": 7.5,
                "sincerity": 8.0,
                "curiosity": 6.0,
                "trust": 7.5,
                "respect": 7.0,
                "affection": 7.0,
                "annoyance": 1.0,
                "admiration": 6.5,
                "romantic_interest": 0.0,
                "humor_compatibility": 7.0,
            },
            "Clint": {
                "summary": "Oh, a customer. I hope they don't want to chat too much. I'm... busy.",
                "friendliness": 4.0,
                "extroversion": 2.0,
                "sincerity": 5.0,
                "curiosity": 4.0,
                "trust": 4.5,
                "respect": 4.0,
                "affection": 2.5,
                "annoyance": 4.0,
                "admiration": 3.5,
                "romantic_interest": 0.0,
                "humor_compatibility": 3.0,
            },
            "Wizard": {
                "summary": "A presence in the valley I did not foresee. They tamper with forces beyond their comprehension. Interesting.",
                "friendliness": 3.5,
                "extroversion": 2.0,
                "sincerity": 6.0,
                "curiosity": 9.0,
                "trust": 4.0,
                "respect": 5.0,
                "affection": 2.0,
                "annoyance": 2.5,
                "admiration": 6.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 4.0,
            },
            # Other Villagers
            "Linus": {
                "summary": "A person from the town. Will they be like the others? Or will they see me as a person?",
                "friendliness": 4.0,
                "extroversion": 1.5,
                "sincerity": 8.0,
                "curiosity": 5.0,
                "trust": 3.0,
                "respect": 4.0,
                "affection": 2.5,
                "annoyance": 3.0,
                "admiration": 4.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 4.0,
            },
            "Willy": {
                "summary": "A new landlubber, eh? Wonder if they've got what it takes to handle a fishing rod.",
                "friendliness": 6.0,
                "extroversion": 5.5,
                "sincerity": 7.0,
                "curiosity": 5.0,
                "trust": 6.0,
                "respect": 6.5,
                "affection": 5.0,
                "annoyance": 1.5,
                "admiration": 6.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 5.5,
            },
            "Marnie": {
                "summary": "Oh, the new farmer! They seem sweet. I hope they like animals.",
                "friendliness": 7.0,
                "extroversion": 6.5,
                "sincerity": 7.5,
                "curiosity": 5.5,
                "trust": 6.5,
                "respect": 6.0,
                "affection": 6.5,
                "annoyance": 1.0,
                "admiration": 5.0,
                "romantic_interest": 0.0,
                "humor_compatibility": 6.0,
            },
            "Robin": {
                "summary": "The new farmer! It'll be great to have someone new in town. I wonder what they'll build on that old farm.",
                "friendliness": 7.5,
                "extroversion": 7.5,
                "sincerity": 7.0,
                "curiosity": 6.5,
                "trust": 7.0,
                "respect": 7.0,
                "affection": 6.0,
                "annoyance": 1.0,
                "admiration": 6.5,
                "romantic_interest": 0.0,
                "humor_compatibility": 6.5,
            },
        }

        # Default for any other NPC
        default = {
            "summary": "A newcomer to town. I'm curious to see what kind of person they really are.",
            "friendliness": 4.5,
            "extroversion": 4.5,
            "sincerity": 5.0,
            "curiosity": 5.5,
            "trust": 4.0,
            "respect": 4.5,
            "affection": 3.0,
            "annoyance": 2.5,
            "admiration": 3.5,
            "romantic_interest": 0.0,
            "humor_compatibility": 4.5,
        }

        return npc_defaults.get(npc_name, default)


# Instancia global del servicio
personality_service = PersonalityService()
