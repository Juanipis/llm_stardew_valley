# Prompt: Client-Server Communication

**Your Role:** You are a C# developer responsible for the networking and configuration aspects of the "StardewEchoes" client mod.

**Context:** This document outlines the process for client-to-server communication. It covers how to make asynchronous HTTP requests from the C# mod to the backend API, how to manage secrets like API keys, and how to integrate with the Generic Mod Config Menu (GMCM) for user-facing configuration.

---

## Client-Side to Server-Side Communication: Calling the API

The "StardewEchoes" mod's core functionality relies on seamless communication with the external Python API server. This involves making HTTP requests from the C# mod to the API, sending game context, and receiving the LLM-generated dialogue.

### 1. Making HTTP Requests (C# `HttpClient`)

- **Mechanism:** The C# mod will use the `System.Net.Http.HttpClient` class to send asynchronous HTTP POST requests to the API server. This client is standard in .NET for web communication.
- **Payload:** The request body will be a JSON object containing all the relevant game context gathered (NPC name, player friendship, time, weather, location, etc.). This JSON will be serialized from C# objects.
- **Response:** The API is expected to return a JSON response containing the generated dialogue string, which the mod will then deserialize and inject into the game.
- **Asynchronous Operations (`async/await`):** It is absolutely crucial that all API calls are performed **asynchronously** using `async` and `await` keywords. This prevents the game from freezing or becoming unresponsive while waiting for the API's response (which can take a few seconds, especially due to LLM processing).

**Conceptual Code Snippet (within `LLMDialogueMod.cs`):**

```csharp
using System.Net.Http;
using System.Text;
using System.Threading.Tasks; // Required for async/await
using Newtonsoft.Json; // Recommended for JSON serialization/deserialization

// ... inside your LLMDialogueMod class ...

private static readonly HttpClient _httpClient = new HttpClient(); // HttpClient should be static and reused

/// <summary>
/// Makes an asynchronous call to the external API to get LLM-generated dialogue.
/// </summary>
/// <param name="npc">The NPC being interacted with.</param>
/// <param name="gameContext">A dictionary or object containing all relevant game state.</param>
/// <returns>The generated dialogue string, or a fallback message if the API call fails.</returns>
private async Task<string> GetDialogueFromApiAsync(NPC npc, Dictionary<string, object> gameContext)
{
    // Retrieve configured API URL and Token (from mod settings)
    ModConfig config = Helper.ReadConfig<ModConfig>(); // Assume ModConfig holds these settings
    if (string.IsNullOrWhiteSpace(config.ApiUrl))
    {
        Monitor.Log("API URL is not configured. Cannot get LLM dialogue.", LogLevel.Error);
        return $"Hello, {Game1.player.Name}. (API not configured)";
    }

    try
    {
        // Add authentication token to request headers (e.g., Bearer token)
        _httpClient.DefaultRequestHeaders.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", config.ApiToken);

        // Prepare the JSON payload
        string jsonPayload = JsonConvert.SerializeObject(gameContext);
        StringContent content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

        // Make the POST request to the API
        HttpResponseMessage response = await _httpClient.PostAsync(config.ApiUrl + "/dialogue/generate", content);
        response.EnsureSuccessStatusCode(); // Throws an exception if not a 2xx status code

        // Read the response content
        string responseBody = await response.Content.ReadAsStringAsync();

        // Deserialize the response (assuming it's JSON like { "dialogue": "..." })
        dynamic apiResponse = JsonConvert.DeserializeObject(responseBody);
        return apiResponse.dialogue;
    }
    catch (HttpRequestException ex)
    {
        Monitor.Log($"API request failed: {ex.Message}. Check if the server is running and URL is correct.", LogLevel.Error);
        return $"Sorry, {Game1.player.Name}. I'm having trouble connecting to my brain right now. (API Error)";
    }
    catch (JsonException ex)
    {
        Monitor.Log($"Failed to parse API response: {ex.Message}.", LogLevel.Error);
        return "Hmm, that didn't make sense. (Dialogue parse error)";
    }
    catch (Exception ex)
    {
        Monitor.Log($"An unexpected error occurred during API call: {ex.Message}", LogLevel.Error);
        return $"An unexpected glitch occurred! (Internal mod error)";
    }
}
```

### 2. Mod Configuration UI and Secret Management

Since the API URL and an authentication token are external secrets that vary per user/setup, the mod needs a way for players to configure them.

**Requirement: In-Game Configuration UI**

The mod will require a user interface for players to configure it. SMAPI has built-in support for integrating with a UI mod called **Generic Mod Config Menu (GMCM)**. Instead of building a custom UI from scratch, the mod will declare GMCM as a dependency and use its API to create a configuration page.

**Implementing GMCM Integration:**

1.  **Add GMCM as a Dependency:** In the `manifest.json`, add a dependency entry for GMCM. This ensures SMAPI will notify the user if GMCM is not installed.
2.  **Use the GMCM API:** Within the mod's `Entry` method, after the game has loaded, check if the GMCM API is available. If it is, register your mod's config class and define the options you want to show.

**Conceptual Code Snippet (in `Entry` method):**

```csharp
// At the top of your file
using StardewModdingAPI.Utilities; // For SButton

// Inside Entry method, after subscribing to events
helper.Events.GameLoop.GameLaunched += (s, e) =>
{
    // Get a reference to the Generic Mod Config Menu API
    var configMenu = this.Helper.ModRegistry.GetApi<IGenericModConfigMenuApi>("spacechase0.GenericModConfigMenu");
    if (configMenu is null) return;

    // Register our mod with GMCM
    configMenu.Register(
        mod: this.ModManifest,
        reset: () => this.Config = new ModConfig(),
        save: () => this.Helper.WriteConfig(this.Config)
    );

    // Add options to the menu
    configMenu.AddSectionTitle(
        mod: this.ModManifest,
        text: () => "API Settings"
    );
    configMenu.AddTextOption(
        mod: this.ModManifest,
        name: () => "API URL",
        tooltip: () => "The URL of the LLM API server.",
        getValue: () => this.Config.ApiUrl,
        setValue: value => this.Config.ApiUrl = value
    );
    configMenu.AddTextOption(
        mod: this.ModManifest,
        name: () => "API Token",
        tooltip: () => "The Bearer token for authenticating with the API.",
        getValue: () => this.Config.ApiToken,
        setValue: value => this.Config.ApiToken = value
    );
};
```

**Storing Configuration Secrets:**

- **Global Mod Configuration:** For settings like API URLs and tokens that apply across all save games, SMAPI provides `Helper.ReadConfig<T>` and `Helper.WriteConfig<T>`. You will define a simple C# class (e.g., `ModConfig`) to hold these settings. SMAPI automatically handles saving/loading this `ModConfig` class to/from a `config.json` file within your mod's folder (`Stardew Valley/Mods/StardewEchoes/config.json`). This keeps the secrets local to the player's installation.

**`ModConfig.cs` (new file):**

```csharp
// StardewEchoes/ModConfig.cs
public class ModConfig
{
    public string ApiUrl { get; set; } = "http://localhost:8000"; // Default URL for local testing
    public string ApiToken { get; set; } = ""; // Default empty token
}
```

- **Security Considerations:**
  - The `ApiToken` should never be hardcoded in the mod's source code.
  - Storing it in `config.json` on the user's machine is standard for mods. This file is local and not publicly exposed unless the user shares their entire mod folder.
  - The server-side API should enforce authentication (e.g., Bearer tokens) to prevent unauthorized access.
