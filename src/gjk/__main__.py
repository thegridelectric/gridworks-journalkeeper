"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """Gridworks Journal Keeper."""


if __name__ == "__main__":
    main(prog_name="gridworks-journalkeeper")  # pragma: no cover
