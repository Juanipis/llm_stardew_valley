from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime, timedelta
from google import genai
from ..db import db
from ..config import settings

# Configurar logging
logger = logging.getLogger(__name__)


class MemoryService:
    """Servicio para manejar la memoria y personalidad de los NPCs"""

    def __init__(self):
        if settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        else:
            self.client = None

    async def get_or_create_player(self, player_name: str) -> str:
        """Obtiene o crea un jugador y retorna su ID"""
        # Nota: Los modelos nuevos estarán disponibles después de la migración
        # Por ahora usamos una implementación simplificada
        try:
            # Buscar jugador existente usando query raw
            result = await db.query_raw(
                'SELECT id FROM "Player" WHERE name = $1', player_name
            )
            if result:
                return result[0]["id"]

            # Crear nuevo jugador
            import uuid

            player_id = str(uuid.uuid4())
            await db.execute_raw(
                'INSERT INTO "Player" (id, name, "createdAt", "updatedAt") VALUES ($1, $2, NOW(), NOW())',
                player_id,
                player_name,
            )
            return player_id
        except Exception as e:
            logger.error(f"Error managing player: {e}")
            return ""

    async def get_or_create_npc(
        self, npc_name: str, npc_location: Optional[str] = None
    ) -> str:
        """Obtiene o crea un NPC y retorna su ID"""
        try:
            # Buscar NPC existente
            result = await db.query_raw(
                'SELECT id FROM "Npc" WHERE name = $1', npc_name
            )
            if result:
                return result[0]["id"]

            # Crear nuevo NPC
            import uuid

            npc_id = str(uuid.uuid4())
            await db.execute_raw(
                'INSERT INTO "Npc" (id, name, location, "createdAt", "updatedAt") VALUES ($1, $2, $3, NOW(), NOW())',
                npc_id,
                npc_name,
                npc_location,
            )
            return npc_id
        except Exception as e:
            logger.error(f"Error managing NPC: {e}")
            return ""

    async def get_personality_profile(
        self, player_id: str, npc_id: str
    ) -> Dict[str, Any]:
        """Obtiene el perfil de personalidad que un NPC tiene de un jugador"""
        try:
            result = await db.query_raw(
                '''SELECT summary, friendliness, extroversion, sincerity, curiosity, 
                          trust, respect, affection, annoyance, admiration, romantic_interest, humor_compatibility 
                   FROM "PlayerPersonalityProfile" WHERE "playerId" = $1 AND "npcId" = $2''',
                player_id,
                npc_id,
            )

            if result:
                profile_data = result[0]
                return {
                    "summary": profile_data["summary"],
                    # Métricas básicas de personalidad
                    "friendliness": float(profile_data["friendliness"]),
                    "extroversion": float(profile_data["extroversion"]),
                    "sincerity": float(profile_data["sincerity"]),
                    "curiosity": float(profile_data["curiosity"]),
                    # Métricas emocionales avanzadas
                    "trust": float(profile_data["trust"]),
                    "respect": float(profile_data["respect"]),
                    "affection": float(profile_data["affection"]),
                    "annoyance": float(profile_data["annoyance"]),
                    "admiration": float(profile_data["admiration"]),
                    "romantic_interest": float(profile_data["romantic_interest"]),
                    "humor_compatibility": float(profile_data["humor_compatibility"]),
                }
            else:
                # Obtener el nombre del NPC para personalizar el perfil
                npc_result = await db.query_raw(
                    'SELECT name FROM "Npc" WHERE id = $1',
                    npc_id,
                )
                npc_name = npc_result[0]["name"] if npc_result else "Unknown"
                
                # Crear perfil por defecto personalizado según el NPC
                import uuid

                profile_id = str(uuid.uuid4())
                
                # Personalizar valores iniciales según el NPC
                default_values = self._get_default_personality_for_npc(npc_name)
                
                await db.execute_raw(
                    """INSERT INTO "PlayerPersonalityProfile" 
                       (id, "playerId", "npcId", summary, friendliness, extroversion, sincerity, curiosity,
                        trust, respect, affection, annoyance, admiration, romantic_interest, humor_compatibility,
                        "createdAt", "updatedAt") 
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW(), NOW())""",
                    profile_id,
                    player_id,
                    npc_id,
                    default_values["summary"],
                    default_values["friendliness"],
                    default_values["extroversion"],
                    default_values["sincerity"],
                    default_values["curiosity"],
                    default_values["trust"],
                    default_values["respect"],
                    default_values["affection"],
                    default_values["annoyance"],
                    default_values["admiration"],
                    default_values["romantic_interest"],
                    default_values["humor_compatibility"],
                )

                return default_values
        except Exception as e:
            logger.error(f"Error managing personality profile: {e}")
            return {
                "summary": "A new person I'm just getting to know. They seem friendly enough.",
                "friendliness": 5.0,
                "extroversion": 5.0,
                "sincerity": 5.0,
                "curiosity": 5.0,
            }

    async def generate_embedding(self, text: str) -> List[float]:
        """Genera un embedding para un texto usando Google's embedding model"""
        try:
            if not self.client:
                logger.warning("No Gemini client available for embedding generation")
                return []

            # TODO: Temporalmente deshabilitado hasta resolver la estructura de response
            logger.info("Embedding generation temporarily disabled")
            return []

            # response = self.client.models.embed_content(
            #     model=settings.embedding_model, contents=text
            # )

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def search_relevant_memories(
        self, player_id: str, npc_id: str, query_text: str
    ) -> List[Dict[str, Any]]:
        """Busca recuerdos relevantes usando búsqueda por vector"""
        try:
            # Por ahora, sin embeddings, buscar las últimas conversaciones
            logger.debug(
                "Searching memories for player %s and NPC %s", player_id, npc_id
            )

            # Buscar las últimas entradas de diálogo entre estos personajes
            query = f"""
            SELECT de.message, de.speaker, de.timestamp, c.id as conversation_id
            FROM "DialogueEntry" de
            JOIN "Conversation" c ON de."conversationId" = c.id
            WHERE c."playerId" = $1 AND c."npcId" = $2 
            ORDER BY de.timestamp DESC
            LIMIT {settings.max_relevant_memories}
            """

            results = await db.query_raw(query, player_id, npc_id)
            logger.debug("Found %d memory entries", len(results))

            memories = []
            for result in results:
                memories.append(
                    {
                        "message": result["message"],
                        "speaker": result["speaker"],
                        "timestamp": result["timestamp"],
                        "conversation_id": result["conversation_id"],
                    }
                )

            return memories
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    async def get_or_create_active_conversation(
        self, player_id: str, npc_id: str, context: Dict[str, Any]
    ) -> str:
        """Obtiene una conversación activa o crea una nueva"""
        try:
            # Buscar conversación activa (sin endTime y reciente)
            cutoff_time = datetime.now() - timedelta(
                minutes=settings.conversation_timeout_minutes
            )

            result = await db.query_raw(
                """SELECT id FROM "Conversation" 
                   WHERE "playerId" = $1 AND "npcId" = $2 
                   AND "endTime" IS NULL 
                   AND "startTime" >= $3::timestamp
                   ORDER BY "startTime" DESC LIMIT 1""",
                player_id,
                npc_id,
                cutoff_time.isoformat(),
            )

            if result:
                return result[0]["id"]

            # Crear nueva conversación
            import uuid

            conversation_id = str(uuid.uuid4())

            await db.execute_raw(
                """INSERT INTO "Conversation" 
                   (id, "startTime", "playerId", "npcId", season, "dayOfMonth", "dayOfWeek", 
                    "timeOfDay", year, weather, "playerLocation", "friendshipHearts") 
                   VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                conversation_id,
                player_id,
                npc_id,
                context.get("season"),
                context.get("day_of_month"),
                context.get("day_of_week"),
                context.get("time_of_day"),
                context.get("year"),
                context.get("weather"),
                context.get("player_location"),
                context.get("friendship_hearts"),
            )

            return conversation_id
        except Exception as e:
            logger.error(f"Error managing conversation: {e}")
            return ""

    async def add_dialogue_entry(
        self,
        conversation_id: str,
        speaker: str,
        message: str,
        generate_embedding: bool = True,
    ):
        """Añade una entrada de diálogo a la conversación"""
        try:
            import uuid

            entry_id = str(uuid.uuid4())

            # Generar embedding si se solicita
            if generate_embedding:
                embedding = await self.generate_embedding(message)
                if embedding:
                    # Convertir embedding a formato PostgreSQL
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                    # Usar query raw para insertar con embedding
                    await db.execute_raw(
                        """INSERT INTO "DialogueEntry" (id, "conversationId", speaker, message, timestamp, embedding)
                           VALUES ($1, $2, $3, $4, NOW(), $5::vector)""",
                        entry_id,
                        conversation_id,
                        speaker,
                        message,
                        embedding_str,
                    )
                else:
                    # Insertar sin embedding
                    await db.execute_raw(
                        """INSERT INTO "DialogueEntry" (id, "conversationId", speaker, message, timestamp)
                           VALUES ($1, $2, $3, $4, NOW())""",
                        entry_id,
                        conversation_id,
                        speaker,
                        message,
                    )
            else:
                await db.execute_raw(
                    """INSERT INTO "DialogueEntry" (id, "conversationId", speaker, message, timestamp)
                       VALUES ($1, $2, $3, $4, NOW())""",
                    entry_id,
                    conversation_id,
                    speaker,
                    message,
                )
        except Exception as e:
            logger.error(f"Error adding dialogue entry: {e}")

    async def end_conversation(self, conversation_id: str):
        """Marca una conversación como terminada"""
        try:
            await db.execute_raw(
                'UPDATE "Conversation" SET "endTime" = NOW() WHERE id = $1',
                conversation_id,
            )
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")

    async def update_personality_profile_async(self, conversation_id: str):
        """Actualiza el perfil de personalidad en segundo plano"""
        try:
            # Obtener la conversación completa
            conversation_result = await db.query_raw(
                """SELECT c.id, c."playerId", c."npcId", p.name as player_name, n.name as npc_name
                   FROM "Conversation" c
                   JOIN "Player" p ON c."playerId" = p.id
                   JOIN "Npc" n ON c."npcId" = n.id
                   WHERE c.id = $1""",
                conversation_id,
            )

            if not conversation_result:
                return

            conversation = conversation_result[0]

            # Obtener entradas de diálogo
            dialogue_results = await db.query_raw(
                'SELECT speaker, message FROM "DialogueEntry" WHERE "conversationId" = $1 ORDER BY timestamp',
                conversation_id,
            )

            if not dialogue_results:
                return

            # Obtener perfil actual
            current_profile = await self.get_personality_profile(
                conversation["playerId"], conversation["npcId"]
            )

            # Generar transcripción
            transcript = ""
            for entry in dialogue_results:
                speaker = (
                    "Player"
                    if entry["speaker"] == "player"
                    else conversation["npc_name"]
                )
                transcript += f"{speaker}: {entry['message']}\n"

            # Prompt para actualizar personalidad
            prompt = f"""You are an AI assistant specialized in psychological analysis based on dialogue.
Your task is to update the comprehensive personality profile that an NPC, {conversation["npc_name"]}, has of a player, {conversation["player_name"]}, based on their most recent conversation.

**Current Personality Profile:**
- Summary: {current_profile["summary"]}

**Basic Personality Metrics (0-10):**
- Friendliness: {current_profile["friendliness"]}/10
- Extroversion: {current_profile["extroversion"]}/10
- Sincerity: {current_profile["sincerity"]}/10
- Curiosity: {current_profile["curiosity"]}/10

**Emotional Relationship Metrics (0-10):**
- Trust: {current_profile["trust"]}/10 (How much {conversation["npc_name"]} trusts {conversation["player_name"]})
- Respect: {current_profile["respect"]}/10 (How much {conversation["npc_name"]} respects {conversation["player_name"]})
- Affection: {current_profile["affection"]}/10 (How much {conversation["npc_name"]} cares about {conversation["player_name"]})
- Annoyance: {current_profile["annoyance"]}/10 (How much {conversation["player_name"]} irritates {conversation["npc_name"]})
- Admiration: {current_profile["admiration"]}/10 (How much {conversation["npc_name"]} admires {conversation["player_name"]})
- Romantic Interest: {current_profile["romantic_interest"]}/10 (Any romantic feelings {conversation["npc_name"]} has)
- Humor Compatibility: {current_profile["humor_compatibility"]}/10 (How funny/compatible their humor is)

**Transcript of the New Conversation:**
{transcript}

**Instructions:**
Analyze the new conversation and make SIGNIFICANT adjustments to ALL metrics based on the player's behavior and the NPC's likely emotional reaction. Don't be conservative - if the player was rude, drop friendliness substantially. If they were kind, raise affection meaningfully.

**Basic Personality Adjustments (be more aggressive):**
- Friendliness: +/- 1.0-3.0 points based on player's warmth/rudeness
- Extroversion: +/- 0.5-2.0 points based on player's social energy
- Sincerity: +/- 1.0-2.5 points based on player's authenticity/sarcasm
- Curiosity: +/- 0.5-2.0 points based on player's interest in topics

**Emotional Relationship Adjustments (be very responsive):**
- Trust: +/- 1.0-3.0 points based on reliability/dishonesty
- Respect: +/- 1.0-3.5 points based on player's behavior/competence
- Affection: +/- 0.5-2.5 points based on caring/coldness
- Annoyance: +/- 1.0-4.0 points based on irritating behavior (THIS SHOULD CHANGE A LOT)
- Admiration: +/- 0.5-2.5 points based on impressive/disappointing actions
- Romantic Interest: +/- 0.5-2.0 points for flirty/dismissive interactions (marriageable NPCs only)
- Humor Compatibility: +/- 0.5-2.0 points based on joke success/failure

**IMPORTANT:** 
- If player chose provocative/teasing responses, INCREASE annoyance significantly (3-6 points)
- If player was consistently rude, DROP friendliness, trust, respect, and affection substantially
- If player was very kind, INCREASE affection, trust, and respect meaningfully
- The summary should reflect the change in tone - from neutral to positive/negative based on interactions

Make substantial changes (1.0-3.0 points per conversation for key metrics). Scores must be between 0 and 10.
The summary must be concise, no more than 60 words, reflecting {conversation["npc_name"]}'s UPDATED emotional state.

Provide the response in JSON format with these exact keys:
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

            if not self.client:
                logger.warning("No Gemini client available for personality update")
                return

            # Llamar al LLM
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-06-17", contents=prompt
            )

            # Parsear respuesta JSON
            try:
                response_text = getattr(response, "text", "") or str(response)
                if response_text:
                    new_profile = json.loads(response_text.strip())
                else:
                    logger.warning("Empty response from LLM for personality update")
                    return

                # Actualizar perfil en la base de datos
                await db.execute_raw(
                    """UPDATE "PlayerPersonalityProfile" 
                       SET summary = $1, friendliness = $2, extroversion = $3, sincerity = $4, curiosity = $5,
                           trust = $6, respect = $7, affection = $8, annoyance = $9, admiration = $10,
                           romantic_interest = $11, humor_compatibility = $12, "updatedAt" = NOW()
                       WHERE "playerId" = $13 AND "npcId" = $14""",
                    new_profile["new_summary"],
                    float(new_profile["new_friendliness"]),
                    float(new_profile["new_extroversion"]),
                    float(new_profile["new_sincerity"]),
                    float(new_profile["new_curiosity"]),
                    float(new_profile["new_trust"]),
                    float(new_profile["new_respect"]),
                    float(new_profile["new_affection"]),
                    float(new_profile["new_annoyance"]),
                    float(new_profile["new_admiration"]),
                    float(new_profile["new_romantic_interest"]),
                    float(new_profile["new_humor_compatibility"]),
                    conversation["playerId"],
                    conversation["npcId"],
                )

                logger.info(
                    f"Updated comprehensive personality profile for {conversation['player_name']} -> {conversation['npc_name']}"
                )

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing personality update JSON: {e}")
                logger.debug("Check response format from LLM")

        except Exception as e:
            logger.error(f"Error updating personality profile: {e}")

    def generate_relationship_insight(self, personality_profile: Dict[str, Any], player_name: str, npc_name: str) -> str:
        """Genera un insight legible sobre cómo el NPC percibe al jugador"""
        
        # Métricas básicas de personalidad
        friendliness = personality_profile['friendliness']
        extroversion = personality_profile['extroversion'] 
        sincerity = personality_profile['sincerity']
        curiosity = personality_profile['curiosity']
        
        # Métricas emocionales avanzadas
        trust = personality_profile['trust']
        respect = personality_profile['respect']
        affection = personality_profile['affection']
        annoyance = personality_profile['annoyance']
        admiration = personality_profile['admiration']
        romantic_interest = personality_profile['romantic_interest']
        humor_compatibility = personality_profile['humor_compatibility']
        
        summary = personality_profile['summary']
        
        # Determinar el nivel general de la relación usando todas las métricas
        positive_metrics = [friendliness, trust, respect, affection, admiration, humor_compatibility]
        negative_metrics = [annoyance]
        
        # Calcular puntaje general (penalizar más la irritación y dar más peso al afecto)
        avg_positive = sum(positive_metrics) / len(positive_metrics)
        avg_negative = sum(negative_metrics) / len(negative_metrics)
        
        # Dar más peso a métricas clave como afecto, confianza y irritación
        weighted_score = (
            (friendliness * 1.2) + 
            (trust * 1.3) + 
            (respect * 1.0) + 
            (affection * 1.5) + 
            (admiration * 0.8) + 
            (humor_compatibility * 0.7) - 
            (annoyance * 2.0)  # La irritación resta mucho más
        ) / 7.5  # Normalizar
        
        relationship_score = max(0, min(10, weighted_score))  # Mantener entre 0-10
        
        # Determinar nivel de relación y emoji
        if relationship_score >= 8.5:
            relationship_level = "EXTRAORDINARIA ✨💕"
        elif relationship_score >= 7.5:
            relationship_level = "EXCELENTE �"
        elif relationship_score >= 6.5:
            relationship_level = "MUY BUENA �"
        elif relationship_score >= 5.5:
            relationship_level = "BUENA �"
        elif relationship_score >= 4.5:
            relationship_level = "NEUTRAL �"
        elif relationship_score >= 3.5:
            relationship_level = "TENSA 😒"
        elif relationship_score >= 2.5:
            relationship_level = "MALA 😠"
        elif relationship_score >= 1.5:
            relationship_level = "MUY MALA 💢"
        else:
            relationship_level = "ODIO 🤬"
        
        # Generar descripciones específicas para métricas básicas
        def get_desc(value, low_desc, mid_desc, high_desc):
            if value >= 7: return high_desc
            elif value >= 4: return mid_desc
            else: return low_desc
        
        friendliness_desc = get_desc(friendliness, "hostil", "cordial", "muy amistoso")
        trust_desc = get_desc(trust, "desconfiado", "cauteloso", "confiable")
        respect_desc = get_desc(respect, "irrespetuoso", "respetuoso", "muy respetado")
        affection_desc = get_desc(affection, "indiferente", "agradable", "querido")
        
        # Métricas especiales
        annoyance_desc = "muy molesto" if annoyance >= 7 else "algo irritante" if annoyance >= 4 else "tolerable"
        admiration_desc = get_desc(admiration, "ordinario", "interesante", "admirable")
        humor_desc = get_desc(humor_compatibility, "sin gracia", "divertido", "muy gracioso")
        
        # Romantic interest (solo mostrar si es significativo)
        romantic_desc = ""
        if romantic_interest >= 6:
            romantic_desc = "💖 ¡Hay chispas románticas!"
        elif romantic_interest >= 4:
            romantic_desc = "💕 Siente cierta atracción"
        elif romantic_interest >= 2:
            romantic_desc = "💭 Podría haber algo..."
        
        insight = f"""
🎭 RELACIÓN {npc_name} → {player_name}: {relationship_level}
📝 Percepción: "{summary}"

📊 MÉTRICAS BÁSICAS:
   • Amistosidad: {friendliness:.1f}/10 ({friendliness_desc})
   • Extroversión: {extroversion:.1f}/10 
   • Sinceridad: {sincerity:.1f}/10 
   • Curiosidad: {curiosity:.1f}/10

💭 MÉTRICAS EMOCIONALES:
   • Confianza: {trust:.1f}/10 ({trust_desc})
   • Respeto: {respect:.1f}/10 ({respect_desc})
   • Afecto: {affection:.1f}/10 ({affection_desc})
   • Irritación: {annoyance:.1f}/10 ({annoyance_desc})
   • Admiración: {admiration:.1f}/10 ({admiration_desc})
   • Humor: {humor_compatibility:.1f}/10 ({humor_desc})"""
        
        if romantic_desc:
            insight += f"\n   • Romance: {romantic_interest:.1f}/10 ({romantic_desc})"
        
        # Resumen emocional
        if relationship_score >= 8:
            emotional_summary = f"💫 {npc_name} adora a {player_name} y los considera especiales"
        elif relationship_score >= 6.5:
            emotional_summary = f"� {npc_name} realmente aprecia a {player_name}"
        elif relationship_score >= 5:
            emotional_summary = f"🤝 {npc_name} tiene una opinión positiva de {player_name}"
        elif relationship_score >= 3.5:
            emotional_summary = f"😐 {npc_name} es neutral hacia {player_name}"
        elif relationship_score >= 2:
            emotional_summary = f"😒 {npc_name} encuentra a {player_name} problemático"
        else:
            emotional_summary = f"💢 {npc_name} realmente no soporta a {player_name}"
            
        insight += f"\n\n{emotional_summary}"
        
        return insight

    def _get_default_personality_for_npc(self, npc_name: str) -> Dict[str, Any]:
        """Obtiene valores de personalidad por defecto personalizados según el NPC"""
        
        # Personalidades específicas de NPCs de Stardew Valley
        npc_defaults = {
            "Haley": {
                "summary": "A new person... they look like they don't know much about fashion or style. Probably another boring farmer.",
                "friendliness": 3.0,  # Haley es inicialmente fría
                "extroversion": 6.0,  # Es social pero superficial
                "sincerity": 4.0,     # No muy sincera al principio
                "curiosity": 3.0,     # No muy interesada en otros
                "trust": 3.5,         # Desconfiada al principio
                "respect": 2.5,       # No respeta mucho inicialmente
                "affection": 1.5,     # Muy poco afecto inicial
                "annoyance": 4.0,     # Se molesta fácilmente
                "admiration": 2.0,    # No admira a extraños
                "romantic_interest": 1.0,
                "humor_compatibility": 3.0,
            },
            "Abigail": {
                "summary": "Someone new! I wonder if they're into adventure and fun stuff, or if they're just another boring adult.",
                "friendliness": 6.0,  # Más amistosa naturalmente
                "extroversion": 7.0,  # Muy extrovertida
                "sincerity": 6.5,     # Bastante sincera
                "curiosity": 7.5,     # Muy curiosa
                "trust": 5.5,         # Moderadamente confiada
                "respect": 5.0,       # Neutral
                "affection": 4.0,     # Un poco de simpatía inicial
                "annoyance": 2.5,     # No se molesta fácilmente
                "admiration": 4.0,    # Abierta a admirar
                "romantic_interest": 2.0,
                "humor_compatibility": 6.5,
            },
            "Sebastian": {
                "summary": "Another person from town... probably wants to chat about boring small-town stuff. Hope they leave me alone to work.",
                "friendliness": 3.5,  # Reservado/antisocial
                "extroversion": 2.5,  # Muy introvertido
                "sincerity": 6.0,     # Honesto pero directo
                "curiosity": 4.0,     # Curiosidad moderada
                "trust": 4.0,         # Toma tiempo ganar su confianza
                "respect": 4.5,       # Neutral
                "affection": 2.0,     # Distante inicialmente
                "annoyance": 3.5,     # Se irrita con socialización forzada
                "admiration": 3.0,    # Escéptico
                "romantic_interest": 1.0,
                "humor_compatibility": 4.0,
            },
            "Penny": {
                "summary": "A new face in town. They seem nice enough... I hope they're not judgmental about my family situation.",
                "friendliness": 6.5,  # Amable por naturaleza
                "extroversion": 4.0,  # Tímida
                "sincerity": 7.5,     # Muy sincera
                "curiosity": 5.5,     # Interesada en otros
                "trust": 4.5,         # Cautelosa pero esperanzada
                "respect": 5.5,       # Respetuosa por defecto
                "affection": 4.5,     # Empática inicialmente
                "annoyance": 1.5,     # Rara vez se molesta
                "admiration": 4.5,    # Ve lo bueno en la gente
                "romantic_interest": 1.5,
                "humor_compatibility": 5.0,
            },
            "Alex": {
                "summary": "New person in town. Wonder if they're into sports or if they're one of those bookworm types.",
                "friendliness": 5.5,  # Sociable pero no profundo
                "extroversion": 7.5,  # Muy extrovertido
                "sincerity": 5.0,     # A veces superficial
                "curiosity": 4.0,     # No muy curioso intelectualmente
                "trust": 5.0,         # Neutral
                "respect": 4.0,       # Debe ganarse su respeto
                "affection": 3.5,     # Neutral
                "annoyance": 3.0,     # Tolerable
                "admiration": 3.5,    # Admira fuerza/deporte
                "romantic_interest": 1.5,
                "humor_compatibility": 5.5,
            },
            "Elliott": {
                "summary": "A new soul graces our valley! Perhaps they possess an appreciation for the finer arts, or mayhap they are but another practical sort.",
                "friendliness": 7.0,  # Muy cordial
                "extroversion": 6.0,  # Social y dramático
                "sincerity": 6.5,     # Sincero aunque florido
                "curiosity": 7.0,     # Muy interesado en otros
                "trust": 5.5,         # Optimista sobre las personas
                "respect": 6.0,       # Respetuoso por naturaleza
                "affection": 4.5,     # Cálido inicialmente
                "annoyance": 2.0,     # Muy tolerante
                "admiration": 5.0,    # Aprecia el arte y la belleza
                "romantic_interest": 2.0,
                "humor_compatibility": 6.0,
            },
        }
        
        # Si no tenemos valores específicos para este NPC, usar valores genéricos pero más realistas
        if npc_name in npc_defaults:
            return npc_defaults[npc_name]
        else:
            # Valores por defecto más neutrales pero interesantes
            return {
                "summary": f"A newcomer to town. I'm curious to see what kind of person they really are.",
                "friendliness": 4.5,   # Ligeramente cauteloso
                "extroversion": 4.5,   # Neutral
                "sincerity": 5.0,      # Neutral
                "curiosity": 5.5,      # Ligeramente curioso
                "trust": 4.0,          # Necesita ganar confianza
                "respect": 4.5,        # Neutral
                "affection": 3.0,      # Poco afecto inicial
                "annoyance": 2.5,      # Baja irritación inicial
                "admiration": 3.5,     # Neutral
                "romantic_interest": 1.0,
                "humor_compatibility": 4.5,
            }


# Instancia global del servicio
memory_service = MemoryService()
