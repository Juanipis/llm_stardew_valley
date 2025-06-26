using System.Collections.Generic;

namespace StardewEchoes.Models
{
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
}
