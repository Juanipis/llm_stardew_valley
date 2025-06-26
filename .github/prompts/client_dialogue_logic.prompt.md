# Prompt: Client-Side Dynamic Dialogue Logic

**Your Role:** You are a C# developer implementing the core gameplay features of the "StardewEchoes" mod.

**Context:** This document details the implementation of the dynamic dialogue logic on the client-side. It explains how to intercept NPC interactions, gather in-game context (like player relationships, time, and weather), and display custom dialogue. This is a critical guide for understanding how the mod hooks into the game to override default behavior.

---

## Implementing the Dynamic Dialogue Logic

This section details the step-by-step process for implementing the core features of the mod. The primary challenge on the client-side will be detecting the precise moment an NPC's dialogue is about to be displayed and intercepting it to replace with the LLM-generated text from the `api` server.

### Step 1: Intercepting NPC Interaction

The most common way to detect player interaction with an NPC in Stardew Valley is by listening for input events, checking if the player is targeting an NPC, and then suppressing the default dialogue.

- **Subscribing to Input Events:** We'll use `helper.Events.Input.ButtonPressed` to listen for player input. The common interaction button for talking is the right-click (`SButton.MouseRight`) or the 'A' button on a controller (`SButton.ControllerA`).

- **Identifying the Interacted NPC:** When an interaction button is pressed, we need to determine if the player is currently facing an NPC and if that NPC is the target of the interaction.

- **Suppressing Default Dialogue:** By calling `helper.Input.Suppress(e.Button)`, we tell SMAPI to prevent the game from processing that specific button press, thus stopping the default dialogue from triggering.

**Example Code (within `StardewEchoes/LLMDialogueMod.cs`):**

```csharp
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley; // Provides access to Game1, NPC, etc.
using StardewValley.Characters; // Specific NPC types

namespace StardewEchoes
{
    public class LLMDialogueMod : Mod
    {
        private IMonitor Monitor;

        public override void Entry(IModHelper helper)
        {
            this.Monitor = helper.Monitor;
            Monitor.Log("StardewEchoes Mod loaded.", LogLevel.Debug);

            // Subscribe to the button pressed event to detect player interaction.
            // This event fires *before* the game processes the input, allowing us to
            // potentially intercept it.
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
        }

        /// <summary>Handles the ButtonPressed event.</summary>
        /// <param name="sender">The event sender.</param>
        /// <param name="e">The event data.</param>
        private void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            // Ensure the game world is loaded and the player is not in a menu.
            if (!Context.IsWorldReady || !Context.IsPlayerFree)
            {
                return;
            }

            // Check if the interaction button (right-click or 'A' on controller) was pressed.
            if (e.Button == SButton.MouseRight || e.Button == SButton.ControllerA)
            {
                // Get the tile the player is facing.
                Microsoft.Xna.Framework.Point tile = e.Cursor.GrabTile;

                // Check for an NPC at the targeted tile.
                // Iterating through current location characters is a common way.
                NPC interactedNpc = null;
                foreach (NPC npc in Game1.currentLocation.characters)
                {
                    // A simple check if the NPC's collision bounding box contains the target tile:
                    if (npc.GetBoundingBox().Contains(e.Cursor.GetWorldCoordinates()) &&
                        Vector2.Distance(Game1.player.Position, npc.Position) < 128f) // within range
                    {
                         interactedNpc = npc;
                         break;
                    }
                }

                if (interactedNpc != null)
                {
                    Monitor.Log($"Player interacted with {interactedNpc.Name}.", LogLevel.Debug);

                    // Suppress the default game action for this interaction.
                    // This is crucial to prevent the default dialogue from appearing.
                    this.Helper.Input.Suppress(e.Button);

                    // Now, trigger our custom dialogue logic.
                    this.SetCustomNpcDialogue(interactedNpc);
                }
            }
        }

        /// <summary>Sets a custom dialogue for the given NPC.</summary>
        /// <param name="npc">The NPC to set dialogue for.</param>
        private void SetCustomNpcDialogue(NPC npc)
        {
            string customDialogue = $"Hello, {Game1.player.Name}! My name is {npc.Name}. This is a custom dialogue!";

            // In the future, this is where the call to the external API would go,
            // and the 'customDialogue' string would be replaced by the LLM's response.

            // The preferred way to show dialogue is to create a Dialogue object
            // and set it on the NPC, then tell the game to show it.
            // This ensures it uses the game's proper dialogue box and speech bubble system.
            Dialogue dialogue = new Dialogue(customDialogue, npc);
            npc.CurrentDialogue.Clear(); // Clear any existing dialogue
            npc.CurrentDialogue.Push(dialogue); // Add our custom dialogue

            // Set the game state to show the dialogue
            Game1.currentSpeaker = npc;
            Game1.dialogueUp = true;
            Game1.player.CanMove = false; // Prevent player movement during dialogue

            Monitor.Log($"Displayed custom dialogue for {npc.Name}: '{customDialogue}'", LogLevel.Info);
        }
    }
}
```

### Step 2: Gathering Context for the LLM Prompt

All the data points gathered here will form the core of the "context" payload sent to the external API.

#### Character (NPC) Information

- **Accessing NPCs:** All characters in the current location are typically available via `Game1.currentLocation.characters`. You can also retrieve specific NPCs by name using `Game1.getCharacterFromName("NPCName")`.
- **NPC Properties:**
  - **Name:** `npc.Name` (e.g., "Shane", "Abigail"). Essential for identifying who is speaking.
  - **Current Location:** `npc.currentLocation.Name` (e.g., "Saloon", "Farm").
  - **Current Schedule/Activity:** `npc.currentLocation.Name` and `Game1.timeOfDay` usually provide enough context.
  - **Facing Direction:** `npc.FacingDirection` (0: Up, 1: Right, 2: Down, 3: Left).

#### Player-NPC Relationships (Friendship)

- **Accessing Friendship Data:** The player's friendship with NPCs is stored in `Game1.player.friendshipData`. This is a `Dictionary<string, Friendship>` where the key is the NPC's name.
- **Friendship Properties:**
  - **Points:** `Game1.player.friendshipData[npc.Name].Points` (raw friendship points).
  - **Hearts:** `Game1.player.friendshipData[npc.Name].Points / 250` (each heart is 250 points).

#### Time and Date Information

- **Current Season:** `Game1.currentSeason` (e.g., "spring", "summer").
- **Current Day of Season:** `Game1.dayOfMonth` (1-28).
- **Current Day of Week:** `new WorldDate(Game1.year, Game1.currentSeason, Game1.dayOfMonth).DayOfWeek`.
- **Current Time of Day:** `Game1.timeOfDay` (minutes past midnight, e.g., `610` for 6:10 AM).
- **Current Year:** `Game1.year`.

#### Environmental and Global Game State

- **Current Weather:** `Game1.isRaining`, `Game1.isSnowing`, `Game1.isLightning` are boolean flags.
- **Current Player Location:** `Game1.currentLocation.Name` (e.g., "Farm", "Town").
- **Active Events/Quests:** `Game1.player.questLog` contains active quests. For festivals, check `Game1.isFestival()`.

#### Significance for LLM Prompting

A well-crafted prompt for the LLM might look something like this (conceptual example):

> "You are [NPC Name] from Stardew Valley. It is [TimeOfDay] on [DayOfWeek], Day [DayOfMonth] of [Season], Year [Year]. The weather is [WeatherDescription]. You are currently in [NPCLocation]. You have [FriendshipHearts] hearts with the player, [PlayerName]. Based on this, generate a single, in-character line of dialogue for [NPC Name] to say."

### Step 3: Displaying Custom Dialogue in Game

Once the default interaction is suppressed (and in the future, a dialogue is received from the API), we must manually tell the game to display our custom string.

- **Manually Trigger Custom Dialogue:** Manipulating the `NPC.CurrentDialogue` stack and setting game state flags like `Game1.currentSpeaker` and `Game1.dialogueUp` is the most robust method for integrating seamlessly with the game's UI. This ensures the proper dialogue box and speech bubble are used. The `SetCustomNpcDialogue` method in the code example above demonstrates this logic.

This setup provides the necessary hooks on the client-side to take control of NPC conversations. The `SetCustomNpcDialogue` method is currently using a hardcoded string, but it's designed to be the place where the dynamic LLM response will eventually be injected after a successful API call.
