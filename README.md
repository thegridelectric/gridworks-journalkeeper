# Gridworks Journal Keeper

[![PyPI](https://img.shields.io/pypi/v/gridworks-journalkeeper.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/gridworks-journalkeeper.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/gridworks-journalkeeper)][python version]
[![License](https://img.shields.io/pypi/l/gridworks-journalkeeper)][license]

[![Read the documentation at https://gridworks-journalkeeper.readthedocs.io/](https://img.shields.io/readthedocs/gridworks-journalkeeper/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/thegridelectric/gridworks-journalkeeper/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/thegridelectric/gridworks-journalkeeper/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/gridworks-journalkeeper/
[status]: https://pypi.org/project/gridworks-journalkeeper/
[python version]: https://pypi.org/project/gridworks-journalkeeper
[read the docs]: https://gridworks-journalkeeper.readthedocs.io/
[tests]: https://github.com/thegridelectric/gridworks-journalkeeper/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/thegridelectric/gridworks-journalkeeper
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

This is a repository for managing GridWorks storage of GridWorks time series data beyond the initial persistence mechanism. It is a major work in progress

Right now it is focused on setting up the simplest usable form of storing the 2023-2024 Millinocket S3 data in a postgres database.




## Dev Quick Start

### Docker database
Journalkeeper expects a PostgreSQL database. For development, we run this locally using Docker.

**Prerequisites**
  - Docker Desktop (macOS / Windows) or Docker Engine (Linux)
  Either:
    - docker compose (Compose v2), or
    - docker-compose (legacy Compose v1)

**Start the dev rabbit broker**

Follow instructions in [gridworks-base](https://github.com/thegridelectric/gridworks-base)

**Start the dev database**

From the repository root:

```
docker compose up # or docker-compose up if legacy
```

You should see logs ending with:
```
database system is ready to accept connections
```

[Note: `docker compose up -d` will run in the background if you prefer that]

The dev database is exposed on:
  - Host port: 5433
  - Database: journaldb_dev
  - User: journaldb
  - Password: journaldb
> Note: The dev container uses port 5433 to avoid conflicts with standard port 5432 in case you already have postgres running locally


Test for success:
```
psql -h localhost -p 5433 -U journaldb journaldb_dev
```
password `journaldb` 

This will bring you to the psql cli. 



### Install virtual env
```
poetry install
poetry shell
python run demo.y
```


## Production

### EC2 instance
Elastic IP 3.221.195.180, key gridworks-hybrid

Accessing locally:

```
ssh ubuntu@journaldb.electricity.works
psql -U journaldb
```

Password is in 1password, look up journaldb

Accessing remotely:

assuming you have psql on your local machine:

```
psql -h journaldb.electricity.works -U journaldb -d journaldb
```
and then enter password



[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/thegridelectric/gridworks-journalkeeper/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/thegridelectric/gridworks-journalkeeper/blob/main/LICENSE
[contributor guide]: https://github.com/thegridelectric/gridworks-journalkeeper/blob/main/CONTRIBUTING.md
