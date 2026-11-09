/*
  Warnings:

  - A unique constraint covering the columns `[npcId,playerId]` on the table `EmotionalState` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `playerId` to the `EmotionalState` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "EmotionalState_npcId_key";

-- AlterTable
ALTER TABLE "EmotionalState" ADD COLUMN     "playerId" TEXT NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "EmotionalState_npcId_playerId_key" ON "EmotionalState"("npcId", "playerId");

-- AddForeignKey
ALTER TABLE "EmotionalState" ADD CONSTRAINT "EmotionalState_playerId_fkey" FOREIGN KEY ("playerId") REFERENCES "Player"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
