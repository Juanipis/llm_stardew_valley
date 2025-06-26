from google import genai
from fastapi import APIRouter, HTTPException
from ..models.request import DialogueRequest
from ..config import settings

router = APIRouter()


client = genai.Client(api_key=settings.gemini_api_key)


@router.post("/generate_dialogue")
async def generate_dialogue(request: DialogueRequest):
    try:
        prompt = f"""You are Lewis, the mayor of Stardew Valley. Generate a dialogue based on the following context:

        Player: {request.player_name}
        Friendship Hearts: {request.friendship_hearts}
        Season: {request.season}
        Day: {request.day_of_week}, {request.day_of_month}
        Time: {request.time_of_day}
        Weather: {request.weather}
        Location: {request.player_location}

        Your response should be in character, reflecting your personality as the mayor. Keep it relatively short and suitable for in-game dialogue."""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17", contents=prompt
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
