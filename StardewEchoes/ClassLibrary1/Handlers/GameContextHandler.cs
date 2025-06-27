using StardewValley;

namespace StardewEchoes.Handlers
{
  public class GameContextHandler
  {
    public string GetGameLanguage()
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

    public string GetLocalizedText(string englishText)
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

    public int GetFriendshipHearts(string npcName)
    {
      return GetFriendshipPoints(npcName) / 250;
    }

    public int GetFriendshipPoints(string npcName)
    {
      if (Game1.player.friendshipData.TryGetValue(npcName, out Friendship friendship))
      {
        return friendship.Points;
      }
      return 0;
    }

    public string GetCurrentWeather()
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
