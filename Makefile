.PHONY: install hooks test test-hardware test-linux cov lint format eep profiles clean

install:  ## Create .venv and install package + dev deps
	uv sync

hooks:  ## Install the git pre-commit hooks
	uvx pre-commit install

test:
	uv run pytest

test-hardware:  ## Tests against the real EnOcean stick configured in .env (some ask you to press a switch)
	uv run pytest hardware_tests -m hardware -vv

PY ?= 3.14
test-linux:  ## Run the test suite in a Linux container (make test-linux PY=3.10)
	docker run --rm -v "$(CURDIR)":/src:ro -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_LINK_MODE=copy \
		ghcr.io/astral-sh/uv:python$(PY)-bookworm-slim \
		sh -c 'cp -r /src /tmp/w && cd /tmp/w && rm -rf .venv && uv sync -q --locked && uv run pytest -p no:cacheprovider'

cov:
	uv run pytest --cov=enocean --cov-report=term-missing

lint:
	uv run ruff check
	uv run ruff format --check
	uv run mypy

format:
	uv run ruff format

eep:  ## Regenerate enocean/protocol/profiles/ from the official EEP specification (downloaded) and tools/eep_additions.xml
	uv run python tools/generate_eep.py
	uv run python generate_supported_profiles.py

profiles:  ## Regenerate SUPPORTED_PROFILES.md from the profiles
	uv run python generate_supported_profiles.py

clean:
	rm -rf .venv .pytest_cache .coverage coverage.xml htmlcov build dist *.egg-info
