# StardewEchoes - Stardew Valley Dynamic Dialogue Mod

This file provides a high-level overview of the "StardewEchoes" project. For detailed information on specific components, please refer to the prompt files located in the `.github/prompts/` directory.

## Project Vision & Architecture

The core goal of this project is to create a Stardew Valley mod that uses a Large Language Model (LLM) to generate dynamic NPC dialogues. It consists of two main parts: a C# mod (the client) and a Python FastAPI server (the backend).

- For a detailed **Project Overview**, see `#file:./prompts/project_overview.prompt.md`
- For the **Technical Stack and Repository Structure**, see `#file:./prompts/technical_stack.prompt.md`

## Client-Side (C# Stardew Valley Mod)

The client is a C# mod using SMAPI. It is responsible for intercepting player-NPC interactions, gathering game context, calling the backend API, and displaying the generated dialogue in-game.

- For **SMAPI Modding Fundamentals**, see `#file:./prompts/smapi_modding_fundamentals.prompt.md`
- For the **Dynamic Dialogue Logic**, including interaction interception and context gathering, see `#file:./prompts/client_dialogue_logic.prompt.md`
- For details on **API Communication and Configuration**, see `#file:./prompts/client_server_communication.prompt.md`

## Server-Side (Python FastAPI Backend)

The backend is a Python server built with FastAPI. It handles requests from the mod, interacts with the LLM, manages conversation history in a database, and provides a web interface for user authentication and API token management.

- For the **FastAPI Server and Database Setup**, see `#file:./prompts/backend_fastapi_server.prompt.md`
- For the **Web UI and Authentication Logic**, see `#file:./prompts/backend_web_auth.prompt.md`

## Character Context

To ensure dialogues are in-character, refer to the character personalities prompt file.

- For **NPC Personalities**, see `#file:./prompts/character_personalities.prompt.md`
