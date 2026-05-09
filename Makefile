.PHONY: build dev test lint start

build:
	docker compose -f docker-compose.dev.yml build

dev:
	docker compose -f docker-compose.dev.yml up

test:
	python -m pytest tests/ -m "not slow and not azure"

lint:
	python -m ruff check shared/config.py shared/logging.py tests/test_shared_config.py
	python -m black --check shared/config.py shared/logging.py tests/test_shared_config.py
	python -m mypy shared/config.py shared/logging.py

start:
	python apps/aria/server.py
