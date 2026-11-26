# Contributing to AttackMate API Server

Everyone taking part follows the [Code of Conduct](https://github.com/ait-testbed/attackmate-api-server/blob/main/CODE_OF_CONDUCT.md).
For security issues, see [SECURITY.md](https://github.com/ait-testbed/attackmate-api-server/blob/main/SECURITY.md).

## Branches

* `main`: target for all PRs
* Feature branches: `feat/<name>`, bugfix branches: `fix/<name>`, created from `main`

## Workflow

1. Open or pick an issue.
2. Branch from `main`.
3. Set up the dev environment:

   ```bash
   uv sync --dev
   uv run --dev prek install
   ```

4. Make your change, add tests.
5. Run the checks:

   ```bash
   uv run --dev prek run -a
   uv run --dev pytest
   ```

6. Open a PR against `main` and fill in the PR template.

## Releases

1. Bump `__version__` in `src/attackmate_api_server/metadata.py`.
2. Create a GitHub release with the tag `v<version>`. The publish workflow uploads the package to PyPI and fails if the tag does not match the version.
