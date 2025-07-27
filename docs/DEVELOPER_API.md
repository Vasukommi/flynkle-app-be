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

Future revisions may introduce conversations, messages and usage tracking to enforce plan quotas as outlined in the design document.
