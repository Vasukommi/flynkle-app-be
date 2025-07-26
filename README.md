# Flynkle API Backend

This project contains a minimal FastAPI backend. The service exposes a single health check endpoint and can be run in Docker.

## Running with Docker

```bash
docker build -t flynkle-api .
docker run -p 8000:8000 flynkle-api
```

The API will be available at `http://localhost:8000`.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/health` | Returns `{"status": "ok"}` |

A root endpoint (`/`) is also available which returns a welcome message but is not included in the OpenAPI schema.
