# StardewEchoes API

This is the backend API for the StardewEchoes mod. It uses FastAPI, Prisma, and Google Gemini to generate dialogue for characters in Stardew Valley.

## Setup

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management.

### Installation

1.  **Clone the repository and navigate to the `api` directory:**

    ```bash
    git clone https://github.com/your-username/llm_stardew_valley.git
    cd llm_stardew_valley/api
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    poetry install
    ```

3.  **Set up your environment variables:**

    Create a `.env` file in the `api` directory by copying the example file:

    ```bash
    cp .env.example .env
    ```

    Now, open the `.env` file and add your `GEMINI_API_KEY` and your `DATABASE_URL` for Prisma.

4.  **Generate the Prisma client:**

    ```bash
    poetry run prisma generate
    ```

    This command reads your `prisma/schema.prisma` file and generates the Python client code necessary to interact with your database.

## Running the Server

To run the FastAPI server, use the following command:

```bash
poetry run uvicorn app.main:app --reload
```

The server will be available at `http://127.0.0.1:8000`. The `--reload` flag will automatically restart the server whenever you make changes to the code.

You can now access the API documentation at `http://127.0.0.1:8000/docs`.
