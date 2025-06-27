-- CreateEnum
CREATE TYPE "MemoryType" AS ENUM ('GIFT_RECEIVED', 'GIFT_GIVEN', 'SHARED_ACTIVITY', 'EMOTIONAL_MOMENT', 'FAVOR_ASKED', 'FAVOR_DONE', 'CONFLICT', 'COMPLIMENT', 'INSULT', 'ROMANTIC_MOMENT', 'ACHIEVEMENT_SHARED', 'SECRET_TOLD', 'BETRAYAL', 'SUPPORT_GIVEN', 'SUPPORT_RECEIVED');

-- CreateEnum
CREATE TYPE "Mood" AS ENUM ('VERY_HAPPY', 'HAPPY', 'CONTENT', 'NEUTRAL', 'WORRIED', 'SAD', 'ANGRY', 'EXCITED', 'ROMANTIC', 'NOSTALGIC', 'STRESSED');

-- CreateEnum
CREATE TYPE "PreferenceCategory" AS ENUM ('GIFTS', 'ACTIVITIES', 'PEOPLE', 'PLACES', 'TOPICS', 'FOODS', 'SEASONS', 'WEATHER');

-- CreateEnum
CREATE TYPE "MilestoneType" AS ENUM ('FIRST_MEETING', 'FIRST_GIFT', 'FIRST_CONVERSATION', 'BECAME_FRIENDS', 'FIRST_SECRET_SHARED', 'FIRST_FAVOR', 'FIRST_CONFLICT', 'ROMANTIC_INTEREST_SPARKED', 'FIRST_DATE', 'RELATIONSHIP_OFFICIAL', 'MARRIED', 'BEST_FRIENDS', 'RIVAL_RELATIONSHIP');

-- CreateTable
CREATE TABLE "MemoryEpisode" (
    "id" TEXT NOT NULL,
    "playerId" TEXT NOT NULL,
    "npcId" TEXT NOT NULL,
    "eventType" "MemoryType" NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "emotionalImpact" DOUBLE PRECISION NOT NULL,
    "importance" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "location" TEXT,
    "season" TEXT,
    "gameDate" TEXT,
    "accessCount" INTEGER NOT NULL DEFAULT 1,
    "lastAccessed" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "decayRate" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "embedding" vector(768),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MemoryEpisode_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EmotionalState" (
    "id" TEXT NOT NULL,
    "npcId" TEXT NOT NULL,
    "currentMood" "Mood" NOT NULL DEFAULT 'NEUTRAL',
    "moodIntensity" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "recentJoy" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "recentSadness" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "recentAnger" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "recentAnxiety" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "recentExcitement" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "lastInteractionEffect" TEXT,
    "externalFactors" TEXT,
    "lastUpdated" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "EmotionalState_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PlayerPreference" (
    "id" TEXT NOT NULL,
    "playerId" TEXT NOT NULL,
    "npcId" TEXT NOT NULL,
    "category" "PreferenceCategory" NOT NULL,
    "item" TEXT NOT NULL,
    "preference" DOUBLE PRECISION NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "evidenceSource" TEXT NOT NULL,
    "lastObserved" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PlayerPreference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RelationshipMilestone" (
    "id" TEXT NOT NULL,
    "playerId" TEXT NOT NULL,
    "npcId" TEXT NOT NULL,
    "milestone" "MilestoneType" NOT NULL,
    "description" TEXT NOT NULL,
    "gameDate" TEXT,
    "heartLevel" INTEGER,
    "achieved" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "RelationshipMilestone_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "EmotionalState_npcId_key" ON "EmotionalState"("npcId");

-- CreateIndex
CREATE UNIQUE INDEX "PlayerPreference_playerId_npcId_category_item_key" ON "PlayerPreference"("playerId", "npcId", "category", "item");

-- CreateIndex
CREATE UNIQUE INDEX "RelationshipMilestone_playerId_npcId_milestone_key" ON "RelationshipMilestone"("playerId", "npcId", "milestone");

-- AddForeignKey
ALTER TABLE "MemoryEpisode" ADD CONSTRAINT "MemoryEpisode_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MemoryEpisode" ADD CONSTRAINT "MemoryEpisode_npcId_fkey" FOREIGN KEY ("npcId") REFERENCES "Npc"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EmotionalState" ADD CONSTRAINT "EmotionalState_npcId_fkey" FOREIGN KEY ("npcId") REFERENCES "Npc"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PlayerPreference" ADD CONSTRAINT "PlayerPreference_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PlayerPreference" ADD CONSTRAINT "PlayerPreference_npcId_fkey" FOREIGN KEY ("npcId") REFERENCES "Npc"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RelationshipMilestone" ADD CONSTRAINT "RelationshipMilestone_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RelationshipMilestone" ADD CONSTRAINT "RelationshipMilestone_npcId_fkey" FOREIGN KEY ("npcId") REFERENCES "Npc"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
