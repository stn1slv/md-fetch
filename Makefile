.PHONY: setup test integration lint format build clean upgrade-deps

setup:
	uv sync --all-extras

test:
	uv run pytest tests/unit/

integration:
	uv run pytest tests/integration/ --override-ini=addopts=

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

build:
	uv build

clean:
	rm -rf dist/ __pycache__ src/mdfetch/__pycache__ .ruff_cache .pytest_cache

upgrade-deps:
	uv sync --all-extras --upgrade
