from google import genai
from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from ..models.request import DialogueRequest, DialogueResponse
from ..config import settings
from ..services.memory_service import memory_service
from ..db import db

router = APIRouter()
logger = logging.getLogger(__name__)

client = (
    genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
)


@router.post("/generate_dialogue", response_model=DialogueResponse)
async def generate_dialogue(
    request: DialogueRequest, background_tasks: BackgroundTasks
):
    try:
        logger.info("Generating dialogue for: %s", request.player_name)
        logger.debug("Request details: %s", request)

        if not client:
            raise HTTPException(status_code=500, detail="Gemini API not configured")

        # === NUEVA LÓGICA DE MEMORIA ===

        # 1. Obtener o crear jugador y NPC
        logger.debug("Creating/retrieving player: %s", request.player_name)
        player_id = await memory_service.get_or_create_player(request.player_name)
        logger.debug("Player ID: %s", player_id)

        logger.debug("Creating/retrieving NPC: %s", request.npc_name)
        npc_id = await memory_service.get_or_create_npc(
            request.npc_name, request.npc_location
        )
        logger.debug("NPC ID: %s", npc_id)

        if not player_id or not npc_id:
            logger.warning(
                "Error creating player or NPC, falling back to basic dialogue"
            )
            personality_context = ""
            relevant_memories_str = ""
            conversation_id = ""
        else:
            # 2. Obtener perfil de personalidad
            logger.debug(
                "Retrieving personality profile for player %s and NPC %s",
                player_id,
                npc_id,
            )
            personality_profile = await memory_service.get_personality_profile(
                player_id, npc_id
            )
            logger.debug("Personality profile: %s", personality_profile)

            # 🎭 GENERAR INSIGHT DE RELACIÓN
            relationship_insight = memory_service.generate_relationship_insight(
                personality_profile, request.player_name, request.npc_name
            )
            logger.info("=== RELATIONSHIP INSIGHT ===")
            for line in relationship_insight.strip().split("\n"):
                logger.info(line)
            logger.info("==============================")
            personality_context = f"""
**Your current perception of {request.player_name}:**
{personality_profile["summary"]}

**Basic Personality Metrics:**
- Friendliness: {personality_profile["friendliness"]:.1f}/10
- Extroversion: {personality_profile["extroversion"]:.1f}/10  
- Sincerity: {personality_profile["sincerity"]:.1f}/10
- Curiosity: {personality_profile["curiosity"]:.1f}/10

**Emotional Relationship Metrics:**
- Trust: {personality_profile["trust"]:.1f}/10 (How much you trust them)
- Respect: {personality_profile["respect"]:.1f}/10 (How much you respect them)
- Affection: {personality_profile["affection"]:.1f}/10 (How much you care about them)
- Annoyance: {personality_profile["annoyance"]:.1f}/10 (How much they irritate you)
- Admiration: {personality_profile["admiration"]:.1f}/10 (How much you admire them)
- Romantic Interest: {personality_profile["romantic_interest"]:.1f}/10 (Any romantic feelings)
- Humor Compatibility: {personality_profile["humor_compatibility"]:.1f}/10 (How funny you find them)

IMPORTANT: Adjust your tone, dialogue, and responses based on these metrics. High affection = warmer, low trust = more guarded, high annoyance = more irritated or short responses, high romantic interest = flirtier (if appropriate for the character), etc."""

            # 3. Recuperar recuerdos relevantes si hay respuesta del jugador
            relevant_memories_str = ""
            if request.player_response:
                relevant_memories = await memory_service.search_relevant_memories(
                    player_id, npc_id, request.player_response
                )

                if relevant_memories:
                    memory_context = "\n**Relevant memories you recall:**\n"
                    for memory in relevant_memories:
                        speaker = (
                            "You"
                            if memory["speaker"] == request.npc_name
                            else request.player_name
                        )
                        memory_context += (
                            f"- {speaker} once said: '{memory['message']}'\n"
                        )
                    relevant_memories_str = memory_context

            # 4. Obtener o crear conversación activa
            context_data = {
                "season": request.season,
                "day_of_month": request.day_of_month,
                "day_of_week": request.day_of_week,
                "time_of_day": request.time_of_day,
                "year": request.year,
                "weather": request.weather,
                "player_location": request.player_location,
                "friendship_hearts": request.friendship_hearts,
            }

            conversation_id = await memory_service.get_or_create_active_conversation(
                player_id, npc_id, context_data
            )

        # === CONSTRUCCIÓN DEL PROMPT MEJORADO ===

        # Build conversation history string
        conversation_context = ""
        if request.conversation_history:
            conversation_context = "\n\n**Recent conversation in this interaction:**\n"
            for entry in request.conversation_history:
                speaker = "Player" if entry.speaker == "player" else request.npc_name
                conversation_context += f"{speaker}: {entry.message}\n"

        # Add player response if provided
        if request.player_response:
            conversation_context += f"Player: {request.player_response}\n"

        # Language instruction
        language_instruction = ""
        if request.language == "es":
            language_instruction = "Respond in Spanish."
        elif request.language == "en":
            language_instruction = "Respond in English."
        else:
            language_instruction = f"Respond in {request.language}."

        prompt = f"""You are {request.npc_name}, a character from Stardew Valley. Generate a dialogue response and conversation options based on the following context.

IMPORTANT INSTRUCTIONS:
- Do NOT use markdown formatting or special characters like *, **, [], etc.
- Do NOT use placeholder text like [Player Name] - use the actual player name: {request.player_name}
- Write everything in plain text
- Be natural and conversational
- Stay in character as {request.npc_name}
- {language_instruction}
- VERY IMPORTANT: The NPC message and each player response option must be no longer than 30 words. Keep them concise and short so they fit on the game screen but sometimes some can be longer, depends of the context.

{personality_context}
{relevant_memories_str}

**Current Context:**
Player: {request.player_name}
NPC: {request.npc_name}
Friendship Hearts: {request.friendship_hearts}
Season: {request.season}
Day: {request.day_of_week}, {request.day_of_month}
Time: {request.time_of_day}
Weather: {request.weather}
Location: {request.player_location}
{conversation_context}

Generate a response as {request.npc_name} that:
1. Responds naturally to the conversation
2. Reflects {request.npc_name}'s personality and role in Stardew Valley
3. Considers the friendship level and your perception of {request.player_name}
4. References relevant memories if appropriate
5. Is suitable for in-game dialogue

Then provide exactly 3 response options for the player with these specific tones:
OPTION_1: A FRIENDLY/CORDIAL response - Be warm, kind, humorous, and cheerful. Show genuine interest and positivity.
OPTION_2: A NEUTRAL/INFORMATIVE response - Be polite but direct, focused on getting important information or business matters. Professional and to-the-point.
OPTION_3: A PROVOCATIVE/TEASING response - Be playfully mocking, sarcastic, or slightly rude. This should annoy or challenge the NPC (but not be truly offensive).

Each option should lead the conversation in a different emotional direction and potentially affect the NPC's reaction based on their personality.

Format your response exactly like this:
NPC_MESSAGE: [Your response as {request.npc_name}]
OPTION_1: [Friendly/cordial player response]
OPTION_2: [Neutral/informative player response]  
OPTION_3: [Provocative/teasing player response]"""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17", contents=prompt
        )

        # Parse the response
        response_text = getattr(response, "text", "") or str(response)
        lines = response_text.split("\n")

        npc_message = ""
        options = []

        for line in lines:
            line = line.strip()
            if line.startswith("NPC_MESSAGE:"):
                npc_message = line.replace("NPC_MESSAGE:", "").strip()
            elif line.startswith("OPTION_1:"):
                options.append(line.replace("OPTION_1:", "").strip())
            elif line.startswith("OPTION_2:"):
                options.append(line.replace("OPTION_2:", "").strip())
            elif line.startswith("OPTION_3:"):
                options.append(line.replace("OPTION_3:", "").strip())

        # Fallback if parsing fails
        if not npc_message:
            npc_message = response_text
        if len(options) < 3:
            if request.language == "es":
                options = [
                    "¡Me alegra verte! ¿Cómo has estado?",  # Friendly
                    "¿Hay algo importante que necesite saber?",  # Neutral
                    "¿Siempre tienes esa cara o es solo hoy?",  # Provocative
                ]
            else:
                options = [
                    "It's great to see you! How have you been?",  # Friendly
                    "Is there anything important I should know?",  # Neutral
                    "Do you always look like that or is it just today?",  # Provocative
                ]

        # === GUARDAR EN MEMORIA ===
        if conversation_id:
            logger.debug("Saving dialogue to conversation: %s", conversation_id)

            # Guardar el mensaje del NPC
            await memory_service.add_dialogue_entry(
                conversation_id,
                request.npc_name,
                npc_message,
                generate_embedding=False,  # Temporalmente sin embeddings
            )
            logger.debug("Saved NPC message: %s", npc_message[:50] + "...")

            # Si hay respuesta del jugador, también guardarla
            if request.player_response:
                await memory_service.add_dialogue_entry(
                    conversation_id,
                    "player",
                    request.player_response,
                    generate_embedding=False,  # Temporalmente sin embeddings
                )
                logger.debug(
                    "Saved player response: %s", request.player_response[:50] + "..."
                )
        else:
            logger.warning("No conversation ID available, not saving to memory")

        return DialogueResponse(
            npc_message=npc_message,
            response_options=options[:3],  # Ensure exactly 3 options
        )

    except Exception as e:
        logger.error("Error generating dialogue: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end_conversation")
async def end_conversation(
    player_name: str, npc_name: str, background_tasks: BackgroundTasks
):
    """Endpoint para marcar el fin de una conversación y disparar actualización de personalidad"""
    try:
        player_id = await memory_service.get_or_create_player(player_name)
        npc_id = await memory_service.get_or_create_npc(npc_name)

        if not player_id or not npc_id:
            raise HTTPException(status_code=404, detail="Player or NPC not found")

        # Buscar conversación activa
        from datetime import datetime, timedelta

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

        if not result:
            raise HTTPException(status_code=404, detail="No active conversation found")

        conversation_id = result[0]["id"]

        # Marcar conversación como terminada
        await memory_service.end_conversation(conversation_id)

        # Disparar actualización de personalidad en segundo plano
        background_tasks.add_task(
            memory_service.update_personality_profile_async, conversation_id
        )

        return {"message": "Conversation ended successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error ending conversation: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
