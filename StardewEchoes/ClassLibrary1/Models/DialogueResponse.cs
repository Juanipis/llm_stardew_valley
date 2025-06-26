using System.Collections.Generic;

namespace StardewEchoes.Models
{
  public class DialogueResponse
  {
    public string npc_message { get; set; } = "";
    public List<string> response_options { get; set; } = new List<string>();
  }
}
