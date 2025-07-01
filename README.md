# StardewEchoes - Dynamic Dialogue Mod

This is a project of a Stardew Valley mod using SMAPI as a base to create a mod that uses an LLM to generate dynamic dialogues with **persistent memory and adaptive personality system**.

The LLM is hosted on a FastAPI server and the mod communicates with it to get contextual dialogues that evolve based on player interactions.

## 🚀 Quick Start

### Building the Mod

```bash
dotnet build /p:GamePath="D:\Cracked\Stardew Valley"
```

### Setting up the API Server

1. **Configure PostgreSQL with pgvector:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Setup API environment:**

```bash
cd api
cp .env.example .env
# Edit .env with your credentials
python setup.py
```

3. **Verify database connection:**

```bash
python verify_db.py
```

4. **Start the server:**

```bash
poetry run uvicorn app.main:app --reload
```

## 🧠 Core Features

- **Adaptive Personality Profiles**: NPCs form unique, evolving opinions of each player based on their interactions.
- **Dynamic Emotional States**: NPCs have moods that change based on dialogue, events, and context, influencing their behavior.
- **Local, Semantic Memory Search**: NPCs recall past conversations using a purely local `sentence-transformers` model (`all-mpnet-base-v2`) to generate 768-dimension vector embeddings. This allows for nuanced, context-aware memory recall without external API calls.
- **Persistent Conversation History**: All dialogues are saved with rich context (time, season, location) for long-term memory.

See the [API README](api/README.md) for more technical details.

## 🎮 In-Game Debug Commands

Use these commands in the SMAPI console to interact with the system:

- `debug wctm [npc_name]`: **W**hat's **C**urrently **T**he **M**atter with `[npc_name]`?

  - Dumps the NPC's current emotional state and personality perception of the player to the console.

- `debug forget [npc_name]`:
  - Resets the memory and relationship between the player and `[npc_name]`.

## 📈 Monitoring Dashboard

The API includes a real-time monitoring dashboard to observe NPC states and conversations. Access it at `http://localhost:8000/monitoring/`.

Debug wctm Clint