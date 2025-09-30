"""Command-line interface for the glazing package.

This module provides a CLI for managing linguistic datasets
including downloading, converting, searching, and information commands.

Commands
--------
download
    Download datasets from official sources.
convert
    Convert datasets to normalized JSON Lines format.
search
    Search across datasets.
info
    Get information about datasets.

Examples
--------
Download a dataset:
    $ glazing download --dataset verbnet

Download all datasets:
    $ glazing download --dataset all

Get help:
    $ glazing --help
    $ glazing download --help
"""

from pathlib import Path

import click

from glazing.__version__ import __version__
from glazing.cli.convert import convert
from glazing.cli.download import download
from glazing.cli.search import search
from glazing.cli.xref import xref
from glazing.initialize import initialize_datasets


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """Glazing - Unified interface for linguistic datasets.

    Glazing provides automatic downloading, conversion, and search
    capabilities for FrameNet, PropBank, VerbNet, and WordNet datasets.

    Examples
    --------
    Download a dataset:
        $ glazing download dataset --dataset verbnet

    Convert datasets to JSON Lines:
        $ glazing convert dataset --dataset all --input-dir data/ --output-dir output/

    Search across datasets:
        $ glazing search query "give" --data-dir output/
    """
    # Store verbose/quiet flags in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.option(
    "--data-dir",
    type=click.Path(),
    help="Directory to store datasets (default: ~/.local/share/glazing)",
)
@click.option("--force", is_flag=True, help="Force re-download even if data exists")
@click.pass_context
def init(ctx: click.Context, data_dir: str | Path | None, force: bool) -> None:
    """Download and convert all linguistic datasets for first-time setup."""
    quiet = ctx.obj.get("quiet", False)

    # Convert to Path if provided
    if data_dir is not None:
        data_dir = Path(data_dir)

    success = initialize_datasets(data_dir=data_dir, force=force, verbose=not quiet)

    if not success:
        raise click.ClickException("Failed to initialize some datasets")


# Register command groups
cli.add_command(download)
cli.add_command(convert)
cli.add_command(search)
cli.add_command(xref)
