# Prompt: Project Vision for StardewEchoes

**Your Role:** You are an expert software developer and architect contributing to the "StardewEchoes" project.

**Context:** This document provides the high-level vision and core objectives for the project. Use this information to understand the project's main goals when answering questions, generating code, or making suggestions. It establishes the "why" behind the project.

---

## Project Vision

### Project Overview

This repository contains the codebase for "StardewEchoes," a Stardew Valley mod that aims to implement dynamic, LLM-powered dialogues for NPCs. Instead of relying on static, predefined dialogue lines, this mod will leverage a Large Language Model (LLM) to generate context-aware and memorable conversations, making NPC interactions feel more alive and personalized.

### Core Objective

The primary goal is to provide NPCs with dynamic, contextually relevant, and "memory-aware" dialogues. This is achieved by having the Stardew Valley mod (client) send contextual game data to a separate API server, which then interacts with an LLM and manages NPC conversation history to return a generated dialogue.
