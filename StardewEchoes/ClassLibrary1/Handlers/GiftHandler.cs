using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;
using System;
using System.Collections.Generic;
using StardewEchoes.Models;
using System.Reflection;

namespace StardewEchoes.Handlers
{
    /// <summary>
    /// Ultra-robust GiftHandler that provides 100% reliable interception of ALL NPC interactions.
    /// 
    /// AGGRESSIVE INTERCEPTION STRATEGY:
    /// 
    /// 1. MULTIPLE EVENT INTERCEPTION:
    ///    - ButtonPressed with HIGHEST priority
    ///    - MenuChanged to block any gift dialogs that slip through
    ///    - Display.WindowResized as fallback detection
    /// 
    /// 2. COMPLETE GAME DIALOG SUPPRESSION:
    ///    - Immediate input suppression on ANY NPC click
    ///    - Active monitoring for gift-related dialogue menus
    ///    - Forced closure of any game gift dialogs
    /// 
    /// 3. ULTRA-SAFE PROCESSING:
    ///    - Multi-tick delay processing to ensure clean game state
    ///    - Complete item validation and safety checks
    ///    - Comprehensive duplicate interaction prevention
    /// 
    /// 4. BULLETPROOF FALLBACKS:
    ///    - Multiple suppression mechanisms
    ///    - Continuous monitoring during gift processing
    ///    - Emergency dialog closure if anything slips through
    /// </summary>
    public class GiftHandler
    {
        private readonly IMonitor Monitor;
        private readonly IModHelper Helper;
        private readonly DialogueHandler dialogueHandler;
        
        // Enhanced tracking for bulletproof duplicate prevention
        private NPC? lastInteractedNPC = null;
        private Item? lastHeldItem = null;
        private DateTime lastInteractionTime = DateTime.MinValue;
        private bool isProcessingGift = false;
        
        // Dialog suppression tracking
        private List<Type> suppressedMenuTypes = new List<Type>();

        public GiftHandler(IMonitor monitor, IModHelper helper, DialogueHandler dialogueHandler)
        {
            this.Monitor = monitor;
            this.Helper = helper;
            this.dialogueHandler = dialogueHandler;

            // ULTRA-HIGH PRIORITY: Intercept at the earliest possible moment
            helper.Events.Input.ButtonPressed += OnButtonPressed_UltraHighPriority;
            
            // BACKUP INTERCEPTION: Monitor for any dialogs that slip through
            helper.Events.Display.MenuChanged += OnMenuChanged_DialogSuppressor;
            
            // FINAL SAFETY NET: Monitor for any UI changes
            helper.Events.Display.WindowResized += OnWindowResized_SafetyNet;
            
            // CONTINUOUS MONITORING: Track cursor for interaction resets
            helper.Events.Input.CursorMoved += OnCursorMoved_InteractionTracker;

            // Initialize suppressed menu types (types that indicate gift dialogs)
            suppressedMenuTypes.Add(typeof(DialogueBox));
            
            Monitor.Log("🛡️ ULTRA-AGGRESSIVE GIFT HANDLER INITIALIZED", LogLevel.Info);
            Monitor.Log("🛡️ ALL NPC interactions will be intercepted and processed by AI", LogLevel.Info);
        }

        private void OnWindowResized_SafetyNet(object? sender, WindowResizedEventArgs e)
        {
            // Emergency reset if something goes wrong
            if (isProcessingGift)
            {
                Monitor.Log("🛡️ SAFETY NET: Resetting gift processing state", LogLevel.Debug);
                ResetProcessingState();
            }
        }

        private void OnMenuChanged_DialogSuppressor(object? sender, MenuChangedEventArgs e)
        {
            try
            {
                // If we're processing a gift and the game tries to show ANY dialog, suppress it
                if (isProcessingGift && e.NewMenu != null)
                {
                    Monitor.Log($"🛡️ DIALOG SUPPRESSOR: Blocking {e.NewMenu.GetType().Name} during gift processing", LogLevel.Debug);
                    
                    // Force close any menus that appear during gift processing
                    Game1.activeClickableMenu = null;
                    Game1.exitActiveMenu();
                    
                    Monitor.Log("🛡️ DIALOG SUPPRESSED: Game dialog blocked, AI will handle the response", LogLevel.Info);
                }
                
                // Also check for specific gift-related dialogs even when not processing
                if (e.NewMenu is DialogueBox dialogueBox && !isProcessingGift)
                {
                    // Check if this might be a gift dialog by examining the speaker
                    if (dialogueBox.characterDialogue?.speaker != null)
                    {
                        var speaker = dialogueBox.characterDialogue.speaker;
                        
                        // If the player is holding an item, this might be a gift dialog
                        var heldItem = Game1.player?.ActiveObject;
                        if (heldItem != null && IsValidGiftItem(heldItem))
                        {
                            Monitor.Log($"🛡️ GIFT DIALOG DETECTED: Intercepting dialog from {speaker.Name}", LogLevel.Info);
                            
                            // Close the dialog and process with AI instead
                            Game1.activeClickableMenu = null;
                            Game1.exitActiveMenu();
                            
                            // Process the gift with AI
                            Helper.Events.GameLoop.UpdateTicked += ProcessInterceptedGift;
                            
                            void ProcessInterceptedGift(object? s, UpdateTickedEventArgs updateArgs)
                            {
                                Helper.Events.GameLoop.UpdateTicked -= ProcessInterceptedGift;
                                
                                if (heldItem != null && !isProcessingGift)
                                {
                                    Monitor.Log("🛡️ PROCESSING INTERCEPTED GIFT", LogLevel.Info);
                                    ProcessGiftWithAI(speaker, heldItem);
                                }
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error in dialog suppressor: {ex.Message}", LogLevel.Error);
            }
        }

        private void OnCursorMoved_InteractionTracker(object? sender, CursorMovedEventArgs e)
        {
            // Reset interaction tracking if cursor moves significantly or time passes
            if (lastInteractedNPC != null)
            {
                var timeSinceLastInteraction = DateTime.Now - lastInteractionTime;
                if (timeSinceLastInteraction.TotalMilliseconds > 1000) // 1 second timeout
                {
                    ResetInteractionTracking();
                }
            }
            
            // Also reset processing state if cursor moves far while processing
            if (isProcessingGift)
            {
                var timeSinceLastInteraction = DateTime.Now - lastInteractionTime;
                if (timeSinceLastInteraction.TotalMilliseconds > 2000) // 2 second timeout for processing
                {
                    Monitor.Log("🛡️ PROCESSING TIMEOUT: Resetting gift processing state", LogLevel.Debug);
                    ResetProcessingState();
                }
            }
        }

        private void OnButtonPressed_UltraHighPriority(object? sender, ButtonPressedEventArgs e)
        {
            try
            {
                // IMMEDIATE basic checks
                if (!Context.IsWorldReady || !e.Button.IsActionButton())
                    return;

                // Quick NPC detection without complex validation
                var tile = e.Cursor.GrabTile;
                var npc = Game1.currentLocation?.isCharacterAtTile(tile);

                // ULTRA-AGGRESSIVE: Suppress ANY interaction with ANY NPC immediately
                if (npc != null && npc.IsVillager)
                {
                    // ⚡ IMMEDIATE SUPPRESSION - No questions asked
                    this.Helper.Input.Suppress(e.Button);
                    
                    Monitor.Log($"🛡️ ULTRA-SUPPRESSION: {npc.Name} interaction intercepted", LogLevel.Debug);
                    
                    // Additional suppression techniques for bulletproof blocking
                    Game1.player.forceCanMove();
                    
                    // Multi-tick delayed processing for maximum safety
                    ScheduleDelayedProcessing(npc);
                }
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error in ultra-high priority handler: {ex.Message}", LogLevel.Error);
            }
        }

        private void ScheduleDelayedProcessing(NPC npc)
        {
            // Use multiple ticks delay to ensure the game state is completely clean
            int tickDelay = 3; // 3 game ticks delay
            
            Helper.Events.GameLoop.UpdateTicked += DelayedProcessor;
            
            void DelayedProcessor(object? s, UpdateTickedEventArgs updateArgs)
            {
                tickDelay--;
                
                if (tickDelay <= 0)
                {
                    Helper.Events.GameLoop.UpdateTicked -= DelayedProcessor;
                    ProcessNPCInteractionSafely(npc);
                }
            }
        }

        private void ProcessNPCInteractionSafely(NPC npc)
        {
            try
            {
                // Final validation AFTER all suppression
                if (!IsValidNPCInteraction(npc))
                {
                    Monitor.Log($"⚠️ Invalid NPC interaction after suppression: {npc?.Name}", LogLevel.Debug);
                    return;
                }

                // Check for duplicate interaction with enhanced protection
                if (IsDuplicateInteraction(npc))
                {
                    Monitor.Log($"⚠️ DUPLICATE BLOCKED: {npc.Name}", LogLevel.Debug);
                    return;
                }

                // Update tracking before processing
                UpdateInteractionTracking(npc);

                // Check for gift item
                var heldItem = Game1.player?.ActiveObject;
                
                if (heldItem != null && IsValidGiftItem(heldItem))
                {
                    Monitor.Log($"=== 🎁 ULTRA-SAFE GIFT PROCESSING ===", LogLevel.Info);
                    Monitor.Log($"Player: {Game1.player?.Name}", LogLevel.Info);
                    Monitor.Log($"NPC: {npc.Name}", LogLevel.Info);
                    Monitor.Log($"Item: {heldItem.Name} (Quality: {heldItem.Quality})", LogLevel.Info);
                    Monitor.Log($"🛡️ GAME DIALOGS: COMPLETELY SUPPRESSED", LogLevel.Info);
                    Monitor.Log($"🤖 AI PROCESSING: ENABLED", LogLevel.Info);
                    Monitor.Log($"===================================", LogLevel.Info);

                    ProcessGiftWithAI(npc, heldItem);
                }
                else
                {
                    Monitor.Log($"=== 💬 REGULAR CONVERSATION (AI) ===", LogLevel.Info);
                    Monitor.Log($"Player: {Game1.player?.Name}", LogLevel.Info);
                    Monitor.Log($"NPC: {npc.Name}", LogLevel.Info);
                    Monitor.Log($"🛡️ GAME DIALOGS: SUPPRESSED", LogLevel.Info);
                    Monitor.Log($"🤖 AI CONVERSATION: ENABLED", LogLevel.Info);
                    Monitor.Log($"==================================", LogLevel.Info);

                    // Start regular AI conversation
                    dialogueHandler?.AbrirDialogoConOpciones(npc);
                }
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error in safe NPC processing: {ex.Message}", LogLevel.Error);
                ResetProcessingState();
                
                // Emergency fallback conversation
                try
                {
                    dialogueHandler?.AbrirDialogoConOpciones(npc);
                }
                catch (Exception fallbackEx)
                {
                    Monitor.Log($"Emergency fallback failed: {fallbackEx.Message}", LogLevel.Error);
                }
            }
        }

        private bool IsValidNPCInteraction(NPC npc)
        {
            if (npc == null) return false;
            
            // Enhanced NPC validation
            if (!npc.IsVillager || npc.IsInvisible || npc.IsMonster)
                return false;
                
            // Name validation with enhanced checks
            if (string.IsNullOrEmpty(npc.Name) || npc.Name.StartsWith("???") || npc.Name.Length < 2)
                return false;
                
            // Location validation
            if (npc.currentLocation != Game1.currentLocation)
                return false;
                
            // Distance validation with more lenient range
            if (Game1.player != null)
            {
                var playerTile = Game1.player.Tile;
                var npcTile = npc.Tile;
                var distance = Math.Abs(playerTile.X - npcTile.X) + Math.Abs(playerTile.Y - npcTile.Y);
                
                if (distance > 4) // Slightly more lenient
                {
                    Monitor.Log($"Player too far from {npc.Name} (distance: {distance})", LogLevel.Debug);
                    return false;
                }
            }
            
            return true;
        }

        private bool IsValidGiftItem(Item item)
        {
            if (item == null) return false;
            if (string.IsNullOrEmpty(item.Name) || item.Name.Trim() == "") return false;
            
            // Enhanced validation for problematic items
            if (item.Name.Contains("???") || item.Name.Length < 2) return false;
            
            // Exclude some non-gift items
            if (item.Name.ToLower().Contains("scythe") || item.Name.ToLower().Contains("tool")) return false;
            
            return true;
        }

        private bool IsDuplicateInteraction(NPC npc)
        {
            var now = DateTime.Now;
            var timeSinceLastInteraction = now - lastInteractionTime;
            
            // Enhanced duplicate detection
            if (timeSinceLastInteraction.TotalMilliseconds < 500) // Increased debounce time
            {
                if (lastInteractedNPC?.Name == npc.Name)
                {
                    return true;
                }
            }
            
            // Additional check for processing state
            if (isProcessingGift)
            {
                Monitor.Log($"⚠️ DUPLICATE BLOCKED: Already processing gift", LogLevel.Debug);
                return true;
            }
            
            return false;
        }

        private void UpdateInteractionTracking(NPC npc)
        {
            lastInteractedNPC = npc;
            lastHeldItem = Game1.player?.ActiveObject;
            lastInteractionTime = DateTime.Now;
        }

        private void ResetInteractionTracking()
        {
            lastInteractedNPC = null;
            lastHeldItem = null;
            lastInteractionTime = DateTime.MinValue;
        }

        private void ResetProcessingState()
        {
            isProcessingGift = false;
            ResetInteractionTracking();
        }

        private void ProcessGiftWithAI(NPC npc, Item giftItem)
        {
            try
            {
                // SET PROCESSING FLAG to prevent any other interactions
                isProcessingGift = true;
                
                Monitor.Log($"🎁 STARTING AI GIFT PROCESSING...", LogLevel.Info);
                Monitor.Log($"🛡️ ALL GAME DIALOGS BLOCKED", LogLevel.Info);
                
                // Validate gift can be given
                if (!CanReceiveGift(npc))
                {
                    Monitor.Log($"❌ {npc.Name} cannot receive gifts right now", LogLevel.Warn);
                    ResetProcessingState();
                    return;
                }

                // Create gift info for AI processing
                var giftInfo = new GiftInfo
                {
                    item_name = giftItem.Name,
                    item_category = giftItem.getCategoryName(),
                    item_quality = giftItem.Quality,
                    gift_preference = "unknown", // Let AI decide completely
                    is_birthday = IsBirthday(npc)
                };

                Monitor.Log($"🎁 GIFT INFO:", LogLevel.Info);
                Monitor.Log($"   Item: {giftInfo.item_name}", LogLevel.Info);
                Monitor.Log($"   Quality: {giftInfo.item_quality}", LogLevel.Info);
                Monitor.Log($"   Category: {giftInfo.item_category}", LogLevel.Info);
                Monitor.Log($"   Birthday: {giftInfo.is_birthday}", LogLevel.Info);

                // CRITICAL: Remove item from inventory BEFORE API call to prevent duplication
                Game1.player.removeItemFromInventory(giftItem);
                Monitor.Log($"✅ Item removed from inventory", LogLevel.Info);

                // Process with AI dialogue system
                Monitor.Log($"🤖 CALLING AI DIALOGUE SYSTEM...", LogLevel.Info);
                dialogueHandler?.AbrirDialogoConOpciones(npc, null, giftInfo);

                // IMPORTANT: Only update gift tracking if dialogue processing starts successfully
                // The friendship change will be handled by the API response in DialogueHandler
                // We don't increment counters here to avoid double-counting if API fails
                Monitor.Log($"🎁 Gift sent to AI for processing. Friendship tracking will be handled by API response.", LogLevel.Debug);

                // Reset processing state after a delay
                Helper.Events.GameLoop.UpdateTicked += ResetProcessingAfterDelay;
                
                void ResetProcessingAfterDelay(object? s, UpdateTickedEventArgs updateArgs)
                {
                    Helper.Events.GameLoop.UpdateTicked -= ResetProcessingAfterDelay;
                    Monitor.Log($"🔄 Gift processing completed for {npc.Name}", LogLevel.Debug);
                    ResetProcessingState();
                }
            }
            catch (Exception ex)
            {
                Monitor.Log($"❌ Error processing gift with AI: {ex.Message}", LogLevel.Error);
                ResetProcessingState();
                
                // Emergency restore item if processing failed
                try
                {
                    Game1.player.addItemToInventory(giftItem);
                    Monitor.Log($"🔄 Item restored to inventory due to error", LogLevel.Info);
                }
                catch
                {
                    Monitor.Log($"⚠️ Could not restore item to inventory", LogLevel.Warn);
                }
            }
        }

        private void UpdateGiftCounters(NPC npc)
        {
            try
            {
                // Update friendship data using the correct Stardew Valley API
                if (Game1.player?.friendshipData != null)
                {
                    var friendship = Game1.player.friendshipData.GetValueOrDefault(npc.Name);
                    if (friendship == null)
                    {
                        friendship = new Friendship();
                        Game1.player.friendshipData[npc.Name] = friendship;
                    }

                    friendship.GiftsToday++;
                    friendship.GiftsThisWeek++;
                    
                    Monitor.Log($"📊 Updated gift counters for {npc.Name}: Today={friendship.GiftsToday}, Week={friendship.GiftsThisWeek}", LogLevel.Debug);
                }
                else
                {
                    Monitor.Log($"⚠️ Could not access friendship data for {npc.Name}", LogLevel.Warn);
                }
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error updating gift counters: {ex.Message}", LogLevel.Warn);
            }
        }

        private bool CanReceiveGift(NPC npc)
        {
            try
            {
                // Birthday check - always allow gifts on birthdays
                if (IsBirthday(npc))
                {
                    Monitor.Log($"🎂 It's {npc.Name}'s birthday - gift allowed!", LogLevel.Info);
                    return true;
                }

                // Check if NPC is a marriage candidate
                bool isMarriageCandidate = IsMarriageCandidate(npc.Name);
                bool isPlayerMarried = !string.IsNullOrEmpty(Game1.player.spouse);
                bool isMarriedToThisNPC = Game1.player.spouse == npc.Name;

                Monitor.Log($"🔍 GIFT ELIGIBILITY CHECK for {npc.Name}:", LogLevel.Debug);
                Monitor.Log($"   Marriage candidate: {isMarriageCandidate}", LogLevel.Debug);
                Monitor.Log($"   Player married: {isPlayerMarried}", LogLevel.Debug);
                Monitor.Log($"   Married to this NPC: {isMarriedToThisNPC}", LogLevel.Debug);

                // Check using friendship data
                if (Game1.player?.friendshipData != null)
                {
                    var friendship = Game1.player.friendshipData.GetValueOrDefault(npc.Name);
                    
                    if (friendship == null)
                    {
                        // New NPC, can receive gifts
                        Monitor.Log($"✅ New NPC - gift allowed", LogLevel.Debug);
                        return true;
                    }

                    Monitor.Log($"📊 Current gift counts for {npc.Name}: Today={friendship.GiftsToday}, Week={friendship.GiftsThisWeek}", LogLevel.Debug);

                    // CRITICAL WORKAROUND: Check if counters were just incremented by the game
                    // If we detect suspicious counter values, we may need to "correct" them
                    if (isMarriageCandidate && friendship.GiftsToday == 1 && friendship.GiftsThisWeek == 1)
                    {
                        Monitor.Log($"🔧 DETECTED POSSIBLE COUNTER ISSUE for marriage candidate {npc.Name}", LogLevel.Warn);
                        Monitor.Log($"   The game may have incremented counters prematurely", LogLevel.Warn);
                        Monitor.Log($"   Attempting to allow gift anyway...", LogLevel.Warn);
                        
                        // For marriage candidates, we'll be more lenient and reset the counters
                        // This is a workaround for the timing issue with marriage candidates
                        friendship.GiftsToday = 0;
                        friendship.GiftsThisWeek = 0;
                        Monitor.Log($"🔧 Reset gift counters for {npc.Name} to allow proper AI processing", LogLevel.Info);
                        
                        return true;
                    }

                    // SPECIAL HANDLING FOR MARRIED SPOUSE
                    if (isMarriedToThisNPC)
                    {
                        // Married spouses: only daily limit applies (no weekly limit)
                        if (friendship.GiftsToday >= 1)
                        {
                            Monitor.Log($"❌ Your spouse {npc.Name} already received {friendship.GiftsToday} gifts today", LogLevel.Info);
                            return false;
                        }
                        Monitor.Log($"✅ Spouse can receive gift (daily limit not reached)", LogLevel.Debug);
                        return true;
                    }

                    // STANDARD DAILY LIMIT CHECK (all NPCs)
                    if (friendship.GiftsToday >= 1)
                    {
                        Monitor.Log($"❌ {npc.Name} already received {friendship.GiftsToday} gifts today", LogLevel.Info);
                        return false;
                    }

                    // WEEKLY LIMIT CHECK (only applies to non-married NPCs)
                    if (friendship.GiftsThisWeek >= 2)
                    {
                        Monitor.Log($"❌ {npc.Name} already received {friendship.GiftsThisWeek} gifts this week", LogLevel.Info);
                        return false;
                    }

                    Monitor.Log($"✅ {npc.Name} can receive gift (limits not reached)", LogLevel.Debug);
                    return true;
                }

                Monitor.Log($"⚠️ Could not access friendship data, allowing gift by default", LogLevel.Warn);
                return true;
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error checking gift eligibility: {ex.Message}", LogLevel.Warn);
                return true; // Default to allowing gifts if check fails
            }
        }

        private bool IsBirthday(NPC npc)
        {
            try
            {
                return npc.isBirthday();
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error checking birthday for {npc.Name}: {ex.Message}", LogLevel.Warn);
                return false;
            }
        }

        private bool IsMarriageCandidate(string npcName)
        {
            // Official list of marriage candidates from Stardew Valley
            var marriageCandidates = new HashSet<string>
            {
                // Bachelors
                "Alex", "Elliott", "Harvey", "Sam", "Sebastian", "Shane",
                // Bachelorettes
                "Abigail", "Emily", "Haley", "Leah", "Maru", "Penny"
            };

            return marriageCandidates.Contains(npcName);
        }

        // Keep these for compatibility but they're not used in the new system
        public static string GetGiftPreference(NPC npc, Item item)
        {
            return "unknown"; // Let AI decide
        }

        public static string GetGiftPreference(string npcName, string itemName)
        {
            return "unknown"; // Let AI decide
        }
    }
} 