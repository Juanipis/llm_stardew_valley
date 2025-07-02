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
        private GameContextHandler? gameContextHandler;
        private GiftHandler? giftHandler;
        private readonly Dictionary<string, List<ConversationEntry>> conversationHistories = new Dictionary<string, List<ConversationEntry>>();

        public override void Entry(IModHelper helper)
        {
            httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(30)
            };

            gameContextHandler = new GameContextHandler();

            dialogueHandler = new DialogueHandler(
                this.Monitor,
                this.Helper,
                httpClient,
                conversationHistories,
                gameContextHandler
            );

            // GiftHandler now handles ALL NPC interactions (with and without gifts)
            // This prevents double-triggering of conversations that was happening when
            // both ModEntry.OnButtonPressed and GiftHandler.OnButtonPressed were active
            giftHandler = new GiftHandler(this.Monitor, this.Helper, dialogueHandler);

            // Only keep MenuChanged event for dialogue flow management
            // NOTE: ButtonPressed event removed to avoid conflicts with GiftHandler
            helper.Events.Display.MenuChanged += OnMenuChanged;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                httpClient?.Dispose();
            }
            base.Dispose(disposing);
        }

        private void OnMenuChanged(object? sender, MenuChangedEventArgs e)
        {
            dialogueHandler?.OnMenuChanged(sender, e);
        }
    }
}
