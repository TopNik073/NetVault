SOURCE_PATH := "src"
TESTS_PATH := "tests"

default:
    @just --list

upgrade:
    uv lock --upgrade

format:
    uv run ruff format {{ SOURCE_PATH }}

lint:
    uv run ruff check {{ SOURCE_PATH }}

mypy:
    uv run python -m mypy --pretty {{ SOURCE_PATH }}

fix:
    uv run ruff check --fix --unsafe-fixes {{ SOURCE_PATH }}

tests:
    uv run pytest \
        --cov=def_form \
        --cov-report=lcov:tests.lcov \
        --cov-report=term \
        tests/
