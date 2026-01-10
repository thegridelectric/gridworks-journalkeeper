# GridWorks JournalKeeper

[![PyPI](https://img.shields.io/pypi/v/gridworks-journalkeeper.svg)](https://pypi.org/project/gridworks-journalkeeper/)
[![Status](https://img.shields.io/pypi/status/gridworks-journalkeeper.svg)](https://pypi.org/project/gridworks-journalkeeper/)
[![Python Version](https://img.shields.io/pypi/pyversions/gridworks-journalkeeper)](https://pypi.org/project/gridworks-journalkeeper/)
[![License](https://img.shields.io/pypi/l/gridworks-journalkeeper)](https://github.com/thegridelectric/gridworks-journalkeeper/blob/main/LICENSE)

[![Read the Docs](https://img.shields.io/readthedocs/gridworks-journalkeeper/latest.svg)](https://gridworks-journalkeeper.readthedocs.io/)
[![Tests](https://github.com/thegridelectric/gridworks-journalkeeper/actions/workflows/tests.yml/badge.svg)](https://github.com/thegridelectric/gridworks-journalkeeper/actions)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

---

GridWorks JournalKeeper is responsible for **long-term storage and management of GridWorks time-series and message data**, beyond the initial persistence layer.

This repository is a **work in progress**. Current focus is on importing and managing the 2023–2024 Millinocket S3 data in a PostgreSQL database, with Alembic-managed schema migrations.

---

## Development Quick Start

### Prerequisites

* Python **3.12**
* `uv`
* `make`
* Docker / Docker Compose
* PostgreSQL client (`psql`) recommended

---

### Python environment (uv + Make)

This project uses **uv** for dependency management and a **Makefile** for workflow orchestration.

From the repository root:

```bash
make venv
make dev
pre-commit install
pre-commit migrate-config
source .venv/bin/activate
```

After changing dependencies:
```bash
make lock
make dev
```

Common commands:
```
make lint
make test
make pre-commit
```
## Runtime Dependencies (Docker)

JournalKeeper expects:
  - a running RabbitMQ broker
  - a PostgreSQL database

We run both locally using Docker.

## RabbitMQ

Follow the RabbitMQ setup instructions in [gridworks-base](https://github.com/thegridelectric/gridworks-base)

## PostgreSQL (development database)

From the repository root:
```bash
docker compose up
```
You should see logs ending with:
```
database system is ready to accept connections
```


[Note: `docker compose up -d` will run in the background if you prefer that]

The dev database is exposed on:
  - Host      `localhost`
  - Port      `5433`
  - Database  `journaldb_dev`
  - User:     `journaldb`
  - Password:  `journaldb`

  Port 5433 is used to avoid conflicts with a local PostgreSQL instance on 5432.

Test connectivity:
```
psql -h localhost -p 5433 -U journaldb journaldb_dev
```


## Database SCcema (Alembic)
Alembic is used to manage database schema migrations.

### Verify Alembic connectivity

With your dev environment active:
```bash

alembic current
```
Expected output:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
<revision_id>(head)
```

### Apply migrations

```
alembic upgrade head
```
This will:
  - 1.  Connect to `journaldb_dev`
  - 2. Create the `alembic_version` table if needed
  - 3. Apply all migrations in `alembic/versions`
  - 4. Mark the database as being at `head`

##  Publishing a Release

## Publishing a Release

JournalKeeper uses **tag-driven releases**. The version in `pyproject.toml` is the single source of truth and **must match the Git tag exactly**.

### Release checklist

1. **Update the version**

   Edit `pyproject.toml`:

   ```toml
   [project]
   version = "0.1.0"
   ```
2. **Commit and merge to `main`**

 do this through standard `branch` -> `dev` -> `main` PRs

3. **Add matching tag on main**

```
git checkout main
git pull origin main
```
This ensures:
  - tag points to the correct commit
  - the release guard `tag is on main` will pass

4. ** Create and push the tag**

Now tag **locally** on `main`:

```
git tag v0.1.0
git push origin v0.1.0
```

This triggers the Release workflow.
## Production Notes

JournalKeeper currently runs on an EC2-hosted PostgreSQL instance.

```
ssh ubuntu@journaldb.electricity.works
psql -U journaldb
```

Credentials are stored in 1Password

Remote access:


```bash
psql -h journaldb.electricity.works -U journaldb -d journaldb
```


## Contributing

This repository uses:
  - `ruff` for linting and formatting
  - `mypy` for type checking
  - `pytest` for tests
  - `pre-commit` for enforcement

Before committing:

```bash

make pre-commit
```

## License

MIT -- see [LICENSE](LICENSE)

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/thegridelectric/gridworks-journalkeeper/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/thegridelectric/gridworks-journalkeeper/blob/main/LICENSE
[contributor guide]: https://github.com/thegridelectric/gridworks-journalkeeper/blob/main/CONTRIBUTING.md
