# Makefile for nativetoolchain-doctor

.PHONY: help install test lint format typecheck build clean verify

help:
	@echo "Available targets:"
	@echo "  install      - Install in editable mode with dev dependencies"
	@echo "  test         - Run all tests except live"
	@echo "  test-live    - Run live tests (requires Windows toolchain)"
	@echo "  lint         - Run ruff check"
	@echo "  format       - Run ruff format --check"
	@echo "  typecheck    - Run mypy"
	@echo "  build        - Build wheel"
	@echo "  verify       - Run all checks (lint, format, typecheck, test)"
	@echo "  clean        - Remove build artifacts"

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -m "not live" -q

test-live:
	python -m pytest -m live -q

lint:
	ruff check src tests

format:
	ruff format --check src tests

typecheck:
	mypy src

build:
	python -m pip wheel . --no-deps -w dist

verify: lint format typecheck test
	@echo "All checks passed"

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true