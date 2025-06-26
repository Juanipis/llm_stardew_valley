from google import genai
from fastapi import APIRouter, HTTPException
from ..models.request import DialogueRequest, DialogueResponse
from ..config import settings

router = APIRouter()

client = genai.Client(api_key=settings.gemini_api_key)


@router.post("/generate_dialogue", response_model=DialogueResponse)
async def generate_dialogue(request: DialogueRequest):
    try:
        print("Generating dialogue for:", request.player_name)
        print("Request details:", request)

        # Build conversation history string
        conversation_context = ""
        if request.conversation_history:
            conversation_context = "\n\nConversation history:\n"
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

Context:
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
3. Considers the friendship level and context
4. Is suitable for in-game dialogue

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
        response_text = response.text.strip()
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

        return DialogueResponse(
            npc_message=npc_message,
            response_options=options[:3],  # Ensure exactly 3 options
        )

    except Exception as e:
        print(f"Error generating dialogue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
