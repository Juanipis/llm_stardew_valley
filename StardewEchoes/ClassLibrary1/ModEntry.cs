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

namespace StardewEchoes
{
    public class ConversationEntry
    {
        public string speaker { get; set; } = "";
        public string message { get; set; } = "";
    }

    public class DialogueRequest
    {
        public string npc_name { get; set; } = "";
        public string npc_location { get; set; } = "";
        public string player_name { get; set; } = "";
        public int friendship_hearts { get; set; }
        public string season { get; set; } = "";
        public int day_of_month { get; set; }
        public int day_of_week { get; set; }
        public int time_of_day { get; set; }
        public int year { get; set; }
        public string weather { get; set; } = "";
        public string player_location { get; set; } = "";
        public string language { get; set; } = "en";
        public List<ConversationEntry> conversation_history { get; set; } = new List<ConversationEntry>();
        public string? player_response { get; set; }
    }

    public class DialogueResponse
    {
        public string npc_message { get; set; } = "";
        public List<string> response_options { get; set; } = new List<string>();
    }

    public class ModEntry : Mod
    {
        private readonly HttpClient httpClient = new HttpClient();
        private const string API_URL = "http://127.0.0.1:8000/generate_dialogue";

        // Dictionary to store conversation history for each NPC
        private readonly Dictionary<string, List<ConversationEntry>> conversationHistories = new Dictionary<string, List<ConversationEntry>>();

        public override void Entry(IModHelper helper)
        {
            helper.Events.Input.ButtonPressed += OnButtonPressed;

            // Initialize HttpClient with timeout
            httpClient.Timeout = TimeSpan.FromSeconds(30);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                httpClient?.Dispose();
            }
            base.Dispose(disposing);
        }

        private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            if (e.Button.IsActionButton())
            {
                var tile = e.Cursor.GrabTile;
                var npc = Game1.currentLocation.isCharacterAtTile(tile);

                if (npc != null && npc.IsVillager)
                {
                    Game1.player.Halt();
                    Game1.player.faceGeneralDirection(npc.getStandingPosition());
                    AbrirDialogoConOpciones(npc);
                }
            }
        }

        private async void AbrirDialogoConOpciones(NPC npc, string? playerResponse = null)
        {
            try
            {
                // Get dialogue and options from API
                var dialogueResponse = await GetDialogueFromAPI(npc, playerResponse);

                // Add NPC response to conversation history
                AddToConversationHistory(npc.Name, "npc", dialogueResponse.npc_message);

                // Create response options from API response
                var opciones = new List<Response>();
                for (int i = 0; i < dialogueResponse.response_options.Count && i < 3; i++)
                {
                    opciones.Add(new Response($"option_{i}", dialogueResponse.response_options[i]));
                }

                // Add exit option
                opciones.Add(new Response("salir", GetLocalizedText("Exit")));

                Game1.currentLocation.createQuestionDialogue(
                    dialogueResponse.npc_message,
                    opciones.ToArray(),
                    (farmer, key) =>
                    {
                        if (key.StartsWith("option_"))
                        {
                            // Get the selected option text
                            int optionIndex = int.Parse(key.Substring("option_".Length));
                            string selectedResponse = dialogueResponse.response_options[optionIndex];

                            // Add player response to conversation history
                            AddToConversationHistory(npc.Name, "player", selectedResponse);

                            // Continue conversation with the selected response
                            this.Helper.Events.GameLoop.UpdateTicked += ContinueConversation;

                            void ContinueConversation(object? s, UpdateTickedEventArgs e)
                            {
                                this.Helper.Events.GameLoop.UpdateTicked -= ContinueConversation;
                                AbrirDialogoConOpciones(npc, selectedResponse);
                            }
                        }
                        else if (key == "salir")
                        {
                            // Clear conversation history when exiting
                            ClearConversationHistory(npc.Name);
                            this.Monitor.Log($"Conversación con {npc.Name} terminada. Historial limpiado.", LogLevel.Debug);
                        }
                    }
                );
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"Error al obtener diálogo: {ex.Message}", LogLevel.Error);

                // Fallback to simple dialogue
                Response[] opciones = new[]
                {
                    new Response("retry", GetLocalizedText("Try again")),
                    new Response("salir", GetLocalizedText("Exit"))
                };

                Game1.currentLocation.createQuestionDialogue(
                    GetLocalizedText("Hello, how are you? (Connection error)"),
                    opciones,
                    (farmer, key) =>
                    {
                        if (key == "retry")
                        {
                            this.Helper.Events.GameLoop.UpdateTicked += RetryDialogue;

                            void RetryDialogue(object? s, UpdateTickedEventArgs e)
                            {
                                this.Helper.Events.GameLoop.UpdateTicked -= RetryDialogue;
                                AbrirDialogoConOpciones(npc);
                            }
                        }
                        else if (key == "salir")
                        {
                            // Clear conversation history when exiting
                            ClearConversationHistory(npc.Name);
                            this.Monitor.Log($"Conversación con {npc.Name} terminada. Historial limpiado.", LogLevel.Debug);
                        }
                    }
                );
            }
        }

        private async Task<DialogueResponse> GetDialogueFromAPI(NPC npc, string? playerResponse = null)
        {
            // Get conversation history for this NPC
            var history = GetConversationHistory(npc.Name);

            // Gather game context data
            var request = new DialogueRequest
            {
                npc_name = npc.Name,
                npc_location = npc.currentLocation?.Name ?? "Unknown",
                player_name = Game1.player.Name,
                friendship_hearts = GetFriendshipHearts(npc.Name),
                season = Game1.currentSeason,
                day_of_month = Game1.dayOfMonth,
                day_of_week = (int)Game1.Date.DayOfWeek,
                time_of_day = Game1.timeOfDay,
                year = Game1.year,
                weather = GetCurrentWeather(),
                player_location = Game1.currentLocation?.Name ?? "Unknown",
                language = GetGameLanguage(),
                conversation_history = history,
                player_response = playerResponse
            };

            // Serialize request to JSON
            string jsonContent = JsonSerializer.Serialize(request);
            var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

            this.Monitor.Log($"Enviando petición a la API para {npc.Name}", LogLevel.Debug);
            this.Monitor.Log($"Datos del contexto: {jsonContent}", LogLevel.Debug);

            // Make HTTP request
            var response = await httpClient.PostAsync(API_URL, content);

            if (response.IsSuccessStatusCode)
            {
                string responseText = await response.Content.ReadAsStringAsync();
                this.Monitor.Log($"Respuesta recibida: {responseText}", LogLevel.Debug);

                var dialogueResponse = JsonSerializer.Deserialize<DialogueResponse>(responseText);
                return dialogueResponse ?? new DialogueResponse
                {
                    npc_message = GetLocalizedText("Hello, how are you?"),
                    response_options = new List<string> {
                        GetLocalizedText("Friendly response"),
                        GetLocalizedText("Neutral response"),
                        GetLocalizedText("Provocative response")
                    }
                };
            }
            else
            {
                this.Monitor.Log($"Error en la API: {response.StatusCode}", LogLevel.Error);
                return new DialogueResponse
                {
                    npc_message = GetLocalizedText("Hello, how are you? (Connection error)"),
                    response_options = new List<string> {
                        GetLocalizedText("Friendly response"),
                        GetLocalizedText("Neutral response"),
                        GetLocalizedText("Provocative response")
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

            // Keep only last 10 messages to avoid too much context
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

        private string GetGameLanguage()
        {
            // Detect game language based on Stardew Valley's language settings
            var languageCode = LocalizedContentManager.CurrentLanguageCode;

            return languageCode switch
            {
                LocalizedContentManager.LanguageCode.es => "es",
                LocalizedContentManager.LanguageCode.fr => "fr",
                LocalizedContentManager.LanguageCode.de => "de",
                LocalizedContentManager.LanguageCode.it => "it",
                LocalizedContentManager.LanguageCode.pt => "pt",
                LocalizedContentManager.LanguageCode.ru => "ru",
                LocalizedContentManager.LanguageCode.ja => "ja",
                LocalizedContentManager.LanguageCode.zh => "zh",
                LocalizedContentManager.LanguageCode.ko => "ko",
                _ => "en" // Default to English
            };
        }

        private string GetLocalizedText(string englishText)
        {
            // Simple localization - in a real implementation, you'd use proper localization
            var language = GetGameLanguage();

            return (language, englishText) switch
            {
                ("es", "Exit") => "Salir",
                ("es", "Try again") => "Intentar de nuevo",
                ("es", "Hello, how are you?") => "Hola, ¿cómo estás?",
                ("es", "Hello, how are you? (Connection error)") => "Hola, ¿cómo estás? (Error de conexión)",
                ("es", "Friendly response") => "¡Me da mucho gusto verte!",
                ("es", "Neutral response") => "¿Hay algo importante que deba saber?",
                ("es", "Provocative response") => "¿Siempre tienes esa cara o es solo hoy?",
                _ => englishText switch
                {
                    "Friendly response" => "It's great to see you!",
                    "Neutral response" => "Is there anything important I should know?",
                    "Provocative response" => "Do you always look like that or is it just today?",
                    _ => englishText // Default to original English text
                }
            };
        }

        private int GetFriendshipHearts(string npcName)
        {
            if (Game1.player.friendshipData.ContainsKey(npcName))
            {
                int points = Game1.player.friendshipData[npcName].Points;
                // Convert friendship points to hearts (250 points = 1 heart)
                return points / 250;
            }
            return 0;
        }

        private string GetCurrentWeather()
        {
            if (Game1.isRaining)
            {
                if (Game1.isLightning)
                    return "Storm";
                else
                    return "Rain";
            }
            else if (Game1.isSnowing)
                return "Snow";
            else if (Game1.isDebrisWeather)
                return "Wind";
            else
                return "Sun";
        }

    }
}
