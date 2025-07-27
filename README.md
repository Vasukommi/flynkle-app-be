# Flynkle API Backend

This project contains a minimal FastAPI backend that demonstrates a few basic features.

## About

- Health check endpoint
- Chat endpoint backed by OpenAI
- Basic user management
- Users have a `plan` field with `free` as the default

The aim of the project is to stay lightweight and easy to extend.

## Running with Docker Compose

The project includes a `docker-compose.yml` that starts the API together with
Redis, MinIO, Qdrant and Postgres. Build the stack once and start it with:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

With the default setup the source code is mounted into the container and
Uvicorn runs in reload mode. This means you do **not** need to rebuild the
Docker image when making code changes. Rebuild only when you add new Python
dependencies.

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
| POST | `/api/v1/chat` | Chat with OpenAI GPT-4. Body: `{"message": "<text>"}`. Returns `{"response": "<reply>"}` |
| GET | `/api/v1/users` | List users with pagination and search |
| POST | `/api/v1/users` | Create a new user |
| GET | `/api/v1/users/{user_id}` | Retrieve a user by ID |
| PUT | `/api/v1/users/{user_id}` | Update a user |
| DELETE | `/api/v1/users/{user_id}` | Soft delete a user |
| GET | `/` | Returns a welcome message (not in the OpenAPI schema) |

