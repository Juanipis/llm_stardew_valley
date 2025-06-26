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

## 🧠 Memory System Features

- **Adaptive Personality Profiles**: Each NPC develops unique perceptions of each player
- **Semantic Memory Search**: NPCs remember and reference relevant past conversations
- **Dynamic Relationship Evolution**: Interactions shape how NPCs respond over time
- **Persistent Conversation History**: All dialogues are saved with context

See [API Memory System Documentation](api/MEMORY_SYSTEM.md) for detailed information.

## 🎮 Debug Commands

```
debug wctm lewis
```
