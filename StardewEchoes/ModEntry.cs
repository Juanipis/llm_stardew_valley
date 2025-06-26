using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Characters;
using StardewValley.Menus;
using Microsoft.Xna.Framework;
using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace StardewEchoes
{
    internal sealed class ModEntry : Mod
    {
        private static readonly string TargetNpcName = "Lewis";
        private static readonly string ApiUrl = "http://localhost:8000/generate_dialogue";
        private readonly HttpClient httpClient;
        private bool isRequestInProgress;

        public ModEntry()
        {
            var handler = new HttpClientHandler();
            handler.ServerCertificateCustomValidationCallback = (message, cert, chain, errors) => true;
            this.httpClient = new HttpClient(handler);
            this.httpClient.Timeout = TimeSpan.FromSeconds(10);
        }

        public override void Entry(IModHelper helper)
        {
            this.Monitor.Log("StardewEchoes Mod loaded.", LogLevel.Info);
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.Display.MenuChanged += this.OnMenuChanged;
            helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
        }

        private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
        {
            this.isRequestInProgress = false;
        }

        private void OnMenuChanged(object? sender, MenuChangedEventArgs e)
        {
            // Monitor dialogue display and handle any errors
            if (e.NewMenu is DialogueBox dialogueBox && dialogueBox.characterDialogue?.speaker?.Name == TargetNpcName)
            {
                this.Monitor.Log($"Dialogue shown for {TargetNpcName}: {dialogueBox.characterDialogue.getCurrentDialogue()}", LogLevel.Trace);
                
                // Reset request flag when dialogue closes
                if (e.OldMenu is DialogueBox && e.NewMenu == null)
                {
                    this.isRequestInProgress = false;
                }
            }
        }

        private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
        {
            if (!Context.IsWorldReady || !Context.IsPlayerFree || this.isRequestInProgress)
                return;

            // Only allow on play days (not festivals/events)
            if (Game1.CurrentEvent != null || Game1.isFestival())
                return;

            if (e.Button == SButton.MouseRight || e.Button == SButton.ControllerA)
            {
                var tile = e.Cursor.Tile;
                NPC? interactedNpc = null;
                foreach (NPC npc in Game1.currentLocation.characters)
                {
                    var npcTile = new Point((int)npc.Tile.X, (int)npc.Tile.Y);
                    if (npc.Name == TargetNpcName && npcTile.Equals(tile) &&
                        Vector2.Distance(Game1.player.Position, npc.Position) < 128f)
                    {
                        interactedNpc = npc;
                        break;
                    }
                }

                if (interactedNpc is not null)
                {
                    this.isRequestInProgress = true;
                    if (Game1.player.friendshipData.ContainsKey(interactedNpc.Name))
                    {
                        Game1.player.friendshipData[interactedNpc.Name].TalkedToToday = false;
                    }
                    this.Monitor.Log($"Player interacted with {interactedNpc.Name}. Fetching dialogue...", LogLevel.Info);
                    this.Helper.Input.Suppress(e.Button);
                    _ = this.SetLewisDialogueAsync(interactedNpc);
                }
            }
        }

        private async Task SetLewisDialogueAsync(NPC npc)
        {
            string contextJson = this.GatherLewisContext(npc);
            this.Monitor.Log($"Gathered context for {npc.Name}: {contextJson}", LogLevel.Debug);
            
            try
            {
                var content = new StringContent(contextJson, System.Text.Encoding.UTF8, "application/json");
                var response = await this.httpClient.PostAsync(ApiUrl, content);
                response.EnsureSuccessStatusCode();
                var responseContent = await response.Content.ReadAsStringAsync();

                if (string.IsNullOrWhiteSpace(responseContent))
                {
                    this.ShowFallbackDialogue(npc, "API returned empty dialogue.");
                    return;
                }

                var dialogueText = JsonSerializer.Deserialize<string>(responseContent);
                if (dialogueText == null)
                {
                    this.ShowFallbackDialogue(npc, "API returned invalid dialogue.");
                    return;
                }

                // Create a dialogue sequence with emotion
                var dialogue = this.CreateDialogueSequence(npc, dialogueText);
                
                // Set up the dialogue display
                npc.CurrentDialogue.Clear();
                npc.CurrentDialogue.Push(dialogue);
                Game1.currentSpeaker = npc;
                Game1.dialogueUp = true;
                Game1.player.CanMove = false;

                this.Monitor.Log($"Displayed custom dialogue for {npc.Name}: '{dialogueText}'", LogLevel.Info);
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"API error: {ex.Message}", LogLevel.Error);
                this.ShowFallbackDialogue(npc, "Error fetching dialogue.");
            }
            finally
            {
                this.isRequestInProgress = false;
            }
        }

        private Dialogue CreateDialogueSequence(NPC npc, string dialogueText)
        {
            // Create the main dialogue
            var dialogue = new Dialogue(npc, dialogueText);
            
            // Set a default happy expression
            dialogue.CurrentEmotion = "$h";

            // You could parse the LLM response to set different emotions
            // Example: if dialogueText contains "[happy]" or similar markers
            if (dialogueText.Contains("[angry]"))
                dialogue.CurrentEmotion = "$a";
            else if (dialogueText.Contains("[sad]"))
                dialogue.CurrentEmotion = "$s";
            else if (dialogueText.Contains("[neutral]"))
                dialogue.CurrentEmotion = "$n";

            return dialogue;
        }

        private void ShowFallbackDialogue(NPC npc, string errorContext)
        {
            this.Monitor.Log($"Showing fallback dialogue due to: {errorContext}", LogLevel.Warn);
            // Create a simple fallback dialogue
            var fallbackDialogue = new Dialogue(npc, "...");
            npc.CurrentDialogue.Clear();
            npc.CurrentDialogue.Push(fallbackDialogue);
            Game1.currentSpeaker = npc;
            Game1.dialogueUp = true;
            Game1.player.CanMove = false;
        }

        private string GatherLewisContext(NPC npc)
        {
            var friendship = Game1.player.friendshipData.ContainsKey(npc.Name) ? Game1.player.friendshipData[npc.Name] : null;
            int hearts = friendship != null ? friendship.Points / 250 : 0;
            var context = new
            {
                npc_name = npc.Name,
                npc_location = npc.currentLocation?.Name,
                player_name = Game1.player.Name,
                friendship_hearts = hearts,
                season = Game1.currentSeason,
                day_of_month = Game1.dayOfMonth,
                day_of_week = new WorldDate(Game1.year, Game1.currentSeason, Game1.dayOfMonth).DayOfWeek.ToString(),
                time_of_day = Game1.timeOfDay,
                year = Game1.year,
                weather = Game1.isRaining ? "raining" : Game1.isSnowing ? "snowing" : Game1.isLightning ? "lightning" : "clear",
                player_location = Game1.currentLocation.Name
            };
            return JsonSerializer.Serialize(context);
        }
    }
} 