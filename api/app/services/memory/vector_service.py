import logging
from typing import List, Dict, Any, Optional

from app.db import db
from app.config import settings

logger = logging.getLogger(__name__)

# Local embedding service implementation
try:
    from sentence_transformers import SentenceTransformer
    import torch

    class LocalEmbeddingService:
        def __init__(self):
            self.model_name = settings.embedding_model
            self._model = None
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(
                f"LocalEmbeddingService initialized with device: {self._device}"
            )

        def _load_model(self):
            if self._model is None:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name, device=self._device)
                logger.info(f"Model loaded successfully on {self._device}")

        def generate_embedding(self, text: str) -> List[float]:
            try:
                if not text or not text.strip():
                    logger.warning("Empty text provided for embedding")
                    return []

                self._load_model()
                if self._model is None:
                    logger.error("Model not available for embedding generation")
                    return []

                logger.debug(f"Generating local embedding for text: {text[:100]}...")
                embedding = self._model.encode(text, convert_to_tensor=False)

                if hasattr(embedding, "tolist"):
                    embedding = embedding.tolist()

                logger.debug(
                    f"Generated local embedding with {len(embedding)} dimensions"
                )
                return embedding

            except Exception as e:
                logger.error(f"Error generating local embedding: {e}")
                return []

    local_embedding_service = LocalEmbeddingService()

except ImportError as e:
    logger.warning(f"sentence-transformers not available ({e}), will use LiteLLM only")
    local_embedding_service = None


class VectorService:
    """
    Service for generating embeddings and performing vector-based memory search.
    This service now exclusively uses a local sentence-transformer model.
    """

    def __init__(self):
        pass

    async def generate_embedding(self, text: str) -> List[float]:
        """Generates an embedding for a text using the local embedding service."""
        try:
            if local_embedding_service:
                embedding = local_embedding_service.generate_embedding(text)
                if embedding:
                    return embedding

            logger.warning(
                "Local embedding service not available or failed to generate embedding."
            )
            return []

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def search_relevant_memories(
        self,
        player_id: str,
        npc_id: str,
        query_text: str,
        memory_types: Optional[List[str]] = None,
        recency_weight: float = 0.3,
        emotional_weight: float = 0.4,
        importance_weight: float = 0.3,
        max_memories: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Enhanced memory search that mimics human memory recall.

        Considers:
        - Semantic similarity (via embeddings)
        - Emotional importance
        - Recency
        - Access frequency
        - Memory type relevance
        """
        if max_memories is None:
            max_memories = settings.max_relevant_memories
            
        logger.debug(
            f"Searching memories for player {player_id} and NPC {npc_id} with query: '{query_text}'"
        )

        try:
            # Generate embedding for the query
            query_embedding = await self.generate_embedding(query_text)

            if not query_embedding:
                # Fallback to simple text search if embeddings fail
                return await self._fallback_text_search(
                    player_id, npc_id, query_text, max_memories
                )

            # For now, use the existing dialogue-based search with enhanced weighting
            # TODO: Once MemoryEpisode model is implemented, search both dialogue and episodes
            dialogue_memories = await self._search_dialogue_memories(
                player_id, npc_id, query_embedding, max_memories
            )

            # Apply human-like weighting
            weighted_memories = await self._apply_human_weighting(
                dialogue_memories, recency_weight, emotional_weight, importance_weight
            )

            # Sort by combined relevance score and return top results
            sorted_memories = sorted(
                weighted_memories,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True,
            )

            logger.debug(
                f"Returning {len(sorted_memories[:max_memories])} weighted memories"
            )
            return sorted_memories[:max_memories]

        except Exception as e:
            logger.error(f"Error in enhanced memory search: {e}")
            return await self._fallback_text_search(
                player_id, npc_id, query_text, max_memories
            )

    async def _search_dialogue_memories(
        self,
        player_id: str,
        npc_id: str,
        query_embedding: List[float],
        max_memories: int,
    ) -> List[Dict[str, Any]]:
        """Search dialogue entries using vector similarity."""
        try:
            embedding_vector = f"[{','.join(map(str, query_embedding))}]"

            # Use raw SQL for vector similarity search with pgvector
            query = """
            SELECT
                de.id,
                de.message,
                de.speaker,
                de.timestamp,
                de."conversationId" as "conversationId",
                c.season,
                c."playerLocation" as location,
                c."friendshipHearts" as friendship_hearts,
                EXTRACT(EPOCH FROM (NOW() - de.timestamp)) / 86400 as days_ago,
                de.embedding <-> $1::vector as distance
            FROM "DialogueEntry" de
            JOIN "Conversation" c ON de."conversationId" = c.id
            WHERE c."playerId" = $2 AND c."npcId" = $3 AND de.embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT $4
            """

            result = await db.query_raw(
                query, embedding_vector, player_id, npc_id, max_memories
            )

            memories = []
            for row in result:
                memory = {
                    "id": row["id"],
                    "message": row["message"],
                    "speaker": row["speaker"],
                    "timestamp": row["timestamp"],
                    "conversation_id": row["conversationId"],
                    "season": row["season"],
                    "location": row["location"],
                    "friendship_hearts": row["friendship_hearts"],
                    "days_ago": float(row["days_ago"]) if row["days_ago"] else 0,
                    "distance": float(row["distance"]) if row["distance"] else 1.0,
                    "memory_type": "dialogue",
                }
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"Error searching dialogue memories: {e}")
            return []

    async def _apply_human_weighting(
        self,
        memories: List[Dict[str, Any]],
        recency_weight: float,
        emotional_weight: float,
        importance_weight: float,
    ) -> List[Dict[str, Any]]:
        """Apply human-like memory weighting to memories."""

        for memory in memories:
            # Semantic Similarity Score (from vector distance)
            distance = memory.get("distance", 1.0)
            similarity_score = max(0, 10 * (1 - distance))  # Scale to 0-10

            # Recency Score (more recent = higher score)
            days_ago = memory.get("days_ago", 0)
            recency_score = max(0, 10 - (days_ago / 7))  # Decreases over weeks

            # Emotional Score (detect emotional content)
            emotional_score = await self._calculate_emotional_impact(memory["message"])

            # Importance Score (based on content analysis)
            importance_score = await self._calculate_importance(memory)

            # Combined relevance score
            relevance_score = (
                similarity_score
                * (
                    1 - recency_weight - emotional_weight - importance_weight
                )  # Weight for similarity
                + recency_score * recency_weight
                + emotional_score * emotional_weight
                + importance_score * importance_weight
            )

            memory["relevance_score"] = relevance_score
            memory["recency_score"] = recency_score
            memory["emotional_score"] = emotional_score
            memory["importance_score"] = importance_score

        return memories

    async def _calculate_emotional_impact(self, message: str) -> float:
        """
        Calculate emotional impact of a message (0-10) using a keyword-based heuristic.
        This is a non-LLM implementation to reduce costs and latency.
        """
        if not message or not message.strip():
            return 5.0  # Neutral

        message_lower = message.lower()

        # Simple keyword-based check for emotional words
        positive_words = [
            "love",
            "amazing",
            "happy",
            "great",
            "thanks",
            "beautiful",
            "wonderful",
            "excited",
        ]
        negative_words = [
            "hate",
            "terrible",
            "sad",
            "angry",
            "awful",
            "cry",
            "pain",
            "disappointed",
        ]

        intensity = 5.0
        if any(word in message_lower for word in positive_words):
            intensity += 2.5

        if any(word in message_lower for word in negative_words):
            intensity += 2.5  # Negative emotions are also intense

        return min(10.0, intensity)

    async def _calculate_importance(self, memory: Dict[str, Any]) -> float:
        """Calculate importance of a memory (0-10)."""
        importance = 5.0  # Base importance

        message = memory["message"].lower()

        # Important events/topics
        if any(
            word in message
            for word in ["gift", "birthday", "festival", "secret", "help"]
        ):
            importance += 2.0

        # Questions are often important for learning about the player
        if "?" in memory["message"]:
            importance += 1.0

        # First-person statements are often more personal/important
        if any(
            phrase in message
            for phrase in ["i think", "i feel", "i love", "i hate", "my"]
        ):
            importance += 1.5

        return min(10.0, importance)

    async def _fallback_text_search(
        self, player_id: str, npc_id: str, query_text: str, max_memories: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fallback to simple recent dialogue search if vector search fails."""
        if max_memories is None:
            max_memories = settings.max_relevant_memories
            
        logger.debug("Using fallback text search for memories")

        try:
            dialogue_entries = await db.dialogueentry.find_many(
                where={
                    "conversation": {
                        "is": {
                            "playerId": player_id,
                            "npcId": npc_id,
                        }
                    }
                },
                order={"timestamp": "desc"},
                take=max_memories,
                include={"conversation": True},
            )

            return [
                {
                    "message": entry.message,
                    "speaker": entry.speaker,
                    "timestamp": entry.timestamp,
                    "conversation_id": entry.conversation.id,
                    "memory_type": "dialogue",
                    "relevance_score": 5.0,  # Default score
                }
                for entry in dialogue_entries
            ]
        except Exception as e:
            logger.error(f"Error in fallback text search: {e}")
            return []


vector_service = VectorService()
