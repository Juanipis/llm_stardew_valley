import pytest
from unittest.mock import Mock, patch
from app.services.memory.vector_service import vector_service


class TestVectorService:
    """Test suite for the enhanced vector service."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        # Mock the Gemini client response
        mock_response = Mock()
        mock_response.embedding = Mock()
        mock_response.embedding.values = [0.1, 0.2, 0.3] * 256  # 768 dimensions

        with patch.object(vector_service, "client") as mock_client:
            mock_client.models.embed_content.return_value = mock_response

            result = await vector_service.generate_embedding("Test message")

            assert len(result) == 768
            assert all(isinstance(x, float) for x in result)
            mock_client.models.embed_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_no_client(self):
        """Test embedding generation when client is not available."""
        with patch.object(vector_service, "client", None):
            result = await vector_service.generate_embedding("Test message")
            assert result == []

    @pytest.mark.asyncio
    async def test_search_relevant_memories(
        self, test_player, test_npc, test_conversation
    ):
        """Test enhanced memory search with human-like weighting."""
        # Create test dialogue entries
        await vector_service.db.dialogueentry.create(
            data={
                "conversationId": test_conversation.id,
                "speaker": "player",
                "message": "I love amethysts! They're my favorite gem.",
                "timestamp": "2024-01-01T10:00:00Z",
            }
        )

        await vector_service.db.dialogueentry.create(
            data={
                "conversationId": test_conversation.id,
                "speaker": "TestAbigail",
                "message": "Really? I love amethysts too! We have so much in common.",
                "timestamp": "2024-01-01T10:01:00Z",
            }
        )

        # Mock embedding generation for the test
        with patch.object(vector_service, "generate_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 768

            result = await vector_service.search_relevant_memories(
                test_player.id, test_npc.id, "amethyst gems"
            )

            assert len(result) >= 1
            assert all("message" in memory for memory in result)
            assert all("relevance_score" in memory for memory in result)
            assert all("emotional_score" in memory for memory in result)

    @pytest.mark.asyncio
    async def test_emotional_impact_calculation(self):
        """Test emotional impact calculation for memories."""
        # Test positive emotional content
        positive_score = await vector_service._calculate_emotional_impact(
            "I love this amazing gift! Thank you so much!"
        )
        assert positive_score > 5.0

        # Test negative emotional content
        negative_score = await vector_service._calculate_emotional_impact(
            "I hate this terrible awful thing! It's so annoying!"
        )
        assert negative_score > 5.0  # Negative emotions are also impactful

        # Test neutral content
        neutral_score = await vector_service._calculate_emotional_impact(
            "The weather is nice today."
        )
        assert neutral_score == 5.0

    @pytest.mark.asyncio
    async def test_importance_calculation(self):
        """Test importance calculation for memories."""
        # Test important content (gifts, personal statements)
        important_memory = {
            "message": "This is my favorite gift ever! I think you're amazing.",
            "speaker": "player",
        }
        importance = await vector_service._calculate_importance(important_memory)
        assert importance > 5.0

        # Test question content
        question_memory = {
            "message": "What's your favorite season?",
            "speaker": "player",
        }
        importance = await vector_service._calculate_importance(question_memory)
        assert importance > 5.0

        # Test neutral content
        neutral_memory = {"message": "Hello there.", "speaker": "player"}
        importance = await vector_service._calculate_importance(neutral_memory)
        assert importance == 5.0

    @pytest.mark.asyncio
    async def test_fallback_text_search(self, test_player, test_npc, test_conversation):
        """Test fallback to text search when embeddings fail."""
        # Create test dialogue entries
        await vector_service.db.dialogueentry.create(
            data={
                "conversationId": test_conversation.id,
                "speaker": "player",
                "message": "Test message for fallback search",
            }
        )

        result = await vector_service._fallback_text_search(
            test_player.id, test_npc.id, "test query", 3
        )

        assert len(result) >= 1
        assert all("message" in memory for memory in result)
        assert all(memory["relevance_score"] == 5.0 for memory in result)

    @pytest.mark.asyncio
    async def test_human_weighting_application(self):
        """Test application of human-like weighting to memories."""
        mock_memories = [
            {
                "message": "I love this gift!",
                "days_ago": 1.0,
                "memory_type": "dialogue",
            },
            {"message": "Hello there", "days_ago": 7.0, "memory_type": "dialogue"},
        ]

        weighted_memories = await vector_service._apply_human_weighting(
            mock_memories,
            recency_weight=0.4,
            emotional_weight=0.4,
            importance_weight=0.2,
        )

        # Recent, emotional memory should score higher
        assert (
            weighted_memories[0]["relevance_score"]
            > weighted_memories[1]["relevance_score"]
        )
        assert all("emotional_score" in memory for memory in weighted_memories)
        assert all("importance_score" in memory for memory in weighted_memories)
        assert all("recency_score" in memory for memory in weighted_memories)
