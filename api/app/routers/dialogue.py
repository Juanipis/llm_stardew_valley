import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models.request import (
    DialogueRequest,
    DialogueResponse,
    EndConversationRequest,
    GiftInfo,
)
from ..config import settings
from ..services.memory_service import memory_service
from ..services.memory.emotional_state_service import emotional_state_service
from ..services.memory.analysis_service import analysis_service
from ..services.llm_service import llm_service
from ..websockets.realtime import realtime_monitor
from ..db import db
from app.data.gift_preferences import get_gift_preference, get_gift_context_for_ai

router = APIRouter()
logger = logging.getLogger(__name__)


async def calculate_immediate_friendship_change(
    player_response: str, personality_profile: dict, npc_name: str
) -> int:
    """
    Calculate immediate friendship change based on player response and NPC personality.
    Returns friendship points change (-50 to +50).
    """
    if not player_response or not player_response.strip():
        return 0

    try:
        # Simple sentiment analysis using keywords - MORE GENEROUS!
        response_lower = player_response.lower()

        # Base sentiment analysis - expanded positive words
        positive_words = [
            "yes",
            "yeah",
            "yep",
            "sure",
            "ok",
            "okay",
            "alright",
            "fine",
            "good",
            "great",
            "awesome",
            "love",
            "like",
            "enjoy",
            "thanks",
            "thank you",
            "please",
            "wonderful",
            "amazing",
            "beautiful",
            "nice",
            "happy",
            "glad",
            "excited",
            "interested",
            "cool",
            "sweet",
            "fantastic",
            "absolutely",
            "definitely",
            "of course",
            "perfect",
            "excellent",
            "brilliant",
            "magnificent",
            "superb",
            "marvelous",
            "impressive",
            "fun",
            "interesting",
            "curious",
            "appreciate",
            "helpful",
            "kind",
            "friendly",
            "warm",
            "pleasant",
            "lovely",
            "delightful",
            "understand",
            "agree",
            "support",
            "care",
            "concern",
            "worry about",
            "hope",
            "wish",
            "want",
            "would like",
            "sounds good",
        ]

        negative_words = [
            "no",
            "nope",
            "nah",
            "hate",
            "dislike",
            "stupid",
            "dumb",
            "boring",
            "terrible",
            "awful",
            "bad",
            "ugly",
            "disgusting",
            "annoying",
            "irritating",
            "frustrating",
            "whatever",
            "don't care",
            "couldn't care less",
            "shut up",
            "leave me alone",
            "go away",
            "idiot",
            "loser",
            "pathetic",
            "worthless",
            "useless",
            "ridiculous",
            "absurd",
            "nonsense",
        ]

        rude_words = [
            "fuck",
            "shit",
            "damn",
            "hell",
            "bitch",
            "asshole",
            "jerk",
            "freak",
            "bastard",
            "crap",
        ]

        # Count sentiment indicators with more weight to positive
        positive_count = sum(1 for word in positive_words if word in response_lower)
        negative_count = sum(1 for word in negative_words if word in response_lower)
        rude_count = sum(1 for word in rude_words if word in response_lower)

        # Base sentiment score (-1.0 to 1.0) - more generous to positive
        base_sentiment = 0.2  # Start slightly positive instead of neutral
        if positive_count > 0:
            base_sentiment = min(
                1.0, 0.2 + positive_count * 0.4
            )  # Stronger positive boost
        elif negative_count > 0 or rude_count > 0:
            base_sentiment = max(
                -1.0, -(negative_count * 0.2 + rude_count * 0.4)
            )  # Less harsh negative

        # Adjust based on NPC personality
        friendliness = personality_profile.get("friendliness", 5.0)
        annoyance = personality_profile.get("annoyance", 2.0)
        trust = personality_profile.get("trust", 5.0)
        humor_compatibility = personality_profile.get("humor_compatibility", 5.0)

        # NPC-specific adjustments
        personality_multiplier = 1.0

        # Friendly NPCs are more forgiving and reward positive responses more
        if friendliness >= 7.0:
            if base_sentiment > 0:
                personality_multiplier *= 1.3  # Boost positive responses
            elif base_sentiment < 0:
                personality_multiplier *= 0.7  # Reduce negative impact

        # Grumpy NPCs (high annoyance) are harder to please
        elif annoyance >= 6.0:
            if base_sentiment > 0:
                personality_multiplier *= 0.8  # Reduce positive impact
            else:
                personality_multiplier *= 1.4  # Amplify negative responses

        # Trust affects how they interpret responses
        if trust <= 3.0 and base_sentiment > 0:
            personality_multiplier *= (
                0.9  # Suspicious NPCs don't trust positive responses easily
            )

        # Special cases for specific NPCs - BALANCED!
        if npc_name == "Shane" and base_sentiment > 0.3:
            personality_multiplier *= 0.8  # Shane is grumpy but fair
        elif npc_name == "Haley" and base_sentiment < 0:
            personality_multiplier *= 1.1  # Haley gets slightly offended
        elif npc_name == "Emily":
            if base_sentiment > 0:
                personality_multiplier *= 1.2  # Emily appreciates positive energy
            else:
                personality_multiplier *= 0.8  # Emily is somewhat forgiving
        elif npc_name == "Gus" and base_sentiment > 0:
            personality_multiplier *= 1.1  # Gus is welcoming
        elif npc_name in ["Penny", "Harvey", "Elliott", "Leah"] and base_sentiment > 0:
            personality_multiplier *= 1.1  # These NPCs appreciate kindness
        elif npc_name in ["Abigail", "Sam", "Maru"] and base_sentiment > 0:
            personality_multiplier *= (
                1.05  # Younger NPCs are slightly more enthusiastic
            )

        # Calculate final friendship change (scale to -20 to +40 points) - BALANCED!
        adjusted_sentiment = base_sentiment * personality_multiplier

        # Balanced positive responses
        if adjusted_sentiment > 0:
            friendship_change = int(
                round(adjusted_sentiment * 30)
            )  # Reduced from 60 to 30
            friendship_change = max(
                5, min(40, friendship_change)
            )  # Minimum +5, max +40
        else:
            friendship_change = int(
                round(adjusted_sentiment * 20)
            )  # Reduced negative impact
            friendship_change = max(
                -20, min(-2, friendship_change)
            )  # Less severe negative impact

        logger.info(
            f"Friendship calculation for {npc_name}: "
            f"response='{player_response[:30]}...', "
            f"base_sentiment={base_sentiment:.2f}, "
            f"personality_mult={personality_multiplier:.2f}, "
            f"final_change={friendship_change}"
        )

        return friendship_change

    except Exception as e:
        logger.error(f"Error calculating friendship change: {e}")
        return 0


async def calculate_gift_friendship_change(gift_info: "GiftInfo", npc_name: str) -> int:
    """
    Calculate friendship change based on a gift given to an NPC.
    If gift_preference is "unknown", the AI will decide based on the item and NPC.
    Returns friendship points change based on gift preference and quality.
    """
    try:
        # If the game didn't provide preference, let AI decide
        if gift_info.gift_preference == "unknown":
            gift_info.gift_preference = await determine_gift_preference_with_ai(
                gift_info.item_name, gift_info.item_category, npc_name
            )
            logger.info(
                f"AI determined gift preference: {gift_info.item_name} is {gift_info.gift_preference} by {npc_name}"
            )

        base_points = {
            "loved": 80,
            "liked": 45,
            "neutral": 20,
            "disliked": -20,
            "hated": -40,
        }

        # Get base points from preference
        points = base_points.get(gift_info.gift_preference, 20)

        # Quality multiplier (0=normal, 1=silver, 2=gold, 3=iridium)
        quality_multipliers = {0: 1.0, 1: 1.25, 2: 1.5, 3: 2.0}
        quality_multiplier = quality_multipliers.get(gift_info.item_quality, 1.0)

        # Birthday bonus
        if gift_info.is_birthday:
            points = int(points * 8)  # Birthday gifts are 8x more effective
            logger.info(f"Birthday bonus applied for {npc_name}!")

        # Apply quality multiplier
        final_points = int(points * quality_multiplier)

        # NPC-specific adjustments based on personality
        final_points = apply_npc_specific_adjustments(final_points, gift_info, npc_name)

        logger.info(
            f"Gift calculation: {gift_info.item_name} ({gift_info.gift_preference}) "
            f"to {npc_name} = {final_points} points "
            f"(base: {points}, quality: {quality_multiplier}x, birthday: {gift_info.is_birthday})"
        )

        return final_points

    except Exception as e:
        logger.error(f"Error calculating gift friendship change: {e}")
        return 20  # Default neutral gift value


async def determine_gift_preference_with_ai(
    item_name: str, item_category: str, npc_name: str
) -> str:
    """
    Use AI to determine how much an NPC would like a specific gift.
    Now enhanced with official Stardew Valley gift preference data.
    """
    try:
        # First, check if we have official data for this gift
        official_preference = get_gift_preference(npc_name, item_name)

        # If we have official data and it's not neutral, use it directly
        if official_preference != "neutral":
            logger.info(
                f"Using official game data: {item_name} is {official_preference} by {npc_name}"
            )
            return official_preference

        # For neutral items or items not in our database, use AI with full context
        gift_context = get_gift_context_for_ai(npc_name, item_name, item_category)

        # Enhanced AI prompt with official game data context
        preference_prompt = f"""{gift_context}

TASK: The player is giving "{item_name}" (category: {item_category}) to {npc_name}. 

INSTRUCTIONS:
1. The "OFFICIAL GAME PREFERENCE" above shows the actual game data for this item-NPC combination
2. If the official preference is "loved", "liked", "disliked", or "hated", return that EXACT value
3. If the official preference is "neutral" or the item isn't in the database, use {npc_name}'s personality and the patterns from their loved/liked gifts to make an informed decision
4. Consider the item category and how it relates to {npc_name}'s interests
5. Be consistent with the official game's gift preference patterns

{npc_name}'S PERSONALITY CONTEXT:
- Abigail: Adventurous gamer who likes mysterious/exciting things and purple items
- Alex: Athletic jock who likes hearty food and sports, dislikes refined/artsy things  
- Caroline: Health-conscious, likes tea and natural items
- Clint: Blacksmith who loves gems, metals, and mining-related items
- Demetrius: Scientist who appreciates fruits and scientific approach to things
- Elliott: Romantic writer who likes sophisticated/poetic items and seafood
- Emily: Spiritual/mystical, loves gems, crystals, and unique colorful items
- Evelyn: Sweet grandmother who likes flowers, baking, and wholesome things
- George: Grumpy old man with simple tastes, dislikes most things
- Gus: Friendly chef who loves cooking ingredients and fine foods
- Haley: Fashion-conscious, likes pretty/cute things, dislikes dirty/weird items
- Harvey: Health-focused doctor who likes coffee, pickles, and healthy foods
- Kent: Veteran with PTSD, likes simple comfort foods, avoids conflict
- Leah: Nature-loving artist who likes natural items, foraging, and simple living
- Lewis: Mayor who likes fancy vegetables and civic responsibility
- Linus: Homeless but wise, likes foraged items and simple natural foods
- Marnie: Ranch owner who likes farm-related items and hearty meals
- Maru: Young scientist/inventor who likes technology, gadgets, and sciences
- Pam: Alcoholic bus driver who likes beer and simple comfort foods
- Penny: Shy teacher who likes books, flowers, and quiet thoughtful gifts
- Pierre: Shopkeeper who's competitive and likes profitable items
- Robin: Carpenter who likes wood-related items and hearty meals
- Sam: Young musician who likes junk food, music, and fun things
- Sandy: Desert shop owner who likes flowers and cheerful items
- Sebastian: Goth programmer who likes dark/edgy items and solitude
- Shane: Depressed alcoholic who likes beer, spicy food, and simple pleasures
- Vincent: Young boy who likes candy, colorful things, and childish items
- Willy: Old fisherman who loves fish and the ocean
- Wizard: Mysterious mage who likes magical/mystical items

Respond with ONLY one word: loved, liked, neutral, disliked, or hated"""

        # Call LLM to determine preference
        messages = [{"role": "user", "content": preference_prompt}]
        response = await llm_service.acompletion(
            model=settings.dialogue_model, messages=messages
        )

        preference = response.choices[0].message.content.strip().lower()

        # Validate the response
        valid_preferences = ["loved", "liked", "neutral", "disliked", "hated"]
        if preference in valid_preferences:
            logger.info(
                f"AI determined preference for {item_name} to {npc_name}: {preference}"
            )
            return preference
        else:
            logger.warning(
                f"AI returned invalid preference '{preference}', using official data: {official_preference}"
            )
            return official_preference

    except Exception as e:
        logger.error(f"Error determining gift preference with AI: {e}")
        return "neutral"  # Safe default


def apply_npc_specific_adjustments(
    points: int, gift_info: "GiftInfo", npc_name: str
) -> int:
    """
    Apply NPC-specific personality adjustments to gift friendship points.
    """
    try:
        multiplier = 1.0

        # Personality-based adjustments
        if npc_name == "Shane":
            if gift_info.gift_preference in ["loved", "liked"]:
                multiplier *= 0.9  # Shane is slightly harder to please
        elif npc_name == "Emily":
            if gift_info.gift_preference == "loved":
                multiplier *= 1.2  # Emily really appreciates loved gifts
            elif gift_info.gift_preference in ["liked", "neutral"]:
                multiplier *= 1.1  # Emily appreciates most gifts
        elif npc_name in ["Penny", "Harvey", "Gus", "Robin", "Caroline"]:
            if gift_info.gift_preference in ["loved", "liked"]:
                multiplier *= 1.1  # Kind NPCs appreciate gifts more
        elif npc_name == "Haley":
            if gift_info.gift_preference == "disliked":
                multiplier *= 1.2  # Haley is more particular about gifts
        elif npc_name in ["Abigail", "Sam", "Maru"]:
            if gift_info.gift_preference in ["loved", "liked"]:
                multiplier *= 1.05  # Younger NPCs are enthusiastic

        return int(points * multiplier)

    except Exception as e:
        logger.error(f"Error applying NPC adjustments: {e}")
        return points


@router.post("/generate_dialogue", response_model=DialogueResponse)
async def generate_dialogue(
    request: DialogueRequest, background_tasks: BackgroundTasks
):
    try:
        logger.info("Generating dialogue for: %s", request.player_name)
        logger.debug("Request details: %s", request)

        # === ENHANCED MEMORY & EMOTIONAL SYSTEM ===

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
            emotional_context = ""
            conversation_id = ""
            personality_profile = {}
        else:
            # 2. Get NPC's current emotional state towards this player
            logger.debug(
                "Retrieving emotional state for NPC %s towards player %s",
                npc_id,
                player_id,
            )
            emotional_state = await emotional_state_service.get_emotional_state(
                npc_id, player_id
            )
            emotional_context = (
                emotional_state_service.generate_mood_context_for_dialogue(
                    emotional_state
                )
            )

            # 3. Obtener perfil de personalidad
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
            relationship_insight = await memory_service.generate_relationship_insight(
                personality_profile,
                request.player_name,
                request.npc_name,
                npc_id,
                player_id,
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

            # 4. Enhanced memory search with human-like weighting
            relevant_memories_str = ""
            if request.player_response:
                # Search for relevant memories with enhanced weighting
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

                        # Include emotional and importance scores for context
                        memory_details = f"- {speaker} once said: '{memory['message']}'"
                        if memory.get("emotional_score", 0) > 7:
                            memory_details += (
                                " (This memory feels emotionally significant)"
                            )
                        if memory.get("location"):
                            memory_details += f" [at {memory['location']}]"
                        if memory.get("season"):
                            memory_details += f" [during {memory['season']}]"

                        memory_context += memory_details + "\n"
                    relevant_memories_str = memory_context

            # 5. Obtener o crear conversación activa
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

        # === CALCULATE IMMEDIATE FRIENDSHIP CHANGE ===
        friendship_points_change = 0

        # Handle gift-giving first
        if request.gift_given:
            friendship_points_change = await calculate_gift_friendship_change(
                request.gift_given, request.npc_name
            )
            logger.info(
                f"Gift given - {request.gift_given.item_name} to {request.npc_name}: {friendship_points_change} friendship points"
            )
        elif request.player_response and personality_profile:
            friendship_points_change = await calculate_immediate_friendship_change(
                request.player_response, personality_profile, request.npc_name
            )
            logger.info(
                f"Calculated friendship change: {friendship_points_change} points for {request.npc_name}"
            )

        # === ENHANCED DIALOGUE PROMPT WITH EMOTIONAL STATE ===

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

        # Add gift context if a gift was given
        gift_context = ""
        if request.gift_given:
            quality_names = {0: "normal", 1: "silver", 2: "gold", 3: "iridium"}
            quality_name = quality_names.get(request.gift_given.item_quality, "normal")

            gift_context = f"\n\n**GIFT RECEIVED:**\n{request.player_name} just gave you a {quality_name} quality {request.gift_given.item_name}"

            if request.gift_given.is_birthday:
                gift_context += (
                    " (IT'S YOUR BIRTHDAY! This gift means extra much to you!)"
                )

            if request.gift_given.gift_preference == "loved":
                gift_context += (
                    "\nYou LOVE this gift! It's one of your absolute favorites!"
                )
            elif request.gift_given.gift_preference == "liked":
                gift_context += "\nYou like this gift. It's quite nice!"
            elif request.gift_given.gift_preference == "disliked":
                gift_context += (
                    "\nYou don't really like this gift. It's not your taste."
                )
            elif request.gift_given.gift_preference == "hated":
                gift_context += "\nYou HATE this gift! It's awful and offensive to you!"
            else:
                gift_context += (
                    "\nThis is an okay gift. Nothing special, but the thought counts."
                )

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

**YOUR CURRENT EMOTIONAL STATE:**
{emotional_context}

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
{gift_context}

Generate a response as {request.npc_name} that:
1. Responds naturally to the conversation{" and especially to any gift received" if request.gift_given else ""}
2. Reflects {request.npc_name}'s personality and role in Stardew Valley
3. Considers the friendship level and your perception of {request.player_name}
4. References relevant memories if appropriate and meaningful
5. Shows your current emotional state through tone and word choice
6. Is suitable for in-game dialogue{"" if not request.gift_given else f"\n7. IMPORTANT: React appropriately to the {request.gift_given.gift_preference} gift you just received. Show genuine emotion!"}

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

        messages = [{"role": "user", "content": prompt}]

        response = await llm_service.acompletion(
            model=settings.dialogue_model, messages=messages
        )

        # Parse the response
        response_text = response.choices[0].message.content
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

        # === ENHANCED MEMORY SAVING WITH EMBEDDINGS ===
        if conversation_id:
            logger.debug("Saving dialogue to conversation: %s", conversation_id)

            # Guardar el mensaje del NPC con embedding
            await memory_service.add_dialogue_entry(
                conversation_id,
                request.npc_name,
                npc_message,
                generate_embedding=True,  # Enable embeddings
            )
            logger.debug("Saved NPC message: %s", npc_message[:50] + "...")

            # Si hay respuesta del jugador, también guardarla con embedding
            if request.player_response:
                await memory_service.add_dialogue_entry(
                    conversation_id,
                    "player",
                    request.player_response,
                    generate_embedding=True,  # Enable embeddings
                )
                logger.debug(
                    "Saved player response: %s", request.player_response[:50] + "..."
                )

                # Send real-time notification for new dialogue
                await realtime_monitor.notify_new_dialogue(
                    {
                        "conversation_id": conversation_id,
                        "player_name": request.player_name,
                        "npc_name": request.npc_name,
                        "player_message": request.player_response,
                        "npc_message": npc_message,
                        "location": request.player_location,
                        "friendship_hearts": request.friendship_hearts,
                        "friendship_change": friendship_points_change,
                    }
                )

        else:
            logger.warning("No conversation ID available, not saving to memory")

        return DialogueResponse(
            npc_message=npc_message,
            response_options=options[:3],  # Ensure exactly 3 options
            friendship_change=friendship_points_change,  # Return the calculated friendship change
        )

    except Exception as e:
        logger.error("Error generating dialogue: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end_conversation")
async def end_conversation(
    request: EndConversationRequest, background_tasks: BackgroundTasks
):
    """Triggers the new unified post-conversation analysis service."""
    try:
        player_name = request.player_name
        npc_name = request.npc_name

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
            logger.warning(
                f"No active conversation found for {player_name} and {npc_name}"
            )
            return {"message": "No active conversation found - nothing to end."}

        conversation_id = result[0]["id"]

        # Marcar conversación como terminada
        await memory_service.end_conversation(conversation_id)

        # NEW: Trigger the single, unified analysis service in the background
        background_tasks.add_task(
            analysis_service.analyze_conversation_and_update_memory, conversation_id
        )

        logger.info(
            f"Conversation ended between {player_name} and {npc_name} - triggering unified memory analysis."
        )

        return {
            "message": "Conversation ended successfully - unified analysis will be performed.",
            "conversation_id": conversation_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error ending conversation: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gift_preferences/{npc_name}")
async def get_npc_gift_preferences(npc_name: str):
    """Get gift preferences for a specific NPC."""
    try:
        from app.data.gift_preferences import (
            VILLAGER_GIFT_PREFERENCES,
            get_npc_birthday,
            get_npc_loved_gifts,
        )

        if npc_name not in VILLAGER_GIFT_PREFERENCES:
            raise HTTPException(
                status_code=404, detail=f"NPC '{npc_name}' not found in gift database"
            )

        preferences = VILLAGER_GIFT_PREFERENCES[npc_name]
        birthday = get_npc_birthday(npc_name)
        loved_gifts = get_npc_loved_gifts(npc_name)

        return {
            "npc_name": npc_name,
            "birthday": birthday,
            "preferences": preferences,
            "loved_gifts_total": loved_gifts,
            "summary": {
                "loved_count": len(preferences.get("loved", [])),
                "liked_count": len(preferences.get("liked", [])),
                "disliked_count": len(preferences.get("disliked", [])),
                "hated_count": len(preferences.get("hated", [])),
            },
        }
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Gift preferences database not available"
        )
    except Exception as e:
        logger.error(f"Error getting gift preferences for {npc_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gift_preferences")
async def get_all_gift_preferences():
    """Get gift preferences for all NPCs."""
    try:
        from app.data.gift_preferences import (
            VILLAGER_GIFT_PREFERENCES,
            VILLAGER_BIRTHDAYS,
        )

        npcs_data = {}
        for npc_name in VILLAGER_GIFT_PREFERENCES:
            preferences = VILLAGER_GIFT_PREFERENCES[npc_name]
            npcs_data[npc_name] = {
                "birthday": VILLAGER_BIRTHDAYS.get(npc_name, "Unknown"),
                "loved_count": len(preferences.get("loved", [])),
                "liked_count": len(preferences.get("liked", [])),
                "disliked_count": len(preferences.get("disliked", [])),
                "hated_count": len(preferences.get("hated", [])),
                "top_loved_gifts": preferences.get("loved", [])[
                    :5
                ],  # Show top 5 loved gifts
            }

        return {"total_npcs": len(npcs_data), "npcs": npcs_data}
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Gift preferences database not available"
        )
    except Exception as e:
        logger.error(f"Error getting all gift preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check_gift_preference")
async def check_gift_preference(request: dict):
    """Check how much a specific NPC would like a specific gift."""
    try:
        npc_name = request.get("npc_name")
        item_name = request.get("item_name")
        item_category = request.get("item_category", "Unknown")

        if not npc_name or not item_name:
            raise HTTPException(
                status_code=400, detail="npc_name and item_name are required"
            )

        from app.data.gift_preferences import (
            get_gift_preference,
            get_gift_context_for_ai,
        )

        # Get official preference
        official_preference = get_gift_preference(npc_name, item_name)

        # Get the AI context for additional information
        context = get_gift_context_for_ai(npc_name, item_name, item_category)

        return {
            "npc_name": npc_name,
            "item_name": item_name,
            "item_category": item_category,
            "official_preference": official_preference,
            "source": "official_game_data"
            if official_preference != "neutral"
            else "ai_inference",
            "context": context,
        }
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Gift preferences database not available"
        )
    except Exception as e:
        logger.error(f"Error checking gift preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))
