# Prompt: Technical Foundation for StardewEchoes

**Your Role:** You are a full-stack developer working on the "StardewEchoes" project.

**Context:** This document outlines the technical stack, key libraries, and repository structure for the project. Refer to this information to ensure your code, suggestions, and architectural decisions align with the project's established technologies and file organization.

---

## Technical Foundation

### Technologies and Tools

**1. Stardew Valley Mod (Client-side):**

- **Language:** C#
- **Framework:** .NET 6.0
- **Modding API:** SMAPI (Stardew Modding API)
- **Development Environment:** Visual Studio Code with C# extension
- **Key Libraries:** Pathoschild.Stardew.ModBuildConfig (for SMAPI/game references), System.Net.Http (for API calls).

**2. LLM API Server (Server-side):**

- **Language:** Python
- **Web Framework:** FastAPI (for building the RESTful API)
- **LLM Integration:** Official client libraries for chosen LLM (e.g., `openai` or `google-generativeai`).
- **Database:** (To be implemented) For persisting NPC memory/conversation history (e.g., SQLite for local development, PostgreSQL/MySQL for deployment).
- **Development Environment:** Visual Studio Code with Python extension.

### Repository Structure

The project is organized into two main top-level folders within the `LLM_STARDEW_VALLEY` repository:

- **`StardewEchoes/` (Stardew Valley Mod):**

  - This folder contains all the C# source code and project files (`.csproj`, `manifest.json`, `Class1.cs`, etc.) for the Stardew Valley mod itself. This is the "client" part that runs within the game.
  - **Purpose:** Detects in-game NPC interactions, gathers relevant game context, sends data to the `api` server, receives generated dialogue, and injects it into the game's dialogue system.

- **`api/` (LLM API Server):**

  - This folder will contain all the Python source code for the backend API server.
  - **Purpose:** Receives requests from the Stardew Valley mod, constructs prompts for the LLM based on game context and historical NPC memory, interacts with the LLM API, stores/retrieves conversation history from a database, and returns generated dialogues to the mod.

- **`.github/`:** (Not directly relevant to code, but noted for completeness) Contains GitHub Actions workflows for CI/CD or other repository automation.
