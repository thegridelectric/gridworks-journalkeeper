# Gridworks Persister

[![PyPI](https://img.shields.io/pypi/v/gridworks-persister.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/gridworks-persister.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/gridworks-persister)][python version]
[![License](https://img.shields.io/pypi/l/gridworks-persister)][license]

[![Read the documentation at https://gridworks-persister.readthedocs.io/](https://img.shields.io/readthedocs/gridworks-persister/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/thegridelectric/gridworks-persister/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/thegridelectric/gridworks-persister/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/gridworks-persister/
[status]: https://pypi.org/project/gridworks-persister/
[python version]: https://pypi.org/project/gridworks-persister
[read the docs]: https://gridworks-persister.readthedocs.io/
[tests]: https://github.com/thegridelectric/gridworks-persister/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/thegridelectric/gridworks-persister
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

This is a repository for managing GridWorks storage of GridWorks time series data beyond the initial persistence mechanism. It is a major work in progress

Right now it is focused on setting up the simplest usable form of storing the 2023-2024 Millinocket S3 data in a postgres database.

## journaldb

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



## Features

- TODO

## Requirements

- TODO

## Installation

You can install _Gridworks Persister_ via [pip] from [PyPI]:

```console
$ pip install gridworks-persister
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Gridworks Persister_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/thegridelectric/gridworks-persister/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/thegridelectric/gridworks-persister/blob/main/LICENSE
[contributor guide]: https://github.com/thegridelectric/gridworks-persister/blob/main/CONTRIBUTING.md
