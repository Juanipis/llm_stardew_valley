# Prompt: Backend FastAPI Server Architecture

**Your Role:** You are a Python backend developer building the API server for the "StardewEchoes" project.

**Context:** This document provides instructions for setting up and building the backend server using FastAPI, Poetry, and Prisma. It covers project dependencies, database schema definition, project structure, and the main API endpoint for generating dialogue. Refer to this guide for all backend development tasks.

---

## Building the FastAPI Server with Prisma (Backend)

The backend is a crucial component responsible for receiving game context, managing long-term memory for NPCs, interacting with the LLM, and returning dynamic dialogue. It will be built with Python, FastAPI, and the Prisma ORM.

### 1. Project Setup and Dependencies (Poetry)

We will use Poetry to manage the project's dependencies and virtual environment.

**Dependencies:**
Add the necessary libraries using Poetry. This includes libraries for the web interface and advanced security.

```bash
# Core server framework
poetry add fastapi uvicorn

# For data validation and settings management
poetry add pydantic pydantic-settings

# For database interaction with Prisma
poetry add prisma
poetry add --group dev prisma

# For LLM interaction (example with OpenAI)
poetry add openai

# For handling .env files
poetry add python-dotenv

# --- New dependencies for Web UI and Auth ---
# For HTML templating
poetry add jinja2

# For password hashing
poetry add "passlib[bcrypt]"

# For handling JSON Web Tokens (JWT) for web sessions
poetry add "python-jose[cryptography]"
```

Your `api/pyproject.toml` should reflect these changes.

### 2. Prisma ORM Setup

**Step 1: Define the Schema**
Open `prisma/schema.prisma` and update the `User` model to support standard email/password authentication. The `api_token` will be generated on demand.

**`prisma/schema.prisma` (Updated):**

```prisma
generator client {
  provider = "prisma-client-py"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

// User model for web authentication and API access
model User {
  id              Int      @id @default(autoincrement())
  email           String   @unique
  hashed_password String
  api_token       String?  @unique // Storing the current API token, nullable
  worlds          World[]
}

// A specific save file/farm for a user
model World {
  id           Int           @id @default(autoincrement())
  farm_name    String
  user         User          @relation(fields: [userId], references: [id])
  userId       Int
  interactions Interaction[]

  @@unique([userId, farm_name])
}

// A single dialogue interaction
model Interaction {
  id                 Int      @id @default(autoincrement())
  npcName            String
  raw_context        String
  generated_dialogue String
  world              World    @relation(fields: [worldId], references: [id])
  worldId            Int
  createdAt          DateTime @default(now())
}
```

**Step 2: Migrate and Generate**
After updating the schema, run `prisma db push` and `prisma generate` again.

```bash
poetry run prisma db push
poetry run prisma generate
```

### 3. Recommended Directory Structure (Updated)

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, routers, and static file mounting
│   ├── db.py              # Prisma client instantiation
│   │   ├── config.py
│   │   └── security.py    # All auth logic (passwords, JWTs, API tokens)
│   ├── models/
│   │   └── request.py
│   └── routers/
│       ├── __init__.py
│       ├── dialogue.py    # API endpoint for the mod
│       └── web.py         # Routes for the web UI (login, dashboard)
├── templates/             # <-- NEW: For HTML templates
│   ├── login.html
│   └── dashboard.html
└── ... (other project files)
```

### 4. API Endpoint for Game Client (`/dialogue/generate`)

The logic for the game client's API endpoint remains largely the same, but the security dependency will be updated to reflect the new user schema.

**Authentication Dependency (`app/core/security.py`):**

```python
# ... (imports: Depends, HTTPException, status, HTTPBearer, db)
auth_scheme = HTTPBearer()

async def get_user_id_from_api_token(token: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API token",
    )
    api_token = token.credentials
    if not api_token:
        raise credentials_exception

    user = await db.user.find_unique(where={"api_token": api_token})
    if user is None:
        raise credentials_exception

    return user.id
```

**Dialogue Router (`app/routers/dialogue.py`):**
The `generate_dialogue` function should now use `Depends(get_user_id_from_api_token)` to authenticate requests from the game mod.
