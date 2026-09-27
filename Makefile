.PHONY: install test test-linux test-timing cov lint format profiles clean

install:  ## Create .venv and install package + dev deps
	uv sync

test:
	uv run pytest

PY ?= 3.14
test-linux:  ## Run the test suite in a Linux container (make test-linux PY=3.10)
	docker run --rm -v "$(CURDIR)":/src:ro -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_LINK_MODE=copy \
		ghcr.io/astral-sh/uv:python$(PY)-bookworm-slim \
		sh -c 'cp -r /src /tmp/w && cd /tmp/w && rm -rf .venv && uv sync -q --locked && uv run pytest -p no:cacheprovider'

test-timing:
	./run_tests_with_timing.sh

cov:
	uv run pytest --cov=enocean --cov-report=term-missing

lint:
	uv run ruff check
	uv run ruff format --check
	uv run mypy

format:
	uv run ruff format

profiles:  ## Regenerate SUPPORTED_PROFILES.md from EEP.xml
	uv run python generate_supported_profiles.py

clean:
	rm -rf .venv .pytest_cache .coverage coverage.xml htmlcov build dist *.egg-info
