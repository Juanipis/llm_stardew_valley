from pydantic import BaseModel
from typing import List, Optional


class ConversationEntry(BaseModel):
    speaker: str  # "player" or "npc"
    message: str


class GiftInfo(BaseModel):
    item_name: str
    item_category: str
    item_quality: int = 0  # 0=normal, 1=silver, 2=gold, 3=iridium
    gift_preference: str = "neutral"  # loved, liked, neutral, disliked, hated
    is_birthday: bool = False


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
    gift_given: Optional[GiftInfo] = None  # Gift information if a gift was given


class EndConversationRequest(BaseModel):
    player_name: str
    npc_name: str


class DialogueResponse(BaseModel):
    npc_message: str
    response_options: List[str]
    friendship_change: int = 0
