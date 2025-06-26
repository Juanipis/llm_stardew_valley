using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using System;
using System.Collections.Generic;
using System.Net.Http;
using StardewEchoes.Handlers;
using StardewEchoes.Models;

namespace StardewEchoes
{
    public class ModEntry : Mod
    {
        private HttpClient? httpClient;
        private DialogueHandler? dialogueHandler;
        private readonly Dictionary<string, List<ConversationEntry>> conversationHistories = new Dictionary<string, List<ConversationEntry>>();

        public override void Entry(IModHelper helper)
        {
            httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(30)
            };

            dialogueHandler = new DialogueHandler(
                this.Monitor,
                this.Helper,
                httpClient,
                conversationHistories,
                GetFriendshipHearts,
                GetCurrentWeather,
                GetGameLanguage,
                GetLocalizedText
            );

            helper.Events.Input.ButtonPressed += OnButtonPressed;
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
                    dialogueHandler?.AbrirDialogoConOpciones(npc);
                }
            }
        }

        private string GetGameLanguage()
        {
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
                _ => "en"
            };
        }

        private string GetLocalizedText(string englishText)
        {
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
                    _ => englishText
                }
            };
        }

        private int GetFriendshipHearts(string npcName)
        {
            if (Game1.player.friendshipData.ContainsKey(npcName))
            {
                int points = Game1.player.friendshipData[npcName].Points;
                return points / 250;
            }
            return 0;
        }

        private string GetCurrentWeather()
        {
            if (Game1.isRaining)
            {
                return Game1.isLightning ? "Storm" : "Rain";
            }
            if (Game1.isSnowing)
                return "Snow";
            if (Game1.isDebrisWeather)
                return "Wind";
            return "Sun";
        }
    }
}
