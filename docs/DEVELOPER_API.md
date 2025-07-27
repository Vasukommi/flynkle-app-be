# Developer API & Schema Overview

This document summarizes the planned API endpoints and database tables for the personal AI application. It is based on the high level design notes but simplified to fit the current lightweight service.

## Database Tables

### Users
- `user_id` **UUID** primary key
- `email` **TEXT** unique, nullable
- `phone_number` **TEXT** unique, nullable
- `provider` **TEXT** provider type
- `provider_id` **TEXT** provider identifier
- `password` **TEXT** hashed password (nullable)
- `is_verified` **BOOLEAN**
- `verified_at` **TIMESTAMP**
- `is_active` **BOOLEAN**
- `is_suspended` **BOOLEAN**
- `plan` **TEXT** user's subscription plan (default `"free"`)
- `created_at` **TIMESTAMP**
- `updated_at` **TIMESTAMP**
- `last_login` **TIMESTAMP**
- `profile` **JSONB** misc preferences

### Conversations
- `conversation_id` **UUID** primary key
- `user_id` **UUID** foreign key to `users`
- `title` **TEXT** optional title
- `created_at` **TIMESTAMP** when the conversation was created
- `updated_at` **TIMESTAMP** updated on each message
- `status` **TEXT** state such as `active` or `archived`

### Messages
- `message_id` **UUID** primary key
- `conversation_id` **UUID** foreign key to `conversations`
- `user_id` **UUID** foreign key to `users` (nullable for system/AI messages)
- `content` **JSONB** message body or structured data
- `timestamp` **TIMESTAMP** when the message was created
- `message_type` **TEXT** e.g. `user`, `ai`, `system`
- `metadata` **JSONB** optional extra info

### Usage
- `usage_id` **UUID** primary key
- `user_id` **UUID** foreign key to `users`
- `date` **DATE** day the usage entry applies to
- `message_count` **INT** messages sent on that day
- `token_count` **INT** optional token count
- `file_uploads` **INT** optional upload count
- `last_updated_at` **TIMESTAMP** updated when counts change

## Response Format

All endpoints return:

```json
{
  "code": 200,
  "message": "Success",
  "data": {}
}
```

Errors follow the same structure with an appropriate status code.

### Authentication

Login returns a JWT token. Include it in the `Authorization` header as
`Bearer <token>` when accessing protected routes. Only active, non-suspended
users can log in. Login is rate limited and `/auth/logout` invalidates the
token while `/auth/verify` checks it.
Message creation and `/chat` requests are also rate limited to prevent abuse.
Successful login updates the `last_login` timestamp for the user.

## API Endpoints

The current service exposes a minimal set of endpoints:

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | `/api/v1/health` | Health check |
| POST   | `/api/v1/chat`   | Chat with the AI model |
| GET    | `/api/v1/users` | List users |
| POST   | `/api/v1/users` | Create a new user |
| GET    | `/api/v1/users/{user_id}` | Retrieve a user by ID |
| PUT    | `/api/v1/users/{user_id}` | Update a user |
| PATCH  | `/api/v1/users/{user_id}` | Partially update a user |
| DELETE | `/api/v1/users/{user_id}` | Delete a user |
| POST   | `/api/v1/auth/login` | Login and receive a token |
| POST   | `/api/v1/auth/logout` | Logout using token |
| POST   | `/api/v1/auth/verify` | Verify token validity |
| GET    | `/api/v1/users/me` | Get current user |
| PATCH  | `/api/v1/users/me` | Update current user |
| DELETE | `/api/v1/users/me` | Delete current user |
| GET    | `/api/v1/plans` | List available plans |
| GET    | `/api/v1/user/usage` | Get usage for current user |
| POST   | `/api/v1/user/upgrade` | Change user plan |
| GET    | `/api/v1/conversations` | List user conversations |
| POST   | `/api/v1/conversations` | Create conversation |
| GET    | `/api/v1/conversations/{conversation_id}` | Get conversation |
| PATCH  | `/api/v1/conversations/{conversation_id}` | Update conversation |
| DELETE | `/api/v1/conversations/{conversation_id}` | Delete conversation |
| GET    | `/api/v1/conversations/{conversation_id}/messages` | List messages in conversation |
| POST   | `/api/v1/conversations/{conversation_id}/messages` | Create message in conversation |
| GET    | `/api/v1/messages/{message_id}` | Get message |
| PATCH  | `/api/v1/messages/{message_id}` | Update message |
| DELETE | `/api/v1/messages/{message_id}` | Delete message |
| GET    | `/api/v1/admin/users` | Admin list users |
| PATCH  | `/api/v1/admin/users/{user_id}` | Admin update user |

### User actions

`PATCH` and `DELETE` on user routes require authentication via the
`Authorization` header or `X-User-ID`.

This table matches the one in the main `README.md` and should be updated whenever routes change.

These tables enable conversation history and quota tracking which can be used to enforce subscription plans.
Each plan defines the maximum number of conversations a user may keep and how many messages they can send per day. Message endpoints store data in the tables while `/chat` sends a single prompt without persisting any messages.
