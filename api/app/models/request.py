from pydantic import BaseModel
from typing import List, Optional


class ConversationEntry(BaseModel):
    speaker: str  # "player" or "npc"
    message: str


class DialogueRequest(BaseModel):
    npc_name: str
    npc_location: str
    player_name: str
    friendship_hearts: int
    season: str
    day_of_month: int
    day_of_week: int
    time_of_day: int
    year: int
    weather: str
    player_location: str
    language: str = "en"  # Default to English
    conversation_history: List[ConversationEntry] = []
    player_response: Optional[str] = None  # The player's chosen response


class DialogueResponse(BaseModel):
    npc_message: str
    response_options: List[str]
