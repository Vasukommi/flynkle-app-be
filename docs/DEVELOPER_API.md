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
| DELETE | `/api/v1/users/{user_id}` | Delete a user |

This table matches the one in the main `README.md` and should be updated whenever routes change.

These tables enable conversation history and quota tracking which can be used to enforce subscription plans.
