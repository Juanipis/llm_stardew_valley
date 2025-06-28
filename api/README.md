# StardewEchoes API

This is the backend API for the StardewEchoes mod. It uses FastAPI to generate dialogue for characters in Stardew Valley, with support for multiple LLM providers.

## ⚙️ Configuration

The application is configured through environment variables.

### 1. LLM Provider Setup

The API uses `litellm` to connect to different LLM providers. You can choose between `google`, `openai`, or `ollama`.

Create a `.env` file in the `api` directory and add the necessary variables based on your chosen provider.

**Google Gemini:**

```env
# .env
LLM_PROVIDER="google"
GEMINI_API_KEY="your-google-gemini-api-key"
# Get your key from https://aistudio.google.com/app/apikey
```

**OpenAI:**

```env
# .env
LLM_PROVIDER="openai"
OPENAI_API_KEY="your-openai-api-key"
```

**Ollama (for local models):**

Make sure you have [Ollama](https://ollama.ai/) installed and running.

```env
# .env
LLM_PROVIDER="ollama"
OLLAMA_API_BASE_URL="http://localhost:11434" # Default Ollama URL
# No API key is needed for local Ollama
```

### 2. Model Selection

You can specify which models to use for different tasks by setting environment variables in your `.env` file. If you don't set them, the application will use default values from `api/app/config.py`.

Here are some examples of how you might configure your models for each provider:

**For Google:**

```env
# .env
LLM_PROVIDER="google"
GEMINI_API_KEY="..."

# Recommended models for Google
DIALOGUE_MODEL="gemini-1.5-flash-latest"
PERSONALITY_MODEL="gemini-1.5-flash-latest"
EMOTIONAL_MODEL="gemini-1.5-flash-latest"
MEMORY_CONSOLIDATION_MODEL="gemini-1.5-flash-latest"
```

**For OpenAI:**

```env
# .env
LLM_PROVIDER="openai"
OPENAI_API_KEY="..."

# Recommended models for OpenAI
DIALOGUE_MODEL="gpt-4o"
PERSONALITY_MODEL="gpt-4o-mini"
EMOTIONAL_MODEL="gpt-4o-mini"
MEMORY_CONSOLIDATION_MODEL="gpt-4o-mini"
```

**For Ollama:**

```env
# .env
LLM_PROVIDER="ollama"
OLLAMA_API_BASE_URL="http://localhost:11434"

# Make sure you have pulled these models, e.g., `ollama pull llama3`
DIALOGUE_MODEL="llama3"
PERSONALITY_MODEL="llama3"
EMOTIONAL_MODEL="llama3"
MEMORY_CONSOLIDATION_MODEL="llama3"
```

The `LLM_PROVIDER` you set will be automatically prepended to the model names when making API calls. For example, if you set `LLM_PROVIDER="openai"` and `DIALOGUE_MODEL="gpt-4o"`, the final model string used will be `openai/gpt-4o`.

### 3. Vector Embeddings (Local)

**Important:** This project handles vector embeddings for semantic memory search **locally** using the `sentence-transformers` library. This process does not require any external API calls or environment variables.

- **Model:** `all-mpnet-base-v2`
- **Vector Dimensions:** 768
- **Note:** The database schema (`prisma/schema.prisma`) is configured for 768 dimensions. If you change the local model, ensure the new model's dimensions match the schema.

### 4. Database

This project uses Prisma with a PostgreSQL database. Set your database connection string in the `.env` file:

```env
# .env
DATABASE_URL="postgresql://user:password@localhost:5432/mydatabase"
```

## 🚀 Running the API

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation)

### Installation & Setup

1.  **Clone the repository and navigate to the `api` directory:**

    ```bash
    git clone https://github.com/your-username/llm_stardew_valley.git
    cd llm_stardew_valley/api
    ```

2.  **Install dependencies:**

    ```bash
    poetry install
    ```

3.  **Create your `.env` file** with the provider and database configurations as explained above.

4.  **Apply database migrations and generate the Prisma client:**
    ```bash
    poetry run prisma migrate dev
    poetry run prisma generate
    ```

### Start the Server

To run the FastAPI server:

```bash
poetry run uvicorn app.main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.
You can access the auto-generated API documentation at `http://127.0.0.1:8000/docs`.
