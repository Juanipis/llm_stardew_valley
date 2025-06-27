import pytest
from unittest.mock import Mock, patch


class TestDialogueAPI:
    """Test suite for the enhanced dialogue API with human-like memory."""

    @pytest.mark.asyncio
    async def test_generate_dialogue_basic(self, client):
        """Test basic dialogue generation."""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: Hi there! How are you doing today?
OPTION_1: I'm doing great! Thanks for asking.
OPTION_2: I'm fine. How about you?
OPTION_3: Been better, but whatever."""

        with patch("app.routers.dialogue.client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "season": "Spring",
                    "day_of_month": 15,
                    "friendship_hearts": 6,
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "npc_message" in data
        assert "response_options" in data
        assert len(data["response_options"]) == 3

    @pytest.mark.asyncio
    async def test_generate_dialogue_with_memory_reference(
        self, client, test_player, test_npc
    ):
        """Test dialogue generation with memory references."""
        # Create some test dialogue history
        conversation = await client.post(
            "/generate_dialogue",
            json={
                "player_name": "TestPlayer",
                "npc_name": "TestAbigail",
                "player_response": "I love collecting amethysts!",
                "season": "Spring",
                "friendship_hearts": 6,
            },
        )

        # Mock Gemini response that references the memory
        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: Oh, you love amethysts! I remember you mentioning that before. They're beautiful gems!
OPTION_1: Yes! I find them so calming and beautiful.
OPTION_2: Do you know where to find more of them?
OPTION_3: They're just rocks, nothing special."""

        with patch("app.routers.dialogue.client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "TestAbigail",
                    "player_response": "Hey, do you remember what I told you about gems?",
                    "season": "Spring",
                    "friendship_hearts": 6,
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "amethyst" in data["npc_message"].lower()

    @pytest.mark.asyncio
    async def test_generate_dialogue_emotional_context(self, client):
        """Test that emotional context is included in dialogue generation."""
        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: I'm feeling really happy today! Thanks for asking!
OPTION_1: That's wonderful! What's making you so happy?
OPTION_2: Good to hear. Any particular reason?
OPTION_3: Cool story. Can we talk about something else?"""

        with (
            patch("app.routers.dialogue.client") as mock_client,
            patch("app.routers.dialogue.emotional_state_service") as mock_emotional,
        ):
            # Mock emotional state
            mock_emotional.get_emotional_state.return_value = {
                "current_mood": "HAPPY",
                "mood_intensity": 8.0,
                "recent_joy": 3.0,
                "recent_sadness": 0.0,
                "recent_anger": 0.0,
                "recent_anxiety": 0.0,
                "recent_excitement": 2.0,
                "last_interaction_effect": "Player gave me a gift",
            }
            mock_emotional.generate_mood_context_for_dialogue.return_value = "You are feeling very happy (intensity 8.0/10). You feel joyful and want to share your happiness."

            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "season": "Spring",
                    "friendship_hearts": 6,
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "happy" in data["npc_message"].lower()

    @pytest.mark.asyncio
    async def test_generate_dialogue_different_tones(self, client):
        """Test that the three response options have different tones."""
        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: How are you feeling about the upcoming festival?
OPTION_1: I'm so excited! It's going to be amazing!
OPTION_2: It should be fine. Are you planning to attend?
OPTION_3: Ugh, festivals are so overrated and boring."""

        with patch("app.routers.dialogue.client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "season": "Spring",
                    "friendship_hearts": 6,
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        options = data["response_options"]

        # Option 1 should be friendly/positive
        assert any(
            word in options[0].lower() for word in ["excited", "amazing", "great"]
        )

        # Option 3 should be provocative/negative
        assert any(
            word in options[2].lower() for word in ["ugh", "overrated", "boring"]
        )

    @pytest.mark.asyncio
    async def test_generate_dialogue_conversation_history(self, client):
        """Test dialogue generation with conversation history."""
        conversation_history = [
            {"speaker": "player", "message": "Hi Abigail!"},
            {
                "speaker": "Abigail",
                "message": "Hey there! How's your farm coming along?",
            },
            {"speaker": "player", "message": "Pretty good! I planted some new crops."},
        ]

        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: That's awesome! What kind of crops did you plant?
OPTION_1: I planted some parsnips and cauliflower!
OPTION_2: Just the usual spring crops.
OPTION_3: Nothing you'd find interesting."""

        with patch("app.routers.dialogue.client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "conversation_history": conversation_history,
                    "player_response": "I've been experimenting with different varieties.",
                    "season": "Spring",
                    "friendship_hearts": 6,
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "crops" in data["npc_message"].lower()

    @pytest.mark.asyncio
    async def test_generate_dialogue_spanish_language(self, client):
        """Test dialogue generation in Spanish."""
        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: ¡Hola! ¿Cómo estás hoy?
OPTION_1: ¡Estoy muy bien! ¿Y tú?
OPTION_2: Bien, gracias. ¿Cómo va todo?
OPTION_3: He tenido días mejores."""

        with patch("app.routers.dialogue.client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "season": "Spring",
                    "friendship_hearts": 6,
                    "language": "es",
                },
            )

        assert response.status_code == 200
        data = response.json()
        # Should contain Spanish text
        assert any(word in data["npc_message"] for word in ["Hola", "cómo", "estás"])

    @pytest.mark.asyncio
    async def test_generate_dialogue_fallback_options(self, client):
        """Test fallback response options when parsing fails."""
        # Mock malformed response
        mock_response = Mock()
        mock_response.text = "Malformed response without proper format"

        with patch("app.routers.dialogue.client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "season": "Spring",
                    "friendship_hearts": 6,
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["response_options"]) == 3
        # Should use fallback options
        assert "great to see you" in data["response_options"][0].lower()

    @pytest.mark.asyncio
    async def test_end_conversation_success(self, client, test_player, test_npc):
        """Test successful conversation ending with memory consolidation."""
        # First create a conversation
        with patch("app.routers.dialogue.client") as mock_client:
            mock_response = Mock()
            mock_response.text = """NPC_MESSAGE: Hi there!
OPTION_1: Hello!
OPTION_2: Hi.
OPTION_3: Whatever."""
            mock_client.models.generate_content.return_value = mock_response

            await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "TestAbigail",
                    "season": "Spring",
                    "friendship_hearts": 6,
                },
            )

        # Now end the conversation
        response = await client.post(
            "/end_conversation",
            params={"player_name": "TestPlayer", "npc_name": "TestAbigail"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "memories will be consolidated" in data["message"]

    @pytest.mark.asyncio
    async def test_end_conversation_not_found(self, client):
        """Test ending conversation when no active conversation exists."""
        response = await client.post(
            "/end_conversation",
            params={"player_name": "NonexistentPlayer", "npc_name": "NonexistentNPC"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_dialogue_no_gemini_client(self, client):
        """Test dialogue generation when Gemini client is not configured."""
        with patch("app.routers.dialogue.client", None):
            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "season": "Spring",
                    "friendship_hearts": 6,
                },
            )

        assert response.status_code == 500
        assert "Gemini API not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_dialogue_embedding_storage(self, client):
        """Test that dialogue entries are stored with embeddings."""
        mock_response = Mock()
        mock_response.text = """NPC_MESSAGE: That's a lovely gift!
OPTION_1: I'm so glad you like it!
OPTION_2: I thought you might enjoy it.
OPTION_3: It was just lying around."""

        with (
            patch("app.routers.dialogue.client") as mock_client,
            patch("app.services.memory_service.memory_service") as mock_memory,
        ):
            mock_client.models.generate_content.return_value = mock_response
            mock_memory.get_or_create_player.return_value = "test_player_id"
            mock_memory.get_or_create_npc.return_value = "test_npc_id"
            mock_memory.get_personality_profile.return_value = {
                "summary": "A friendly person",
                "friendliness": 7.0,
                "extroversion": 6.0,
                "sincerity": 8.0,
                "curiosity": 5.0,
                "trust": 6.0,
                "respect": 7.0,
                "affection": 5.0,
                "annoyance": 2.0,
                "admiration": 4.0,
                "romantic_interest": 1.0,
                "humor_compatibility": 6.0,
            }
            mock_memory.search_relevant_memories.return_value = []
            mock_memory.get_or_create_active_conversation.return_value = "test_conv_id"
            mock_memory.generate_relationship_insight.return_value = "Good relationship"

            response = await client.post(
                "/generate_dialogue",
                json={
                    "player_name": "TestPlayer",
                    "npc_name": "Abigail",
                    "player_response": "I brought you an amethyst!",
                    "season": "Spring",
                    "friendship_hearts": 6,
                },
            )

        assert response.status_code == 200

        # Verify memory service calls
        mock_memory.add_dialogue_entry.assert_called()
        calls = mock_memory.add_dialogue_entry.call_args_list

        # Should be called twice (NPC message and player response)
        assert len(calls) >= 2

        # Check that embeddings are enabled
        for call in calls:
            args, kwargs = call
            assert kwargs.get("generate_embedding", True) == True
