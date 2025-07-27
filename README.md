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

### Response Format

Every endpoint wraps its payload in a simple envelope:

```json
{
  "code": 200,
  "message": "Success",
  "data": {}
}
```

Errors use the same structure with an appropriate status code and message.


## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/health` | Returns `{"status": "ok"}` |
| POST | `/api/v1/chat` | Chat with OpenAI GPT-4. Body: `{"message": "<text>"}`. Returns `{"response": "<reply>"}` |
| GET | `/api/v1/users` | List users with pagination and search |
| POST | `/api/v1/users` | Create a new user |
| GET | `/api/v1/users/{user_id}` | Retrieve a user by ID |
| PUT | `/api/v1/users/{user_id}` | Update a user |
| DELETE | `/api/v1/users/{user_id}` | Delete a user |
| GET | `/` | Returns a welcome message (not in the OpenAPI schema) |
| POST | `/api/v1/auth/login` | Login placeholder |
| POST | `/api/v1/auth/logout` | Logout placeholder |
| POST | `/api/v1/auth/verify` | Verification placeholder |
| GET | `/api/v1/users/me` | Get current user |
| PATCH | `/api/v1/users/me` | Update current user |
| DELETE | `/api/v1/users/me` | Delete current user |
| GET | `/api/v1/plans` | List available plans |
| GET | `/api/v1/user/usage` | Get usage for current user |
| POST | `/api/v1/user/upgrade` | Change user plan |
| GET | `/api/v1/conversations` | List user conversations |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations/{conversation_id}` | Get conversation |
| PATCH | `/api/v1/conversations/{conversation_id}` | Update conversation |
| DELETE | `/api/v1/conversations/{conversation_id}` | Delete conversation |
| GET | `/api/v1/conversations/{conversation_id}/messages` | List messages in conversation |
| POST | `/api/v1/conversations/{conversation_id}/messages` | Create message in conversation |
| GET | `/api/v1/messages/{message_id}` | Get message |
| PATCH | `/api/v1/messages/{message_id}` | Update message |
| DELETE | `/api/v1/messages/{message_id}` | Delete message |
| GET | `/api/v1/admin/users` | Admin list users |
| PATCH | `/api/v1/admin/users/{user_id}` | Admin update user |

