"""Download commands for the glazing CLI.

This module provides CLI commands for downloading linguistic datasets
from their official sources with progress tracking and error handling.

Commands
--------
download
    Download specific or all datasets.

Examples
--------
Download VerbNet:
    $ glazing download --dataset verbnet

Download all datasets:
    $ glazing download --dataset all

Download to specific directory:
    $ glazing download --dataset propbank --output-dir /path/to/data

List available datasets:
    $ glazing download --list
"""

from pathlib import Path

import click

from glazing.downloader import (
    DownloadError,
    ExtractionError,
    download_all,
    download_dataset,
    get_available_datasets,
    get_dataset_info,
)
from glazing.types import DatasetType


@click.group(name="download")
def download() -> None:
    """Download datasets from official sources.

    Downloads linguistic datasets including VerbNet, PropBank, WordNet,
    and FrameNet (manual download required) from their official sources.
    """


@download.command(name="dataset")
@click.option(
    "--dataset",
    "-d",
    type=click.Choice(["all", "verbnet", "propbank", "wordnet", "framenet"]),
    required=True,
    help="Dataset to download (all for all datasets)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    default=Path("data/raw"),
    help="Output directory for downloaded datasets",
)
@click.option(
    "--skip-manual",
    is_flag=True,
    default=True,
    help="Skip datasets requiring manual download (FrameNet)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force re-download even if dataset already exists",
)
def dataset_command(dataset: str, output_dir: str | Path, skip_manual: bool, force: bool) -> None:
    """Download a specific dataset or all datasets.

    Downloads the specified dataset(s) to the output directory.
    By default, skips datasets that require manual download.

    Parameters
    ----------
    dataset : str
        Dataset name to download ('all' for all datasets).
    output_dir : str | Path
        Output directory for downloaded datasets.
    skip_manual : bool
        Skip datasets requiring manual download (FrameNet).
    force : bool
        Force re-download even if dataset already exists.

    Examples
    --------
    Download VerbNet:
        glazing download dataset --dataset verbnet

    Download all datasets:
        glazing download dataset --dataset all --output-dir /data

    Download with force:
        glazing download dataset --dataset framenet --no-skip-manual
    """
    # Convert output_dir to Path and resolve to absolute path
    output_path = Path(output_dir).resolve()

    # Create output directory if it doesn't exist
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        click.echo(f"✗ Failed to create output directory: {e}", err=True)
        click.get_current_context().exit(1)

    if dataset == "all":
        _download_all_datasets(output_path, skip_manual)
    else:
        _download_single_dataset(dataset, output_path, force)


def _download_all_datasets(output_path: Path, skip_manual: bool) -> None:
    """Handle downloading all datasets.

    Parameters
    ----------
    output_path : Path
        Output directory path.
    skip_manual : bool
        Skip datasets requiring manual download.
    """
    click.echo(f"Downloading all datasets to: {output_path}")

    datasets_to_download: list[DatasetType] = get_available_datasets()
    if skip_manual:
        datasets_to_download = [d for d in datasets_to_download if d != "FrameNet"]

    click.echo(f"Datasets to download: {', '.join(datasets_to_download)}")

    results = download_all(output_path, datasets_to_download, skip_manual=False)

    # Report results
    success_count = 0
    failure_count = 0

    for ds_name, result in results.items():
        if isinstance(result, Path):
            click.echo(f"✓ {ds_name}: Downloaded to {result}")
            success_count += 1
        else:
            click.echo(f"✗ {ds_name}: {result}", err=True)
            failure_count += 1

    click.echo(f"\nSummary: {success_count} successful, {failure_count} failed")

    if failure_count > 0:
        click.get_current_context().exit(1)


def _download_single_dataset(dataset: str, output_path: Path, force: bool) -> None:
    """Handle downloading a single dataset.

    Parameters
    ----------
    dataset : str
        Dataset name (lowercase).
    output_path : Path
        Output directory path.
    force : bool
        Force re-download.
    """
    dataset_map = {
        "verbnet": "VerbNet",
        "propbank": "PropBank",
        "wordnet": "WordNet",
        "framenet": "FrameNet",
    }

    dataset_name: DatasetType = dataset_map[dataset]  # type: ignore[assignment]
    click.echo(f"Downloading {dataset_name} to: {output_path}")

    # Check if dataset already exists and force flag
    if not force and any(output_path.glob(f"{dataset.lower()}-*")):
        click.echo(f"Dataset {dataset_name} already exists. Use --force to re-download.")
        return

    try:
        path = download_dataset(dataset_name, output_path)
        click.echo(f"✓ {dataset_name}: Downloaded to {path}")

    except NotImplementedError as e:
        click.echo(f"Manual download required for {dataset_name}:", err=True)
        click.echo(str(e), err=True)
        click.get_current_context().exit(2)

    except (DownloadError, ExtractionError) as e:
        click.echo(f"✗ Failed to download {dataset_name}: {e}", err=True)
        click.get_current_context().exit(1)

    except (OSError, ValueError) as e:
        click.echo(f"✗ Unexpected error downloading {dataset_name}: {e}", err=True)
        click.get_current_context().exit(1)


# Export the Click command for testing
download_dataset_cmd = dataset_command


@download.command(name="list")
def list_datasets() -> None:
    """List available datasets for download.

    Shows all supported datasets with their versions and download status.
    """
    click.echo("Available datasets:")
    click.echo()

    datasets = get_available_datasets()

    for dataset in datasets:
        try:
            info = get_dataset_info(dataset)
            status = "Manual download required" if dataset == "FrameNet" else "Auto-download"

            click.echo(f"  {dataset}:")
            click.echo(f"    Version: {info['version']}")
            click.echo(f"    Status:  {status}")
            click.echo()

        except ValueError as e:
            click.echo(f"  {dataset}: Error getting info - {e}")
            click.echo()


@download.command(name="info")
@click.argument("dataset", type=click.Choice(["verbnet", "propbank", "wordnet", "framenet"]))
def dataset_info(dataset: str) -> None:
    """Get detailed information about a dataset.

    Shows version, download method, and other metadata for the specified dataset.

    Examples:
        glazing download info verbnet
        glazing download info framenet
    """
    # Map CLI names to DatasetType
    dataset_map = {
        "verbnet": "VerbNet",
        "propbank": "PropBank",
        "wordnet": "WordNet",
        "framenet": "FrameNet",
    }

    dataset_name: DatasetType = dataset_map[dataset]  # type: ignore[assignment]

    try:
        info = get_dataset_info(dataset_name)

        click.echo(f"Dataset: {info['name']}")
        click.echo(f"Version: {info['version']}")
        click.echo(f"Downloader: {info['class']}")

        if dataset_name == "FrameNet":
            click.echo("Download: Manual (license required)")
            click.echo("URL: https://framenet.icsi.berkeley.edu/fndrupal/framenet_request_data")
        else:
            click.echo("Download: Automatic")

        # Add dataset-specific information
        if dataset_name == "VerbNet":
            click.echo("Source: GitHub (uvi-nlp/verbnet)")
            click.echo("Format: XML classes with thematic roles and frames")

        elif dataset_name == "PropBank":
            click.echo("Source: GitHub (propbank/propbank-frames)")
            click.echo("Format: XML framesets with semantic roles")

        elif dataset_name == "WordNet":
            click.echo("Source: Princeton University")
            click.echo("Format: Text files with synsets and relations")

        elif dataset_name == "FrameNet":
            click.echo("Source: UC Berkeley ICSI")
            click.echo("Format: XML frames with lexical units and annotations")

    except ValueError as e:
        click.echo(f"Error getting dataset info: {e}", err=True)
        click.get_current_context().exit(1)
