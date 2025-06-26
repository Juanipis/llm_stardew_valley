using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;

namespace StardewEchoes
{
    public class ModEntry : Mod
    {
        private const string Mensaje = "Hola Mundo";

        public override void Entry(IModHelper helper)
        {
            helper.Events.Input.ButtonPressed += OnButtonPressed;
        }

        private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
        {
            if (!Context.IsWorldReady)
                return;

            if (e.Button.IsActionButton())
            {
                var tile = e.Cursor.GrabTile;
                var npc = Game1.currentLocation.isCharacterAtTile(tile);

                if (npc != null && npc.Name == "Lewis")
                {
                    Game1.player.Halt();
                    Game1.player.faceGeneralDirection(npc.getStandingPosition());
                    AbrirDialogoConOpciones(npc);
                }
            }
        }

        private void AbrirDialogoConOpciones(NPC npc)
        {
            Response[] opciones = new[]
            {
        new Response("repetir", "Hablar de nuevo"),
        new Response("salir", "Salir")
    };

            Game1.currentLocation.createQuestionDialogue(
                Mensaje,
                opciones,
                (farmer, key) =>
                {
                    if (key == "repetir")
                    {
                        // Usar el helper para ejecutar en el siguiente tick
                        this.Helper.Events.GameLoop.UpdateTicked += ReabrirDialogo;
                    }
                    // Si es "salir", no hace nada
                }
            );

            void ReabrirDialogo(object? sender, StardewModdingAPI.Events.UpdateTickedEventArgs e)
            {
                this.Helper.Events.GameLoop.UpdateTicked -= ReabrirDialogo;
                AbrirDialogoConOpciones(npc);
            }
        }

    }
}
