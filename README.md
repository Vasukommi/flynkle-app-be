# Flynkle API Backend

This project contains a minimal FastAPI backend. The service exposes a single health check endpoint and can be run in Docker.

## Running with Docker Compose

The project includes a `docker-compose.yml` that starts the API together with
Redis, MinIO, Qdrant and Postgres. Build and start the stack with:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Environment variables

Copy `.env.example` to `.env` and fill in the values. To enable the chat
endpoint you must provide a valid `OPENAI_API_KEY`.

### Database migrations

Alembic is configured for database migrations. Create a revision with:

```bash
alembic revision --autogenerate -m "message"
```

Apply migrations with:

```bash
alembic upgrade head
```

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/health` | Returns `{"status": "ok"}` |
| POST | `/api/v1/chat` | Chat with OpenAI GPT-4 |

A root endpoint (`/`) is also available which returns a welcome message but is not included in the OpenAPI schema.
