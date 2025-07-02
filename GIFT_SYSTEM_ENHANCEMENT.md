# 🎁 Enhanced Gift System with Official Stardew Valley Data

## Overview

We've significantly enhanced the gift system in the StardewEchoes mod by integrating the complete official Stardew Valley gift preferences database. This provides the AI with accurate, game-consistent information to make better gift-related decisions.

## What Was Added

### 1. Complete Gift Preferences Database (`api/app/data/gift_preferences.py`)

- **Complete villager data**: All 33 NPCs with their loved, liked, disliked, and hated gifts
- **Birthday information**: Accurate birthday dates for all characters
- **Universal preferences**: Items that are universally loved, liked, disliked, or hated
- **Gift categories**: Organized categorization of items (gems, flowers, fruits, etc.)

**Source**: Based on the [official Steam community guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2133111137)

### 2. Enhanced AI Gift Preference System

The `determine_gift_preference_with_ai()` function now:

1. **Checks official data first**: If an item has a known preference in the game database, uses it directly
2. **Falls back to AI**: For neutral/unknown items, uses AI with comprehensive context
3. **Provides full context**: Gives the AI complete information about the NPC's official preferences

### 3. New API Endpoints

#### `GET /gift_preferences/{npc_name}`

Get complete gift preferences for a specific NPC:

```json
{
  "npc_name": "Abigail",
  "birthday": "Fall 13",
  "preferences": {
    "loved": ["Amethyst", "Blackberry Cobbler", ...],
    "liked": ["All other gems", "All flowers", ...],
    "disliked": ["All fish (except Crab, Lobster, Shrimp, Snail)", ...],
    "hated": ["Holly", "Wild Horseradish"]
  },
  "loved_gifts_total": [...], // Including universal loves
  "summary": {
    "loved_count": 6,
    "liked_count": 7,
    "disliked_count": 4,
    "hated_count": 2
  }
}
```

#### `GET /gift_preferences`

Get summary of all NPCs:

```json
{
  "total_npcs": 33,
  "npcs": {
    "Abigail": {
      "birthday": "Fall 13",
      "loved_count": 6,
      "liked_count": 7,
      "disliked_count": 4,
      "hated_count": 2,
      "top_loved_gifts": ["Amethyst", "Blackberry Cobbler", ...]
    },
    ...
  }
}
```

#### `POST /check_gift_preference`

Check preference for a specific gift:

```json
// Request
{
  "npc_name": "Abigail",
  "item_name": "Amethyst",
  "item_category": "Gem"
}

// Response
{
  "npc_name": "Abigail",
  "item_name": "Amethyst",
  "item_category": "Gem",
  "official_preference": "loved",
  "source": "official_game_data", // or "ai_inference"
  "context": "OFFICIAL STARDEW VALLEY GIFT PREFERENCES FOR ABIGAIL: ..."
}
```

## How It Works

### 1. Gift Detection (C# Mod)

When a player gives a gift, the `GiftHandler` creates a `GiftInfo` object with:

- Item name
- Item category
- Item quality
- Whether it's the NPC's birthday
- Preference set to "unknown" (letting the API decide)

### 2. API Processing

The API processes the gift through:

1. **Official lookup**: Check if the gift has a known preference in the database
2. **Context generation**: Create comprehensive context for the AI including:
   - Official game preferences for that NPC
   - NPC personality traits
   - Similar items that are loved/hated
3. **AI decision**: If needed, use AI to determine preference with full context
4. **Friendship calculation**: Calculate appropriate friendship points based on preference and quality

### 3. AI Context Enhancement

The AI now receives context like:

```
OFFICIAL STARDEW VALLEY GIFT PREFERENCES FOR ABIGAIL:

🎁 ITEM BEING GIVEN: Amethyst (Category: Gem)
📊 OFFICIAL GAME PREFERENCE: LOVED

❤️ LOVED GIFTS (Abigail absolutely adores these):
Amethyst, Blackberry Cobbler, Chocolate Cake, Pufferfish, Pumpkin, Spicy Eel

😊 LIKED GIFTS (Abigail appreciates these):
All other gems, All flowers, Quartz, Earth Crystal, Fire Quartz, Frozen Tear...

🎂 BIRTHDAY: Fall 13

INSTRUCTIONS: Use this official data to determine the exact gift preference...
```

## Benefits

### 1. **Game Accuracy**

- Matches official Stardew Valley gift preferences exactly
- Maintains consistency with player expectations
- Respects game lore and character personalities

### 2. **Enhanced AI Intelligence**

- AI makes better decisions with comprehensive context
- Falls back gracefully for unknown items
- Considers character personality patterns

### 3. **Developer Tools**

- New API endpoints for testing and debugging
- Easy to query gift preferences
- Comprehensive logging

### 4. **Extensibility**

- Easy to add new NPCs or modify preferences
- Structured data format for future enhancements
- Separation of data from logic

## Database Coverage

The system includes complete data for **33 NPCs**:

**Marriage Candidates**:

- Abigail, Alex, Elliott, Emily, Haley, Harvey, Leah, Maru, Penny, Sam, Sebastian, Shane (12)

**Townspeople**:

- Caroline, Clint, Demetrius, Evelyn, George, Gus, Jodi, Kent, Lewis, Linus, Marnie, Pam, Pierre, Robin, Willy, Wizard (16)

**Children**:

- Jas, Vincent (2)

**Special NPCs**:

- Dwarf, Krobus, Sandy (3)

Each NPC has:

- ✅ Complete loved gifts list
- ✅ Complete liked gifts list
- ✅ Complete disliked gifts list
- ✅ Complete hated gifts list
- ✅ Accurate birthday information

## Testing

The system includes comprehensive testing via `test_gift_api.py`:

```bash
python test_gift_api.py
```

This tests:

- ✅ NPC preference retrieval
- ✅ Specific gift preference checking
- ✅ Official vs AI-inferred preferences
- ✅ All NPCs summary data

## Future Enhancements

1. **Seasonal Preferences**: Add seasonal modifiers to gifts
2. **Friendship Level Impact**: Adjust preferences based on relationship level
3. **Mod Item Support**: Add preferences for modded items
4. **Dynamic Learning**: Let AI learn new preferences over time
5. **Gift Suggestions**: Provide gift recommendations to players

## Integration Status

- ✅ Database created with all official data
- ✅ API endpoints implemented and tested
- ✅ AI enhancement with contextual information
- ✅ C# mod integration ready
- ✅ Comprehensive testing suite
- ✅ Documentation complete

The enhanced gift system is now ready for production use and provides a solid foundation for future gift-related features!
