# Flynkle API Backend

This project contains a minimal FastAPI backend that demonstrates a few basic features.

## About

- Health check endpoint
- Chat endpoint backed by OpenAI
- Basic user management
- Users have a `plan` field with `free` as the default
- Users have an `is_admin` flag for admin access
- Usage tracking captures daily message count, tokens and file uploads
- Login updates the `last_login` timestamp
- Chat, login and message creation endpoints are rate limited

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

### Authentication

Login returns a JWT access token. Pass it in the `Authorization` header as
`Bearer <token>` when calling protected endpoints. Accounts must be active and
not suspended in order to authenticate. Excessive login attempts are rate
limited. The `/auth/logout` endpoint now invalidates the provided token and
`/auth/verify` checks that it is still valid.


## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/health` | Returns `{"status": "ok"}` |
| POST | `/api/v1/chat` | Chat with OpenAI GPT-4. Body: `{"message": "<text>", "conversation_id": "<uuid>"}`. Returns `{"response": "<reply>", "tokens": <n>}` |
| GET | `/api/v1/users` | List users with pagination and search |
| POST | `/api/v1/users` | Create a new user |
| GET | `/api/v1/users/{user_id}` | Retrieve a user by ID |
| PUT | `/api/v1/users/{user_id}` | Update a user |
| PATCH | `/api/v1/users/{user_id}` | Partially update a user |
| DELETE | `/api/v1/users/{user_id}` | Delete a user |
| GET | `/` | Returns a welcome message (not in the OpenAPI schema) |
| POST | `/api/v1/auth/login` | Login and receive access & refresh tokens |
| POST | `/api/v1/auth/logout` | Logout using token |
| POST | `/api/v1/auth/verify` | Verify token validity |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/request-reset` | Request password reset OTP |
| POST | `/api/v1/auth/reset-password` | Reset password with OTP |
| POST | `/api/v1/auth/request-verify` | Request email verification OTP |
| POST | `/api/v1/auth/verify-email` | Verify user email |
| GET | `/api/v1/users/me` | Get current user |
| PATCH | `/api/v1/users/me` | Update current user |
| DELETE | `/api/v1/users/me` | Delete current user |
| GET | `/api/v1/plans` | List available plans |
| GET | `/api/v1/user/usage` | Get usage for current user |
| POST | `/api/v1/user/upgrade` | Change user plan |
| GET | `/api/v1/conversations` | List user conversations (search with `q`) |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations/{conversation_id}` | Get conversation |
| PATCH | `/api/v1/conversations/{conversation_id}` | Update conversation |
| DELETE | `/api/v1/conversations/{conversation_id}` | Delete conversation |
| DELETE | `/api/v1/conversations` | Bulk delete conversations |
| GET | `/api/v1/conversations/{conversation_id}/messages` | List messages in conversation |
| POST | `/api/v1/conversations/{conversation_id}/messages` | Create message in conversation |
| GET | `/api/v1/messages/{message_id}` | Get message |
| PATCH | `/api/v1/messages/{message_id}` | Update message |
| DELETE | `/api/v1/messages/{message_id}` | Delete message |
| POST | `/api/v1/uploads` | Upload file |
| GET | `/api/v1/admin/users` | Admin list users |
| PATCH | `/api/v1/admin/users/{user_id}` | Admin update user |

The message routes above store conversation history. They are separate from the
`/chat` endpoint which streams a single prompt to the language model without
creating conversation records.

Plan limits restrict how many conversations a user may keep, how many messages
they can send per day and the total GPT tokens allowed each day. Exceeding
these limits returns "Upgrade required".

### User actions

`PATCH` and `DELETE` on user resources require a valid token in the
`Authorization` header (or `X-User-ID` for internal calls).

### Admin access

Set `is_admin` to `true` on a user to grant admin rights. Admin endpoints
require the `X-User-ID` header of an admin user. The old `X-Admin` header is no
longer used.

## Future Enhancements

- Replace in-memory rate limiting with Redis for horizontal scaling
- Add background job queue for long running tasks
- Implement OAuth providers for enterprise authentication
- Provide OpenAPI schemas for client code generation

