from fastapi import FastAPI
from .routers import dialogue

app = FastAPI()

app.include_router(dialogue.router)
