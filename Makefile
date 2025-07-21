.PHONY: install test lint format clean dev-install build

install:
	uv tool install .
	./scripts/install_ffmpeg.sh

dev-install:
	uv sync --dev
	./scripts/install_ffmpeg.sh

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=src/screenscribe --cov-report=term-missing

lint:
	uv run ruff check src/ tests/ --fix
	uv run mypy src/

format:
	uv run black src/ tests/

build:
	uv build

publish:
	uv publish

clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf dist/
	rm -rf build/
	rm -rf .uv_cache/