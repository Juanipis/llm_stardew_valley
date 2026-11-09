-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateTable
CREATE TABLE "User" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    "hashed_password" TEXT NOT NULL,
    "api_token" TEXT,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "World" (
    "id" SERIAL NOT NULL,
    "farm_name" TEXT NOT NULL,
    "userId" INTEGER NOT NULL,

    CONSTRAINT "World_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Interaction" (
    "id" SERIAL NOT NULL,
    "npcName" TEXT NOT NULL,
    "raw_context" TEXT NOT NULL,
    "generated_dialogue" TEXT NOT NULL,
    "worldId" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Interaction_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Player" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Player_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Npc" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "location" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Npc_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PlayerPersonalityProfile" (
    "id" TEXT NOT NULL,
    "playerId" TEXT NOT NULL,
    "npcId" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "friendliness" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "extroversion" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "sincerity" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "curiosity" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "trust" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "respect" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "affection" DOUBLE PRECISION NOT NULL DEFAULT 3.0,
    "annoyance" DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    "admiration" DOUBLE PRECISION NOT NULL DEFAULT 3.0,
    "romantic_interest" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "humor_compatibility" DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PlayerPersonalityProfile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Conversation" (
    "id" TEXT NOT NULL,
    "startTime" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endTime" TIMESTAMP(3),
    "playerId" TEXT NOT NULL,
    "npcId" TEXT NOT NULL,
    "season" TEXT,
    "dayOfMonth" INTEGER,
    "dayOfWeek" INTEGER,
    "timeOfDay" INTEGER,
    "year" INTEGER,
    "weather" TEXT,
    "playerLocation" TEXT,
    "friendshipHearts" INTEGER,

    CONSTRAINT "Conversation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DialogueEntry" (
    "id" TEXT NOT NULL,
    "conversationId" TEXT NOT NULL,
    "speaker" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "embedding" vector(768),

    CONSTRAINT "DialogueEntry_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "User_api_token_key" ON "User"("api_token");

-- CreateIndex
CREATE UNIQUE INDEX "World_userId_farm_name_key" ON "World"("userId", "farm_name");

-- CreateIndex
CREATE UNIQUE INDEX "Player_name_key" ON "Player"("name");

-- CreateIndex
CREATE UNIQUE INDEX "Npc_name_key" ON "Npc"("name");

-- CreateIndex
CREATE UNIQUE INDEX "PlayerPersonalityProfile_playerId_npcId_key" ON "PlayerPersonalityProfile"("playerId", "npcId");

-- AddForeignKey
ALTER TABLE "World" ADD CONSTRAINT "World_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Interaction" ADD CONSTRAINT "Interaction_worldId_fkey" FOREIGN KEY ("worldId") REFERENCES "World"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PlayerPersonalityProfile" ADD CONSTRAINT "PlayerPersonalityProfile_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PlayerPersonalityProfile" ADD CONSTRAINT "PlayerPersonalityProfile_npcId_fkey" FOREIGN KEY ("npcId") REFERENCES "Npc"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Conversation" ADD CONSTRAINT "Conversation_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Conversation" ADD CONSTRAINT "Conversation_npcId_fkey" FOREIGN KEY ("npcId") REFERENCES "Npc"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DialogueEntry" ADD CONSTRAINT "DialogueEntry_conversationId_fkey" FOREIGN KEY ("conversationId") REFERENCES "Conversation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
