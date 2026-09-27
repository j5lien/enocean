# Development

The development environment uses [uv](https://docs.astral.sh/uv/):

```bash
make install        # create .venv with the package and dev tools
make hooks          # install the pre-commit hooks
make test           # run the tests (no hardware needed: a pseudo-terminal stands in for the module)
make test-linux     # same, in a Linux Docker container (PY=3.10 to pick the Python version)
make test-hardware  # against a real EnOcean stick configured in .env (see .env.example), local only
make cov            # tests with coverage
make lint           # ruff (including docstrings) + mypy --strict
make docs           # serve this documentation locally
make eep            # regenerate the profiles from the official specification
```

The test suite covers every profile (structure, round trips, a snapshot of the decoding), property-based tests of the
parser, end-to-end tests of the communicators on a pseudo-terminal, and telegrams captured from real devices. The
examples of this documentation are run by the test suite.
