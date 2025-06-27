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

            helper.Events.Input.ButtonPressed += OnButtonPressed;
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
                    this.Helper.Input.Suppress(e.Button);
                    Game1.player.Halt();
                    Game1.player.faceGeneralDirection(npc.getStandingPosition());
                    dialogueHandler?.AbrirDialogoConOpciones(npc);
                }
            }
        }

        private void OnMenuChanged(object? sender, MenuChangedEventArgs e)
        {
            dialogueHandler?.OnMenuChanged(sender, e);
        }
    }
}
