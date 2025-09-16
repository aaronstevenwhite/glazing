"""Command-line interface for the glazing package.

This module provides a comprehensive CLI for managing linguistic datasets
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

import click

from glazing.cli.download import download


@click.group()
@click.version_option()
def cli() -> None:
    """Glazing - Unified interface for linguistic datasets.

    Glazing provides automatic downloading, conversion, and search
    capabilities for FrameNet, PropBank, VerbNet, and WordNet datasets.
    """


# Register command groups
cli.add_command(download)
