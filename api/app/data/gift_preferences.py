"""
Stardew Valley Gift Preferences Database
Based on official game data and community guides.

This data is used by the AI to make informed decisions about gift preferences
while maintaining consistency with the actual game mechanics.

Source: https://steamcommunity.com/sharedfiles/filedetails/?id=2133111137
"""

from typing import Dict, List, Set

# Complete gift preferences for all villagers
VILLAGER_GIFT_PREFERENCES: Dict[str, Dict[str, List[str]]] = {
    "Abigail": {
        "loved": [
            "Amethyst",
            "Blackberry Cobbler",
            "Chocolate Cake",
            "Pufferfish",
            "Pumpkin",
            "Spicy Eel",
        ],
        "liked": [
            "All other gems",
            "All flowers",
            "Quartz",
            "Earth Crystal",
            "Fire Quartz",
            "Frozen Tear",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
        ],
        "disliked": [
            "All fish (except Crab, Lobster, Shrimp, Snail)",
            "All eggs",
            "All milk",
            "Clay",
        ],
        "hated": ["Holly", "Wild Horseradish"],
    },
    "Alex": {
        "loved": ["Complete Breakfast", "Salmon Dinner"],
        "liked": [
            "All eggs",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
        ],
        "disliked": [
            "All flowers",
            "All vegetables",
            "All gems",
            "All artifacts",
            "Wild Seeds",
            "Tea Leaves",
        ],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Caroline": {
        "loved": ["Fish Taco", "Green Tea", "Summer Spangle"],
        "liked": [
            "All fruits",
            "All vegetables",
            "Tea Leaves",
            "Daffodil",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
        ],
        "disliked": ["All fish", "All gems", "All artifacts", "Wild Seeds"],
        "hated": ["Holly", "Mayonnaise", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Clint": {
        "loved": [
            "Amethyst",
            "Aquamarine",
            "Artichoke Dip",
            "Emerald",
            "Fiddlehead Risotto",
            "Gold Bar",
            "Iridium Bar",
            "Jade",
            "Omni Geode",
            "Ruby",
            "Topaz",
        ],
        "liked": [
            "All gems",
            "All geodes",
            "All metal bars",
            "Copper Ore",
            "Iron Ore",
            "Gold Ore",
            "Iridium Ore",
            "Coal",
        ],
        "disliked": ["All flowers", "All fruits", "All milk", "Clay"],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
    "Demetrius": {
        "loved": ["Bean Hotpot", "Ice Cream", "Rice Pudding", "Strawberry"],
        "liked": [
            "All fruits",
            "All eggs",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Purple Mushroom",
        ],
        "disliked": ["All flowers", "All gems", "All artifacts", "Wild Seeds"],
        "hated": ["Holly", "Mayonnaise", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Dwarf": {
        "loved": [
            "Amethyst",
            "Aquamarine",
            "Emerald",
            "Jade",
            "Lemon Stone",
            "Omni Geode",
            "Ruby",
            "Topaz",
        ],
        "liked": [
            "All gems",
            "All geodes",
            "All metal bars",
            "All artifacts",
            "Dwarf Scroll I",
            "Dwarf Scroll II",
            "Dwarf Scroll III",
            "Dwarf Scroll IV",
        ],
        "disliked": ["All flowers", "All fruits", "All vegetables", "All fish"],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
    "Elliott": {
        "loved": [
            "Crab Cakes",
            "Duck Feather",
            "Lobster",
            "Pomegranate",
            "Tom Kha Soup",
        ],
        "liked": [
            "All fruits",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Squid Ink",
            "All books",
        ],
        "disliked": [
            "All fish (except Crab, Lobster, Shrimp, Snail)",
            "All gems",
            "Wild Seeds",
            "Acorn",
            "Maple Seed",
            "Pine Cone",
        ],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Emily": {
        "loved": [
            "Amethyst",
            "Aquamarine",
            "Cloth",
            "Emerald",
            "Jade",
            "Ruby",
            "Survival Burger",
            "Topaz",
            "Wool",
        ],
        "liked": [
            "All gems",
            "All flowers",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Coconut",
            "Cactus Fruit",
            "Crystal Fruit",
        ],
        "disliked": ["All fish", "All eggs", "All milk", "Mayonnaise", "Ice Cream"],
        "hated": ["Holly", "Maki Roll", "Salmon Dinner", "Sashimi"],
    },
    "Evelyn": {
        "loved": [
            "Beet",
            "Chocolate Cake",
            "Diamond",
            "Fairy Rose",
            "Stuffing",
            "Tulip",
        ],
        "liked": [
            "All flowers",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All vegetables",
            "All fruits",
        ],
        "disliked": ["All fish", "All gems (except Diamond)", "Wild Seeds"],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish", "Fried Eel"],
    },
    "George": {
        "loved": ["Fried Mushroom", "Leek"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Daffodil",
        ],
        "disliked": [
            "All flowers (except Daffodil)",
            "All fruits",
            "All gems",
            "All vegetables (except Leek)",
            "Wild Seeds",
        ],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Gus": {
        "loved": ["Diamond", "Escargot", "Fish Taco", "Orange"],
        "liked": [
            "All cooked foods",
            "All fruits",
            "All eggs",
            "All milk",
            "Truffle",
            "Truffle Oil",
        ],
        "disliked": ["All flowers", "All gems (except Diamond)", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Haley": {
        "loved": ["Coconut", "Fruit Salad", "Pink Cake", "Sunflower"],
        "liked": [
            "All fruits",
            "Daffodil",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
        ],
        "disliked": ["All fish", "All gems", "All vegetables", "Clay", "Wild Seeds"],
        "hated": [
            "Holly",
            "Prismatic Shard",
            "Quartz",
            "Salmonberries",
            "Wild Horseradish",
        ],
    },
    "Harvey": {
        "loved": ["Coffee", "Pickles", "Super Meal", "Truffle Oil", "Wine"],
        "liked": [
            "All fruits",
            "All vegetables",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Energy Tonic",
            "Muscle Remedy",
        ],
        "disliked": [
            "All flowers",
            "All gems",
            "Wild Seeds",
            "Acorn",
            "Maple Seed",
            "Pine Cone",
        ],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Jas": {
        "loved": ["Fairy Rose", "Pink Cake", "Plum Pudding"],
        "liked": [
            "All flowers",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "Coconut",
        ],
        "disliked": ["All fish", "All gems", "All vegetables", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Jodi": {
        "loved": [
            "Chocolate Cake",
            "Crispy Bass",
            "Diamond",
            "Eggplant Parmesan",
            "Fried Eel",
            "Pancakes",
            "Rhubarb Pie",
            "Vegetable Medley",
        ],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All eggs",
            "All milk",
            "All fruits",
        ],
        "disliked": ["All flowers", "All gems (except Diamond)", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Kent": {
        "loved": ["Fiddlehead Risotto", "Roasted Hazelnuts"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Daffodil",
            "All fruits",
        ],
        "disliked": ["All flowers (except Daffodil)", "All gems", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Krobus": {
        "loved": [
            "Diamond",
            "Iridium Bar",
            "Pumpkin",
            "Void Egg",
            "Void Mayonnaise",
            "Wild Horseradish",
        ],
        "liked": [
            "All gems",
            "All artifacts",
            "Horseradish",
            "Void Essence",
            "Solar Essence",
            "Life Elixir",
        ],
        "disliked": [
            "All cooked foods",
            "All flowers",
            "All fruits",
            "All vegetables (except Horseradish, Pumpkin)",
        ],
        "hated": ["Holly", "Strange Bun"],
    },
    "Leah": {
        "loved": [
            "Goat Cheese",
            "Poppyseed Muffin",
            "Salad",
            "Stir Fry",
            "Truffle",
            "Vegetable Medley",
            "Wine",
        ],
        "liked": [
            "All fruits",
            "All vegetables",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All flowers",
            "Driftwood",
        ],
        "disliked": ["All fish", "All gems", "Bread", "Pancakes", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Lewis": {
        "loved": [
            "Autumn's Bounty",
            "Glazed Yams",
            "Green Tea",
            "Hot Pepper",
            "Vegetable Medley",
        ],
        "liked": [
            "All vegetables",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Blueberry",
            "Cactus Fruit",
        ],
        "disliked": ["All flowers", "All gems", "Wild Seeds", "Pickles"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Linus": {
        "loved": [
            "Blueberry Tart",
            "Cactus Fruit",
            "Coconut",
            "Dish O' The Sea",
            "Yam",
        ],
        "liked": [
            "All fruits",
            "All vegetables",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All forageable items",
            "Wild Seeds",
        ],
        "disliked": ["All flowers", "All gems", "Bread", "Maki Roll"],
        "hated": [
            "Holly",
            "Quartz",
            "Salmonberries (disliked when given, not hated)",
            "Wild Horseradish (loved, not hated)",
        ],
    },
    "Marnie": {
        "loved": ["Diamond", "Farmer's Lunch", "Pink Cake", "Pumpkin Pie"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All eggs",
            "All milk",
            "All fruits",
        ],
        "disliked": ["All flowers", "All gems (except Diamond)", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Maru": {
        "loved": [
            "Battery Pack",
            "Cauliflower",
            "Cheese Cauliflower",
            "Diamond",
            "Gold Bar",
            "Iridium Bar",
            "Miner's Treat",
            "Pepper Poppers",
            "Rhubarb Pie",
            "Strawberry",
        ],
        "liked": [
            "All gems",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "Quartz",
            "Refined Quartz",
        ],
        "disliked": ["All flowers", "All fish", "Honey", "Maple Syrup"],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
    "Pam": {
        "loved": [
            "Beer",
            "Cactus Fruit",
            "Glazed Yams",
            "Mead",
            "Pale Ale",
            "Parsnip",
            "Parsnip Soup",
        ],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "Daffodil",
            "Life Elixir",
        ],
        "disliked": ["All flowers (except Daffodil)", "All gems", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Penny": {
        "loved": [
            "Diamond",
            "Emerald",
            "Melon",
            "Poppy",
            "Poppyseed Muffin",
            "Red Plate",
            "Roots Platter",
            "Sandfish",
            "Tom Kha Soup",
        ],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "All flowers",
            "All gems",
            "All books",
        ],
        "disliked": [
            "All fish (except Crab, Lobster, Shrimp, Snail, Sandfish)",
            "Beer",
            "Grape",
            "Holly",
            "Hops",
            "Mead",
            "Pale Ale",
            "Wine",
        ],
        "hated": ["Holly", "Rabbit's Foot", "Duck Feather"],
    },
    "Pierre": {
        "loved": ["Fried Calamari"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Daffodil",
        ],
        "disliked": ["All flowers (except Daffodil)", "All gems", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Robin": {
        "loved": ["Goat Cheese", "Peach", "Spaghetti"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "Hardwood",
        ],
        "disliked": ["All flowers", "All gems", "Quartz", "Wild Seeds"],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
    "Sam": {
        "loved": ["Cactus Fruit", "Maple Bar", "Pizza", "Tigerseye"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All eggs",
            "Joja Cola",
        ],
        "disliked": [
            "All flowers",
            "All fruits (except Cactus Fruit)",
            "All vegetables",
            "All gems (except Tigerseye)",
            "Mayonnaise",
        ],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Sandy": {
        "loved": ["Crocus", "Daffodil", "Sweet Pea"],
        "liked": [
            "All flowers",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "Coconut",
        ],
        "disliked": ["All fish", "All gems", "Clay", "Wild Seeds"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Sebastian": {
        "loved": ["Frozen Tear", "Obsidian", "Pumpkin Soup", "Sashimi", "Void Egg"],
        "liked": [
            "All gems",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Coffee",
            "Quartz",
        ],
        "disliked": [
            "All flowers",
            "All eggs (except Void Egg)",
            "Clay",
            "Complete Breakfast",
        ],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
    "Shane": {
        "loved": ["Beer", "Hot Pepper", "Pepper Poppers", "Pizza"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All eggs",
            "All fruits",
        ],
        "disliked": ["All flowers", "All gems", "Pickles", "Quartz"],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
    "Vincent": {
        "loved": ["Cranberry Candy", "Grape", "Pink Cake", "Snail"],
        "liked": [
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "All fruits",
            "Coconut",
        ],
        "disliked": ["All flowers", "All gems", "All vegetables", "Wild Seeds"],
        "hated": ["Holly", "Mayonnaise", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Willy": {
        "loved": [
            "Catfish",
            "Diamond",
            "Iridium Bar",
            "Mead",
            "Octopus",
            "Pumpkin",
            "Sea Cucumber",
            "Sturgeon",
        ],
        "liked": [
            "All fish",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Daffodil",
            "All gems (except Quartz)",
        ],
        "disliked": ["All flowers (except Daffodil)", "All fruits", "Algae", "Seaweed"],
        "hated": ["Holly", "Quartz", "Salmonberries", "Wild Horseradish"],
    },
    "Wizard": {
        "loved": ["Purple Mushroom", "Solar Essence", "Super Cucumber", "Void Essence"],
        "liked": [
            "All gems",
            "All cooked foods (except Bread, Fried Egg, Strange Bun)",
            "Quartz",
            "All magical items",
        ],
        "disliked": [
            "All flowers",
            "All fish (except Super Cucumber)",
            "All eggs",
            "Wild Seeds",
        ],
        "hated": ["Holly", "Salmonberries", "Wild Horseradish"],
    },
}

# Birthday information for all villagers
VILLAGER_BIRTHDAYS: Dict[str, str] = {
    "Abigail": "Fall 13",
    "Alex": "Summer 13",
    "Caroline": "Winter 7",
    "Clint": "Winter 26",
    "Demetrius": "Summer 19",
    "Dwarf": "Summer 22",
    "Elliott": "Fall 5",
    "Emily": "Spring 27",
    "Evelyn": "Winter 20",
    "George": "Fall 24",
    "Gus": "Summer 8",
    "Haley": "Spring 14",
    "Harvey": "Summer 6",
    "Jas": "Summer 4",
    "Jodi": "Fall 11",
    "Kent": "Spring 4",
    "Krobus": "Winter 1",
    "Leah": "Winter 23",
    "Lewis": "Spring 7",
    "Linus": "Winter 3",
    "Marnie": "Fall 18",
    "Maru": "Summer 10",
    "Pam": "Spring 18",
    "Penny": "Fall 2",
    "Pierre": "Spring 26",
    "Robin": "Fall 21",
    "Sam": "Summer 17",
    "Sandy": "Fall 15",
    "Sebastian": "Winter 10",
    "Shane": "Spring 20",
    "Vincent": "Spring 10",
    "Willy": "Summer 24",
    "Wizard": "Winter 17",
}

# Universal gift preferences (apply to most villagers)
UNIVERSAL_LOVES: Set[str] = {
    "Golden Pumpkin",
    "Magic Rock Candy",
    "Pearl",
    "Prismatic Shard",
    "Rabbit's Foot",
}

UNIVERSAL_LIKES: Set[str] = {
    "Life Elixir",
    "Oil of Garlic",
    "All Artisan Goods (except Mayonnaise, Oil, Void Mayonnaise)",
}

UNIVERSAL_NEUTRALS: Set[str] = {"Sap", "Wood", "Stone", "Fiber"}

UNIVERSAL_DISLIKES: Set[str] = {
    "Bait",
    "Crab Pot",
    "Fertilizer",
    "Basic Retaining Soil",
    "Quality Retaining Soil",
    "Speed-Gro",
    "Deluxe Speed-Gro",
    "Wild Seeds",
    "Winter Seeds",
}

UNIVERSAL_HATES: Set[str] = {"Bug Meat", "Hay", "Oil", "Void Mayonnaise", "Joja Cola"}

# Gift categories for easy lookup
GIFT_CATEGORIES: Dict[str, Set[str]] = {
    "gems": {
        "Amethyst",
        "Aquamarine",
        "Diamond",
        "Emerald",
        "Jade",
        "Ruby",
        "Topaz",
        "Quartz",
        "Earth Crystal",
        "Fire Quartz",
        "Frozen Tear",
        "Lemon Stone",
        "Neptunite",
        "Bixite",
        "Baryte",
        "Aerinite",
        "Calcite",
        "Dolomite",
        "Esperite",
        "Fluorapatite",
        "Geminite",
        "Helvite",
        "Jamborite",
        "Jagoite",
        "Kyanite",
        "Lunarite",
        "Malachite",
        "Orpiment",
        "Petrified Slime",
        "Thunder Egg",
        "Pyrite",
        "Ocean Stone",
        "Ghost Crystal",
        "Tigerseye",
        "Jasper",
        "Opal",
        "Fire Opal",
        "Celestine",
        "Marble",
        "Sandstone",
        "Granite",
        "Basalt",
        "Limestone",
        "Soapstone",
        "Hematite",
        "Mudstone",
        "Obsidian",
        "Slate",
        "Fairy Stone",
        "Star Shards",
    },
    "flowers": {
        "Parsnip",
        "Bean Starter",
        "Cauliflower",
        "Potato",
        "Tulip Bulb",
        "Kale",
        "Jazz",
        "Garlic",
        "Blue Jazz",
        "Cauliflower Seeds",
        "Coffee Bean",
        "Sunflower",
        "Spice Berry",
        "Wild Horseradish",
        "Daffodil",
        "Leek",
        "Dandelion",
        "Tulip",
        "Summer Spangle",
        "Sweet Pea",
        "Poppy",
        "Fairy Rose",
        "Crocus",
    },
    "fruits": {
        "Wild Horseradish",
        "Daffodil",
        "Leek",
        "Dandelion",
        "Parsnip",
        "Green Bean",
        "Cauliflower",
        "Potato",
        "Tulip Bulb",
        "Kale",
        "Jazz",
        "Garlic",
        "Blue Jazz",
        "Coffee Bean",
        "Apple",
        "Orange",
        "Peach",
        "Pomegranate",
        "Cherry",
        "Strawberry",
        "Rhubarb",
        "Melon",
        "Tomato",
        "Blueberry",
        "Hot Pepper",
        "Radish",
        "Red Cabbage",
        "Starfruit",
        "Corn",
        "Eggplant",
        "Pumpkin",
        "Bok Choy",
        "Yam",
        "Beet",
        "Artichoke",
        "Amaranth",
        "Grape",
        "Sweet Gem Berry",
        "Cranberries",
        "Sunflower Seeds",
        "Cactus Fruit",
        "Banana",
        "Mango",
        "Pineapple",
        "Coconut",
        "Crystal Fruit",
    },
    "vegetables": {
        "Parsnip",
        "Green Bean",
        "Cauliflower",
        "Potato",
        "Kale",
        "Garlic",
        "Rhubarb",
        "Tomato",
        "Hot Pepper",
        "Radish",
        "Red Cabbage",
        "Corn",
        "Eggplant",
        "Pumpkin",
        "Bok Choy",
        "Yam",
        "Beet",
        "Artichoke",
        "Amaranth",
        "Fiddlehead Fern",
        "Horseradish",
    },
    "fish": {
        "Carp",
        "Herring",
        "Sardine",
        "Bream",
        "Largemouth Bass",
        "Smallmouth Bass",
        "Rainbow Trout",
        "Salmon",
        "Walleye",
        "Perch",
        "Pike",
        "Red Mullet",
        "Sea Cucumber",
        "Super Cucumber",
        "Ghostfish",
        "Stonefish",
        "Ice Pip",
        "Lava Eel",
        "Sandfish",
        "Scorpion Carp",
        "Flounder",
        "Anchovy",
        "Tuna",
        "Sardine",
        "Red Snapper",
        "Tilapia",
        "Shad",
        "Lingcod",
        "Halibut",
        "Hardhead",
        "Crab",
        "Lobster",
        "Crayfish",
        "Periwinkle",
        "Oyster",
        "Mussel",
        "Clam",
        "Cockle",
        "Shrimp",
        "Snail",
        "Octopus",
        "Squid",
        "Pufferfish",
        "Eel",
        "Catfish",
        "Sturgeon",
        "Tiger Trout",
        "Bullhead",
        "Chub",
        "Dorado",
        "Albacore",
        "Legend",
        "Crimsonfish",
        "Angler",
        "Glacierfish",
        "Mutant Carp",
    },
}


def get_gift_preference(npc_name: str, item_name: str) -> str:
    """
    Get the gift preference for a specific NPC and item.

    Args:
        npc_name: Name of the NPC
        item_name: Name of the item

    Returns:
        Gift preference: "loved", "liked", "neutral", "disliked", or "hated"
    """
    if npc_name not in VILLAGER_GIFT_PREFERENCES:
        return "neutral"

    prefs = VILLAGER_GIFT_PREFERENCES[npc_name]

    # Check specific item preferences
    for preference_level, items in prefs.items():
        if item_name in items:
            return preference_level

    # Check universal preferences
    if item_name in UNIVERSAL_LOVES:
        return "loved"
    elif item_name in UNIVERSAL_LIKES:
        return "liked"
    elif item_name in UNIVERSAL_DISLIKES:
        return "disliked"
    elif item_name in UNIVERSAL_HATES:
        return "hated"

    return "neutral"


def get_npc_loved_gifts(npc_name: str) -> List[str]:
    """Get all loved gifts for a specific NPC."""
    if npc_name not in VILLAGER_GIFT_PREFERENCES:
        return []

    loved_gifts = VILLAGER_GIFT_PREFERENCES[npc_name].get("loved", [])
    return loved_gifts + list(UNIVERSAL_LOVES)


def get_npc_birthday(npc_name: str) -> str:
    """Get the birthday for a specific NPC."""
    return VILLAGER_BIRTHDAYS.get(npc_name, "Unknown")


def get_gift_context_for_ai(npc_name: str, item_name: str, item_category: str) -> str:
    """
    Generate comprehensive context about gift preferences for the AI to use.

    Args:
        npc_name: Name of the NPC
        item_name: Name of the item being given
        item_category: Category of the item

    Returns:
        Formatted context string for the AI
    """
    if npc_name not in VILLAGER_GIFT_PREFERENCES:
        return f"No specific preference data available for {npc_name}. Use general personality traits to decide."

    prefs = VILLAGER_GIFT_PREFERENCES[npc_name]
    loved = prefs.get("loved", [])
    liked = prefs.get("liked", [])
    disliked = prefs.get("disliked", [])
    hated = prefs.get("hated", [])

    # Check what preference level this specific item falls into
    actual_preference = get_gift_preference(npc_name, item_name)

    context = f"""OFFICIAL STARDEW VALLEY GIFT PREFERENCES FOR {npc_name.upper()}:

🎁 ITEM BEING GIVEN: {item_name} (Category: {item_category})
📊 OFFICIAL GAME PREFERENCE: {actual_preference.upper()}

❤️ LOVED GIFTS ({npc_name} absolutely adores these):
{", ".join(loved[:10]) + ("..." if len(loved) > 10 else "")}

😊 LIKED GIFTS ({npc_name} appreciates these):
{", ".join(liked[:10]) + ("..." if len(liked) > 10 else "")}

😐 DISLIKED GIFTS ({npc_name} doesn't really want these):
{", ".join(disliked[:10]) + ("..." if len(disliked) > 10 else "")}

💔 HATED GIFTS ({npc_name} really doesn't want these):
{", ".join(hated[:10]) + ("..." if len(hated) > 10 else "")}

🎂 BIRTHDAY: {get_npc_birthday(npc_name)}

INSTRUCTIONS: Use this official data to determine the exact gift preference. The "OFFICIAL GAME PREFERENCE" above shows exactly how {npc_name} feels about {item_name} in the actual game."""

    return context
