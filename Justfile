# Directory for source code
SOURCE_DIR := "src"

# Default command: list available commands
default:
    @just --list

# Environment variables file
set dotenv-filename := ".env"

# Run all checks: linters and formatting validation
lint: ruff-check

# --- Dependency Management ---

# Update project dependencies
[group('dependencies')]
update:
    uv sync --upgrade

# Sync project dependencies
[group('dependencies')]
sync:
    uv sync

# --- Linters and Formatting ---

# Automatically format code
[group('linters')]
ruff-format:
    uv run ruff check --fix --unsafe-fixes {{ SOURCE_DIR }}
    uv run ruff format .

# Lint code using Ruff
[group('linters')]
ruff-check:
    uv run ruff check {{ SOURCE_DIR }}

run-server:
    uv run python -m src.main server

run-cli:
    uv run python -m src.main interactive
