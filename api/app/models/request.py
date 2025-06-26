from pydantic import BaseModel


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
