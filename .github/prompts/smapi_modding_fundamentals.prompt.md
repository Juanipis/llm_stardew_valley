# Prompt: Stardew Valley Modding Fundamentals

**Your Role:** You are a C# developer specializing in Stardew Valley modding with the SMAPI framework.

**Context:** This document provides a detailed guide on the fundamentals of SMAPI modding. It covers the mod lifecycle, project structure, the `manifest.json` file, and how to access core game functionality through the `IModHelper` interface. Use this as your primary reference for any questions related to the client-side C# mod's interaction with the game.

---

## Stardew Valley Modding Fundamentals (Client-Side)

This section covers the basics of how Stardew Valley mods work using SMAPI.

### How SMAPI Modding Works

1.  **SMAPI as a Mod Loader:**

    - Stardew Valley itself does not have a built-in modding API. SMAPI is a community-developed, open-source project that runs alongside the game.
    - When the player launches Stardew Valley via the SMAPI executable, SMAPI hooks into the game's process. It then scans the designated `Mods` folder for installed mods.
    - SMAPI dynamically loads and injects the compiled code of each mod into the running game instance, allowing mods to extend or alter game functionalities without modifying the original game files.

2.  **Mod Structure and Compilation:**

    - Stardew Valley mods, including "StardewEchoes," are primarily developed using **C#** (C Sharp) within the **.NET** framework (specifically .NET 6.0 for this project).
    - A mod is essentially a C# **Class Library** project. When this project is compiled (e.g., using `dotnet build` or Visual Studio/VS Code's build commands), it produces a **`.dll` (Dynamic Link Library) file**. This `.dll` contains all the mod's executable code.
    - The `Pathoschild.Stardew.ModBuildConfig` NuGet package is used to simplify the project setup, automatically adding necessary references to Stardew Valley's game assemblies and SMAPI's core libraries.

3.  **The `manifest.json` File:**

    - Every SMAPI mod requires a `manifest.json` file located in its root directory (alongside the compiled `.dll`).
    - This JSON file provides essential metadata about the mod, such as:
      - `Name`: The display name of the mod.
      - `Author`: The creator's name.
      - `Version`: The mod's version number.
      - `Description`: A brief overview of what the mod does.
      - `UniqueID`: A unique identifier (crucial for SMAPI and mod management, typically in `Author.ModName` format).
      - `Dependencies`: Specifies other mods required for this mod to function.

4.  **Mod Placement:**
    - Once compiled, the mod's folder (containing the `.dll`, `manifest.json`, and any other assets) is placed directly into the `Mods` directory within the Stardew Valley game installation folder (e.g., `Stardew Valley/Mods/StardewEchoes/`).

### Accessing Game Functionality via SMAPI (`IModHelper`)

The core of mod development in C# involves interacting with the game through SMAPI's provided interfaces and classes.

1.  **The `Mod` Class and `Entry()` Method:**

    - Every SMAPI mod must have a main class that inherits from `StardewModdingAPI.Mod`.
    - The `public override void Entry(IModHelper helper)` method is the mod's entry point. SMAPI calls this method when the mod is loaded.
    - The `IModHelper helper` parameter is the central access point to all SMAPI's functionalities.

2.  **Key SMAPI APIs accessible via `IModHelper`:**

    - **`helper.Events`:** Provides access to a wide range of game events. Mods subscribe to these events to react to specific actions or game states (e.g., `GameLoop.DayStarted`, `Input.ButtonPressed`, `Display.MenuChanged`, `Player.Warped`). This is the primary mechanism for interaction.
    - **`helper.GameContent`:** Allows reading and, crucially for this project, **editing** game content data, such as dialogue strings, textures, and map data. This will be vital for replacing default NPC dialogue with LLM-generated responses.
    - **`helper.Input`:** Manages player input (keyboard, mouse, controller). Can be used to detect interactions or custom keybindings.
    - **`helper.Reflection`:** An advanced API for accessing private or internal members (fields, properties, methods) of game classes that are not directly exposed by SMAPI. This is useful for manipulating game state in ways not covered by the public API.
    - **`helper.Monitor`:** Provides logging capabilities to the SMAPI console window. Essential for debugging, displaying information, and tracking mod behavior (`Monitor.Log("Message", LogLevel.Debug/Info/Error)`).
    - **`helper.Data`:** Enables saving and loading custom data specific to your mod within the save game file or a separate JSON file. This could be used for local caching or other persistent mod data if needed.
    - **`helper.ModRegistry`:** Allows querying information about other installed mods or interacting with them if they expose their own APIs.

3.  **Accessing Game Objects:**
    - **`Game1.player`:** Direct access to the current player object, including inventory, skills, relationships, location, etc.
    - **`Game1.currentLocation`:** Access to the current game location (e.g., `Farm`, `Town`).
    - **NPCs:** Non-Player Characters (NPCs) are instances of the `NPC` class. They can be accessed via `Game1.getCharacterFromName("NPCName")` or by iterating through collections like `Game1.currentLocation.characters`. Your mod will frequently interact with these objects to get their current state (e.g., `NPC.friendship`, `NPC.name`) and to manipulate their dialogue.

This understanding of SMAPI's role, the C# mod structure, and access to game elements via `IModHelper` will be foundational for developing "StardewEchoes."
