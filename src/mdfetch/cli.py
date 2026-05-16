"""
Command-line interface for mdfetch.
"""

from __future__ import annotations

import sys

import click

from mdfetch import extract
from mdfetch.exceptions import MdfetchError


@click.command()
@click.argument("url")
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, dir_okay=False),
    help="Save Markdown to this file",
)
def main(url: str, output: str | None) -> None:
    """Fetch and extract Markdown from the given URL."""
    try:
        content = extract(url)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            click.echo(content)
    except MdfetchError as e:
        click.secho(str(e), err=True, fg="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
