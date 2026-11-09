using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using StardewEchoes.Models;

namespace StardewEchoes.Handlers
{
  public class DialogueHandler
  {
    private readonly IMonitor Monitor;
    private readonly IModHelper Helper;
    private readonly HttpClient httpClient;
    private readonly Dictionary<string, List<ConversationEntry>> conversationHistories;
    private readonly GameContextHandler gameContextHandler;
    private NPC? npcWithPendingOptions;
    private DialogueResponse? pendingOptionsResponse;

    private const string API_URL = "http://127.0.0.1:8000/generate_dialogue";

    public DialogueHandler(
        IMonitor monitor,
        IModHelper helper,
        HttpClient httpClient,
        Dictionary<string, List<ConversationEntry>> conversationHistories,
        GameContextHandler gameContextHandler)
    {
      this.Monitor = monitor;
      this.Helper = helper;
      this.httpClient = httpClient;
      this.conversationHistories = conversationHistories;
      this.gameContextHandler = gameContextHandler;
    }

    // Main method that accepts GiftInfo directly (for GiftHandler)
    public async void AbrirDialogoConOpciones(NPC npc, string? playerResponse = null, GiftInfo? giftInfo = null)
    {
      try
      {
        var dialogueResponse = await GetDialogueFromAPI(npc, playerResponse, giftInfo);

        // Handle gift counter updates for successful gift processing (regardless of friendship change)
        if (giftInfo != null)
        {
          UpdateGiftCounters(npc);
          Monitor.Log($"🎁 Gift successfully processed: {giftInfo.item_name} given to {npc.Name}", LogLevel.Info);
        }

        // Apply friendship changes from both gifts and player responses
        if (dialogueResponse.friendship_change != 0)
        {
          int oldPoints = gameContextHandler.GetFriendshipPoints(npc.Name);
          int oldHearts = gameContextHandler.GetFriendshipHearts(npc.Name);
          
          Game1.player.changeFriendship(dialogueResponse.friendship_change, npc);
          
          int newPoints = gameContextHandler.GetFriendshipPoints(npc.Name);
          int newHearts = gameContextHandler.GetFriendshipHearts(npc.Name);

          string changeType;
          string reason;
          
          if (dialogueResponse.friendship_change > 0)
          {
            changeType = "INCREASED";
            if (giftInfo != null)
            {
              reason = $"{npc.Name} loved the {giftInfo.item_name} gift!";
            }
            else if (playerResponse != null)
            {
              reason = $"{npc.Name} liked your response: \"{playerResponse}\"";
            }
            else
            {
              reason = $"{npc.Name} appreciated the interaction";
            }
          }
          else
          {
            changeType = "DECREASED";
            if (giftInfo != null)
            {
              reason = $"{npc.Name} didn't like the {giftInfo.item_name} gift...";
            }
            else if (playerResponse != null)
            {
              reason = $"{npc.Name} didn't appreciate your response: \"{playerResponse}\"";
            }
            else
            {
              reason = $"{npc.Name} was displeased with the interaction";
            }
          }

          Monitor.Log($"=== FRIENDSHIP CHANGE ===", LogLevel.Info);
          Monitor.Log($"NPC: {npc.Name}", LogLevel.Info);
          if (giftInfo != null)
          {
            Monitor.Log($"Gift Given: {giftInfo.item_name} (Quality: {giftInfo.item_quality}, Preference: {giftInfo.gift_preference})", LogLevel.Info);
          }
          if (playerResponse != null)
          {
            Monitor.Log($"Player Response: \"{playerResponse}\"", LogLevel.Info);
          }
          Monitor.Log($"Friendship {changeType} by {Math.Abs(dialogueResponse.friendship_change)} points", LogLevel.Info);
          Monitor.Log($"Points: {oldPoints} → {newPoints} (Change: {dialogueResponse.friendship_change:+0;-0;0})", LogLevel.Info);
          Monitor.Log($"Hearts: {oldHearts} → {newHearts}", LogLevel.Info);
          Monitor.Log($"Reason: {reason}", LogLevel.Info);
          Monitor.Log($"========================", LogLevel.Info);
          
          // Show appropriate in-game messages
          if (newHearts > oldHearts)
          {
            Game1.drawObjectDialogue($"❤️ Your friendship with {npc.Name} increased to {newHearts} hearts!");
          }
          else if (newHearts < oldHearts)
          {
            Game1.drawObjectDialogue($"💔 Your friendship with {npc.Name} decreased to {newHearts} hearts...");
          }
          else if (dialogueResponse.friendship_change > 0)
          {
            if (giftInfo != null)
            {
              Game1.drawObjectDialogue($"😊 {npc.Name} liked the gift! (+{dialogueResponse.friendship_change} friendship)");
            }
            else
            {
              Game1.drawObjectDialogue($"😊 {npc.Name} liked that response! (+{dialogueResponse.friendship_change} friendship)");
            }
          }
          else if (dialogueResponse.friendship_change < 0)
          {
            if (giftInfo != null)
            {
              Game1.drawObjectDialogue($"😞 {npc.Name} didn't like the gift... ({dialogueResponse.friendship_change} friendship)");
            }
            else
            {
              Game1.drawObjectDialogue($"😞 {npc.Name} didn't like that response... ({dialogueResponse.friendship_change} friendship)");
            }
          }
        }

        AddToConversationHistory(npc.Name, "npc", dialogueResponse.npc_message);

        this.npcWithPendingOptions = npc;
        this.pendingOptionsResponse = dialogueResponse;

        ShowDialogue(npc, dialogueResponse.npc_message);
      }
      catch (Exception ex)
      {
        Monitor.Log($"Error al obtener diálogo: {ex.Message}", LogLevel.Error);

        Response[] opciones = new[]
        {
                    new Response("retry", gameContextHandler.GetLocalizedText("Try again")),
                    new Response("salir", gameContextHandler.GetLocalizedText("Exit"))
                };

        Game1.currentLocation.createQuestionDialogue(
            gameContextHandler.GetLocalizedText("Hello, how are you? (Connection error)"),
            opciones,
            (farmer, key) =>
            {
              if (key == "retry")
              {
                Helper.Events.GameLoop.UpdateTicked += RetryDialogue;

                void RetryDialogue(object? s, UpdateTickedEventArgs e)
                {
                  Helper.Events.GameLoop.UpdateTicked -= RetryDialogue;
                  AbrirDialogoConOpciones(npc);
                }
              }
            }
        );
      }
    }

    // Overload that accepts Item for backward compatibility
    public void AbrirDialogoConOpciones(NPC npc, string? playerResponse, Item giftItem)
    {
      var giftInfo = CreateGiftInfo(npc.Name, giftItem);
      AbrirDialogoConOpciones(npc, playerResponse, giftInfo);
    }

    public void OnMenuChanged(object? sender, MenuChangedEventArgs e)
    {
      if (e.OldMenu is DialogueBox dialogueBox &&
          this.npcWithPendingOptions != null &&
          dialogueBox.characterDialogue?.speaker == this.npcWithPendingOptions)
      {
        if (this.pendingOptionsResponse != null)
        {
          var npc = this.npcWithPendingOptions;
          var response = this.pendingOptionsResponse;

          this.npcWithPendingOptions = null;
          this.pendingOptionsResponse = null;

          ShowQuestionDialogue(npc, response);
        }
      }
    }

    private void ShowDialogue(NPC npc, string message)
    {
      npc.facePlayer(Game1.player);
      Game1.activeClickableMenu = new DialogueBox(new Dialogue(npc, "StardewEchoes", message));
    }

    private void ShowQuestionDialogue(NPC npc, DialogueResponse dialogueResponse)
    {
      var opciones = new List<Response>();
      for (int i = 0; i < dialogueResponse.response_options.Count && i < 3; i++)
      {
        opciones.Add(new Response($"option_{i}", dialogueResponse.response_options[i]));
      }
      opciones.Add(new Response("salir", gameContextHandler.GetLocalizedText("Exit")));

      Game1.currentLocation.createQuestionDialogue(
          "Choose an option to continue the conversation",
          opciones.ToArray(),
          (farmer, key) =>
          {
            if (key.StartsWith("option_"))
            {
              int optionIndex = int.Parse(key.Substring("option_".Length));
              string selectedResponse = dialogueResponse.response_options[optionIndex];
              AddToConversationHistory(npc.Name, "player", selectedResponse);

              Helper.Events.GameLoop.UpdateTicked += ContinueConversation;

              void ContinueConversation(object? s, UpdateTickedEventArgs e)
              {
                Helper.Events.GameLoop.UpdateTicked -= ContinueConversation;
                AbrirDialogoConOpciones(npc, selectedResponse);
              }
            }
            else if (key == "salir")
            {
              ClearConversationHistory(npc.Name);
              
              // Notify the API that the conversation has ended
              Helper.Events.GameLoop.UpdateTicked += EndConversationWithAPI;

              void EndConversationWithAPI(object? s, UpdateTickedEventArgs e)
              {
                Helper.Events.GameLoop.UpdateTicked -= EndConversationWithAPI;
                _ = Task.Run(async () =>
                {
                  try
                  {
                    var endRequest = new
                    {
                      player_name = Game1.player.Name,
                      npc_name = npc.Name
                    };

                    string jsonContent = JsonSerializer.Serialize(endRequest);
                    var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                    var response = await httpClient.PostAsync("http://127.0.0.1:8000/end_conversation", content);
                    
                    if (response.IsSuccessStatusCode)
                    {
                      Monitor.Log($"Successfully ended conversation with {npc.Name} - background analysis will be performed by the API.", LogLevel.Debug);
                    }
                    else
                    {
                      Monitor.Log($"Warning: Failed to notify API about conversation end with {npc.Name}: {response.StatusCode}", LogLevel.Warn);
                    }
                  }
                  catch (Exception ex)
                  {
                    Monitor.Log($"Error ending conversation with API: {ex.Message}", LogLevel.Error);
                  }
                });
              }
              
              Monitor.Log($"Conversación con {npc.Name} terminada. Historial limpiado.", LogLevel.Debug);
            }
          }
      );
    }

    private async Task<DialogueResponse> GetDialogueFromAPI(NPC npc, string? playerResponse = null, GiftInfo? giftInfo = null)
    {
      var history = GetConversationHistory(npc.Name);
      var request = new DialogueRequest
      {
        npc_name = npc.Name,
        npc_location = npc.currentLocation?.Name ?? "Unknown",
        player_name = Game1.player.Name,
        friendship_hearts = gameContextHandler.GetFriendshipHearts(npc.Name),
        season = Game1.currentSeason,
        day_of_month = Game1.dayOfMonth,
        day_of_week = (int)Game1.Date.DayOfWeek,
        time_of_day = Game1.timeOfDay,
        year = Game1.year,
        weather = gameContextHandler.GetCurrentWeather(),
        player_location = Game1.currentLocation?.Name ?? "Unknown",
        language = gameContextHandler.GetGameLanguage(),
        conversation_history = history,
        player_response = playerResponse,
        gift_given = giftInfo
      };

      string jsonContent = JsonSerializer.Serialize(request);
      var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

      Monitor.Log($"Enviando petición a la API para {npc.Name}", LogLevel.Debug);
      Monitor.Log($"Datos del contexto: {jsonContent}", LogLevel.Debug);

      var response = await httpClient.PostAsync(API_URL, content);

      if (response.IsSuccessStatusCode)
      {
        string responseText = await response.Content.ReadAsStringAsync();
        Monitor.Log($"Respuesta recibida: {responseText}", LogLevel.Debug);

        var dialogueResponse = JsonSerializer.Deserialize<DialogueResponse>(responseText);
        return dialogueResponse ?? new DialogueResponse
        {
          npc_message = gameContextHandler.GetLocalizedText("Hello, how are you?"),
          response_options = new List<string> {
                        gameContextHandler.GetLocalizedText("Friendly response"),
                        gameContextHandler.GetLocalizedText("Neutral response"),
                        gameContextHandler.GetLocalizedText("Provocative response")
                    }
        };
      }
      else
      {
        Monitor.Log($"Error en la API: {response.StatusCode}", LogLevel.Error);
        return new DialogueResponse
        {
          npc_message = gameContextHandler.GetLocalizedText("Hello, how are you? (Connection error)"),
          response_options = new List<string> {
                        gameContextHandler.GetLocalizedText("Friendly response"),
                        gameContextHandler.GetLocalizedText("Neutral response"),
                        gameContextHandler.GetLocalizedText("Provocative response")
                    }
        };
      }
    }

    private void AddToConversationHistory(string npcName, string speaker, string message)
    {
      if (!conversationHistories.ContainsKey(npcName))
      {
        conversationHistories[npcName] = new List<ConversationEntry>();
      }

      conversationHistories[npcName].Add(new ConversationEntry
      {
        speaker = speaker,
        message = message
      });

      if (conversationHistories[npcName].Count > 10)
      {
        conversationHistories[npcName].RemoveAt(0);
      }
    }

    private List<ConversationEntry> GetConversationHistory(string npcName)
    {
      return conversationHistories.ContainsKey(npcName)
          ? conversationHistories[npcName]
          : new List<ConversationEntry>();
    }

    private void ClearConversationHistory(string npcName)
    {
      if (conversationHistories.ContainsKey(npcName))
      {
        conversationHistories[npcName].Clear();
        conversationHistories.Remove(npcName);
      }
    }

    private GiftInfo CreateGiftInfo(string npcName, Item item)
    {
      // Get the NPC for birthday checking
      var npc = Game1.getCharacterFromName(npcName);
      bool isBirthday = false;
      
      if (npc != null)
      {
        // Check if it's the NPC's birthday
        try
        {
          isBirthday = npc.isBirthday();
        }
        catch (Exception ex)
        {
          Monitor.Log($"Error checking birthday for {npcName}: {ex.Message}", LogLevel.Warn);
        }
      }

      return new GiftInfo
      {
        item_name = item.Name,
        item_category = item.getCategoryName(),
        item_quality = item.Quality,
        gift_preference = "unknown", // Let AI decide (consistent with GiftHandler)
        is_birthday = isBirthday
      };
    }

    private void UpdateGiftCounters(NPC npc)
    {
      try
      {
        // Update friendship data using the correct Stardew Valley API
        if (Game1.player?.friendshipData != null)
        {
          var friendship = Game1.player.friendshipData.GetValueOrDefault(npc.Name);
          if (friendship == null)
          {
            friendship = new Friendship();
            Game1.player.friendshipData[npc.Name] = friendship;
          }

          friendship.GiftsToday++;
          friendship.GiftsThisWeek++;
          
          Monitor.Log($"📊 Updated gift counters for {npc.Name}: Today={friendship.GiftsToday}, Week={friendship.GiftsThisWeek}", LogLevel.Debug);
        }
        else
        {
          Monitor.Log($"⚠️ Could not access friendship data for {npc.Name}", LogLevel.Warn);
        }
      }
      catch (Exception ex)
      {
        Monitor.Log($"Error updating gift counters: {ex.Message}", LogLevel.Warn);
      }
    }
  }
}
