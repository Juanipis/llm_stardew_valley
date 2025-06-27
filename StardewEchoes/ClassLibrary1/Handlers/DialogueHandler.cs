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

    public async void AbrirDialogoConOpciones(NPC npc, string? playerResponse = null)
    {
      try
      {
        var dialogueResponse = await GetDialogueFromAPI(npc, playerResponse);

        if (playerResponse != null && dialogueResponse.friendship_change != 0)
        {
          int oldPoints = gameContextHandler.GetFriendshipPoints(npc.Name);
          Game1.player.changeFriendship(dialogueResponse.friendship_change, npc);
          int newPoints = gameContextHandler.GetFriendshipPoints(npc.Name);

          if (dialogueResponse.friendship_change > 0)
          {
            Monitor.Log($"{npc.Name}'s friendship increased by {dialogueResponse.friendship_change} points. (From {oldPoints} to {newPoints})", LogLevel.Info);
          }
          else
          {
            Monitor.Log($"{npc.Name}'s friendship decreased by {-dialogueResponse.friendship_change} points. (From {oldPoints} to {newPoints})", LogLevel.Info);
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
              Monitor.Log($"Conversación con {npc.Name} terminada. Historial limpiado.", LogLevel.Debug);
            }
          }
      );
    }

    private async Task<DialogueResponse> GetDialogueFromAPI(NPC npc, string? playerResponse = null)
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
        player_response = playerResponse
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
  }
}
