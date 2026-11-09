import pytest
from unittest.mock import Mock, patch
from app.services.memory.emotional_state_service import emotional_state_service


class TestEmotionalStateService:
    """Test suite for the emotional state service."""

    @pytest.mark.asyncio
    async def test_get_emotional_state_default(self, test_npc):
        """Test getting default emotional state for a new NPC."""
        result = await emotional_state_service.get_emotional_state(test_npc.id)

        assert result["npc_id"] == test_npc.id
        assert result["current_mood"] == "NEUTRAL"
        assert result["mood_intensity"] == 5.0
        assert result["recent_joy"] == 0.0
        assert result["recent_sadness"] == 0.0
        assert result["recent_anger"] == 0.0

    @pytest.mark.asyncio
    async def test_update_emotional_state_friendly_interaction(self, test_npc):
        """Test emotional state update with friendly player interaction."""
        conversation_transcript = """
        Player: Hi Abigail! I brought you this beautiful amethyst!
        TestAbigail: Oh wow, thank you so much! This is amazing!
        Player: I'm so glad you like it!
        TestAbigail: You always know exactly what I love!
        """

        # Mock the LLM response for emotional analysis
        mock_response = Mock()
        mock_response.text = """{
            "new_mood": "HAPPY",
            "new_mood_intensity": 7.5,
            "joy_change": 2.0,
            "sadness_change": -0.5,
            "anger_change": -0.5,
            "anxiety_change": -0.3,
            "excitement_change": 1.5,
            "interaction_summary": "Player gave me a thoughtful gift",
            "mood_reason": "The amethyst made me really happy"
        }"""

        with patch.object(emotional_state_service, "client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            await emotional_state_service.update_emotional_state_from_interaction(
                test_npc.id, conversation_transcript, "friendly"
            )

            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_emotional_state_provocative_interaction(self, test_npc):
        """Test emotional state update with provocative player interaction."""
        conversation_transcript = """
        Player: Your hair looks stupid today.
        TestAbigail: Excuse me? That's really rude!
        Player: Whatever, I don't care.
        TestAbigail: Why are you being so mean?
        """

        # Mock the LLM response for emotional analysis
        mock_response = Mock()
        mock_response.text = """{
            "new_mood": "ANGRY",
            "new_mood_intensity": 6.5,
            "joy_change": -1.5,
            "sadness_change": 0.5,
            "anger_change": 2.0,
            "anxiety_change": 0.5,
            "excitement_change": -1.0,
            "interaction_summary": "Player was rude about my appearance",
            "mood_reason": "Their comments were hurtful and unnecessary"
        }"""

        with patch.object(emotional_state_service, "client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            await emotional_state_service.update_emotional_state_from_interaction(
                test_npc.id, conversation_transcript, "provocative"
            )

            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_emotional_state_no_client(self, test_npc):
        """Test emotional state update when Gemini client is not available."""
        with patch.object(emotional_state_service, "client", None):
            # Should not raise an error, just log warning
            await emotional_state_service.update_emotional_state_from_interaction(
                test_npc.id, "Test conversation", "neutral"
            )

    def test_generate_mood_context_happy(self):
        """Test mood context generation for happy emotional state."""
        emotional_state = {
            "current_mood": "HAPPY",
            "mood_intensity": 7.0,
            "recent_joy": 2.0,
            "recent_sadness": 0.0,
            "recent_anger": 0.0,
            "recent_anxiety": 0.0,
            "recent_excitement": 1.5,
            "last_interaction_effect": "Player gave me a thoughtful gift",
        }

        context = emotional_state_service.generate_mood_context_for_dialogue(
            emotional_state
        )

        assert "feeling good" in context.lower()
        assert "intensity 7.0/10" in context
        assert "with recent moments of happiness" in context
        assert "with bursts of excitement" in context
        assert "Player gave me a thoughtful gift" in context

    def test_generate_mood_context_angry(self):
        """Test mood context generation for angry emotional state."""
        emotional_state = {
            "current_mood": "ANGRY",
            "mood_intensity": 6.5,
            "recent_joy": 0.0,
            "recent_sadness": 0.0,
            "recent_anger": 2.5,
            "recent_anxiety": 0.5,
            "recent_excitement": 0.0,
            "last_interaction_effect": "Player was rude to me",
        }

        context = emotional_state_service.generate_mood_context_for_dialogue(
            emotional_state
        )

        assert "feeling irritated or frustrated" in context.lower()
        assert "intensity 6.5/10" in context
        assert "with some underlying frustration" in context
        assert "Player was rude to me" in context

    def test_generate_mood_context_neutral(self):
        """Test mood context generation for neutral emotional state."""
        emotional_state = {
            "current_mood": "NEUTRAL",
            "mood_intensity": 5.0,
            "recent_joy": 0.0,
            "recent_sadness": 0.0,
            "recent_anger": 0.0,
            "recent_anxiety": 0.0,
            "recent_excitement": 0.0,
            "last_interaction_effect": "",
        }

        context = emotional_state_service.generate_mood_context_for_dialogue(
            emotional_state
        )

        assert "normal, balanced mood" in context.lower()
        assert "intensity 5.0/10" in context

    def test_get_default_emotional_change_friendly(self):
        """Test default emotional changes for friendly interactions."""
        result = emotional_state_service._get_default_emotional_change("friendly")

        assert result["new_mood"] == "HAPPY"
        assert result["joy_change"] > 0
        assert result["anger_change"] < 0
        assert "friendly and kind" in result["interaction_summary"].lower()

    def test_get_default_emotional_change_provocative(self):
        """Test default emotional changes for provocative interactions."""
        result = emotional_state_service._get_default_emotional_change("provocative")

        assert result["new_mood"] == "ANGRY"
        assert result["anger_change"] > 0
        assert result["joy_change"] < 0
        assert "provocative or rude" in result["interaction_summary"].lower()

    def test_get_default_emotional_change_neutral(self):
        """Test default emotional changes for neutral interactions."""
        result = emotional_state_service._get_default_emotional_change("neutral")

        assert result["new_mood"] == "NEUTRAL"
        assert result["joy_change"] == 0
        assert result["anger_change"] == 0
        assert "normal, polite conversation" in result["interaction_summary"].lower()

    @pytest.mark.asyncio
    async def test_analyze_interaction_emotion_json_error(self, test_npc):
        """Test handling of JSON parsing errors in emotional analysis."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"

        with patch.object(emotional_state_service, "client") as mock_client:
            mock_client.models.generate_content.return_value = mock_response

            current_state = await emotional_state_service.get_emotional_state(
                test_npc.id
            )

            result = await emotional_state_service._analyze_interaction_emotion(
                "TestAbigail", "Test conversation", "friendly", current_state
            )

            # Should fall back to default emotional change
            assert result["new_mood"] == "HAPPY"  # Default for friendly
            assert "interaction_summary" in result
