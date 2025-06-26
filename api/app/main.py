from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from .routers import dialogue
from .db import db

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our modules
logging.getLogger("app.services.memory_service").setLevel(logging.DEBUG)
logging.getLogger("app.routers.dialogue").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🔗 Connecting to database...")
    await db.connect()
    logger.info("✅ Database connected successfully!")

    yield

    # Shutdown
    logger.info("🔌 Disconnecting from database...")
    await db.disconnect()
    logger.info("👋 Database disconnected!")


app = FastAPI(lifespan=lifespan)

app.include_router(dialogue.router)
