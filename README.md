# NetVault

Cloud file storage with FastAPI backend and MinIO object storage.

## Description

API application for file storage and management with user authentication and bucket-based organization.

## Features

- User authentication with JWT tokens
- Bucket management with permission system (read, write, admin)
- Folder hierarchy
- File upload (simple and multipart)
- File operations (rename, move, delete)
- Public links for file sharing

## Requirements

- Python >= 3.13
- PostgreSQL
- Redis
- MinIO (or compatible S3 storage)

## Installation

```bash
uv sync
```

## Configuration

Create `.env` file:

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=your_password
DB_NAME=netvault

REDIS_HOST=localhost
REDIS_PORT=6379

MINIO_ENDPOINT=localhost:9000
MINIO_EXTERNAL_ENDPOINT=192.168.1.35:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

YC_POSTBOX_ACCESS_KEY=your_access_key
YC_POSTBOX_SECRET_KEY=your_secret_key
YC_POSTBOX_REGION=your_region
YC_POSTBOX_ENDPOINT=https://postbox.cloud.yandex.net
MAIL_FROM=no-reply@netvault.ru

JWT_SECRET=your_secret_key
```

## Running

```bash
uv run python -m src
```

## API Endpoints

You can find it after server startup. There will be the route in terminal for Swagger documentation (which provided by FastAPI automatically)

## Development

Run linters:

```bash
just lint
```

Run migrations:

```bash
alembic upgrade head
```