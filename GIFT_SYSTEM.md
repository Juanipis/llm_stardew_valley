# Gift-Giving Conversation System

## Overview

The StardewEchoes mod now includes an intelligent gift-giving conversation system that triggers dynamic conversations whenever a player gives a gift to an NPC. This system integrates with the existing AI-powered dialogue and memory systems.

## How It Works

### 1. Gift Detection

- The `GiftHandler` monitors player interactions and inventory changes
- When a player gives an item to an NPC, the system automatically detects it
- The handler captures gift details including item name, quality, and category

### 2. Gift Analysis

- The system analyzes the gift based on the NPC's preferences
- Gift preferences are categorized as: `loved`, `liked`, `neutral`, `disliked`, `hated`
- Special bonuses apply for birthday gifts (8x friendship multiplier)
- Item quality affects friendship points (normal, silver, gold, iridium quality)

### 3. Conversation Trigger

- After detecting a gift, the system automatically triggers a conversation
- The conversation context includes detailed gift information
- NPCs respond authentically based on their personality and gift preference

### 4. Friendship Calculation

- Friendship points are calculated based on:
  - Base gift preference (loved: 80pts, liked: 45pts, neutral: 20pts, disliked: -20pts, hated: -40pts)
  - Quality multiplier (normal: 1x, silver: 1.25x, gold: 1.5x, iridium: 2x)
  - Birthday bonus (8x multiplier on special day)
  - NPC-specific adjustments (e.g., Shane is harder to please)

## Technical Implementation

### C# Mod Components

**GiftHandler.cs**

- Monitors `Input.ButtonPressed` and `Player.InventoryChanged` events
- Detects when items are given to NPCs
- Triggers gift conversations through the DialogueHandler
- Contains gift preference database for major NPCs

**Updated DialogueHandler.cs**

- Enhanced to support gift context in API requests
- Creates detailed `GiftInfo` objects with item details
- Checks for NPC birthdays using `npc.isBirthday()`

**Models/DialogueRequest.cs**

- Added `GiftInfo` class with item details
- Includes quality, preference, and birthday information

### Python API Components

**models/request.py**

- Added `GiftInfo` model for gift data transfer
- Integrated with existing `DialogueRequest` structure

**routers/dialogue.py**

- New `calculate_gift_friendship_change()` function
- Enhanced dialogue prompts with gift context
- Special gift reaction instructions for NPCs

## Supported NPCs and Preferences

The system includes gift preferences for major NPCs:

**Abigail**: Loves amethyst, chocolate cake, blackberry cobbler, pufferfish, spicy eel
**Alex**: Loves complete breakfast, salmon dinner; likes eggs, mayonnaise  
**Elliott**: Loves crab cakes, duck feather, lobster, pomegranate, squid ink, tom kha soup
**Emily**: Loves gems (amethyst, aquamarine, emerald, jade, ruby, topaz), cloth, wool, survival burger
**Haley**: Loves coconut, fruit salad, pink cake, sunflower; likes daffodils

_Additional NPCs can be easily added to the gift preference database._

## Example Gift Interactions

### Loved Gift on Birthday

```
Player gives Amethyst to Abigail on her birthday
→ +640 friendship points (80 base × 8 birthday × 1.0 quality)
→ Conversation: "OMG! An amethyst on my birthday?! This is absolutely perfect! Thank you so much!"
```

### Quality Gift

```
Player gives Iridium Quality Coffee to Elliott
→ +50 friendship points (45 base × 1.0 neutral × 2.0 iridium quality)
→ Conversation: "What exquisite coffee! The quality is remarkable - I can taste the care that went into this."
```

### Disliked Gift

```
Player gives Trash to any NPC
→ -20 friendship points
→ Conversation: "Um... thanks? I'm not really sure what to do with this..."
```

## Configuration

Gift preferences can be customized by modifying the `giftPreferences` dictionary in `GiftHandler.cs`. The system supports:

- Any Stardew Valley item by name
- Preference levels: loved, liked, neutral, disliked, hated
- Easy addition of new NPCs and preferences

## Future Enhancements

- Dynamic learning of gift preferences based on player interactions
- Seasonal gift preferences (e.g., different favorites in winter vs summer)
- Memory integration to remember past gifts
- Special event gift reactions (festivals, heart events, etc.)
- Gift recommendation system based on NPC analysis

## Integration with Existing Systems

The gift system seamlessly integrates with:

- **Memory System**: Gift events are stored in conversation history
- **Emotional State**: Gift reactions affect NPC emotional states
- **Personality Profiles**: Gift preferences align with character personalities
- **Friendship Tracking**: Automatic friendship point adjustments
- **AI Dialogue**: Contextual responses based on gift quality and preference

This creates a rich, immersive experience where every gift matters and contributes to the evolving relationship between the player and NPCs.
