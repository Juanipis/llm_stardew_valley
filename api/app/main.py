from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from .routers import dialogue, monitoring, websocket_router
from .db import db

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set debug level for our modules
logging.getLogger("app.services.memory_service").setLevel(logging.DEBUG)
logging.getLogger("app.routers.dialogue").setLevel(logging.DEBUG)
logging.getLogger("app.routers.monitoring").setLevel(logging.DEBUG)

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


app = FastAPI(
    title="StardewEchoes API",
    description="AI-powered dialogue system for Stardew Valley with real-time monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files (if needed in the future)
# static_dir = os.path.join(os.path.dirname(__file__), "static")
# if os.path.exists(static_dir):
#     app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(dialogue.router, tags=["dialogue"])
app.include_router(monitoring.router, tags=["monitoring"])
app.include_router(websocket_router.router, tags=["websockets"])
