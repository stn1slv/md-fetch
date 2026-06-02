"""
Command-line interface for mdfetch.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

import click

from mdfetch import extract
from mdfetch.exceptions import MdfetchError, UnsupportedPlatformError
from mdfetch.router import supported_domains, supported_platforms


@click.command(name="md-fetch")
@click.version_option(package_name="mdfetch", prog_name="md-fetch")
@click.argument("url", required=False)
@click.option(
    "--list-platforms",
    is_flag=True,
    default=False,
    help="List all supported platforms and exit.",
)
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
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite the output file if it already exists",
)
def main(
    url: str | None,
    list_platforms: bool,
    output: str | None,
    retries: int,
    retry_delay: float,
    force: bool,
) -> None:
    """Fetch and extract Markdown from the given URL."""
    if list_platforms:
        click.echo("Supported platforms:")
        for domain, matches_subdomains in supported_platforms():
            line = f"{domain} (and *.{domain})" if matches_subdomains else domain
            click.echo(f"  {line}")
        return

    if url is None:
        raise click.UsageError("Missing argument 'URL'.")

    if output and os.path.exists(output) and not force:
        click.secho(
            f"Error: '{output}' already exists. Use --force to overwrite.",
            err=True,
            fg="red",
        )
        sys.exit(1)
    try:
        content = extract(url, retries=retries, retry_delay=retry_delay)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            click.echo(content)
    except UnsupportedPlatformError as e:
        domain = (urlparse(e.url).hostname if e.url else None) or str(e)
        domains = ", ".join(sorted(supported_domains()))
        click.secho(
            f"Error: '{domain}' is not a supported platform.\nSupported domains: {domains}",
            err=True,
            fg="red",
        )
        sys.exit(1)
    except MdfetchError as e:
        click.secho(str(e), err=True, fg="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
