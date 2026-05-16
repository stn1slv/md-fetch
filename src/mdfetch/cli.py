"""
Command-line interface for mdfetch.
"""

from __future__ import annotations

import sys

import click

from mdfetch import extract
from mdfetch.exceptions import MdfetchError


@click.command(name="mdfetch")
@click.version_option(package_name="mdfetch", prog_name="mdfetch")
@click.argument("url")
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, dir_okay=False),
    help="Save Markdown to this file",
)
@click.option(
    "--retries",
    type=click.IntRange(min=1),
    default=3,
    show_default=True,
    help="Total number of fetch attempts on transient errors",
)
@click.option(
    "--retry-delay",
    type=click.FloatRange(min=0),
    default=2.0,
    show_default=True,
    help="Seconds to wait between retry attempts",
)
def main(url: str, output: str | None, retries: int, retry_delay: float) -> None:
    """Fetch and extract Markdown from the given URL."""
    try:
        content = extract(url, retries=retries, retry_delay=retry_delay)

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
