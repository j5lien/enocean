.PHONY: install test test-timing cov lint format clean

install:  ## Create .venv and install package + dev deps
	uv sync

test:
	uv run pytest

test-timing:
	./run_tests_with_timing.sh

cov:
	uv run pytest --cov=enocean --cov-report=term-missing

lint:
	uv run ruff check enocean

format:
	uv run ruff format enocean

clean:
	rm -rf .venv .pytest_cache .coverage coverage.xml htmlcov build dist *.egg-info
