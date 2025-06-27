import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from app.main import app
from app.db import db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_player():
    """Create a test player for memory tests."""
    # Clean up any existing test player
    existing_player = await db.player.find_unique(where={"name": "TestPlayer"})
    if existing_player:
        await db.player.delete(where={"id": existing_player.id})

    # Create fresh test player
    player = await db.player.create(data={"name": "TestPlayer"})
    yield player

    # Cleanup after test
    await db.player.delete(where={"id": player.id})


@pytest.fixture
async def test_npc():
    """Create a test NPC for memory tests."""
    # Clean up any existing test NPC
    existing_npc = await db.npc.find_unique(where={"name": "TestAbigail"})
    if existing_npc:
        await db.npc.delete(where={"id": existing_npc.id})

    # Create fresh test NPC
    npc = await db.npc.create(data={"name": "TestAbigail", "location": "TestTown"})
    yield npc

    # Cleanup after test
    await db.npc.delete(where={"id": npc.id})


@pytest.fixture
async def test_conversation(test_player, test_npc):
    """Create a test conversation for memory tests."""
    conversation = await db.conversation.create(
        data={
            "playerId": test_player.id,
            "npcId": test_npc.id,
            "season": "Spring",
            "dayOfMonth": 15,
            "year": 1,
            "weather": "Sunny",
            "playerLocation": "TestLocation",
            "friendshipHearts": 6,
        }
    )
    yield conversation

    # Cleanup after test
    await db.conversation.delete(where={"id": conversation.id})
