"""CLI commands for cross-reference extraction and resolution.

This module provides commands for managing cross-references between
linguistic datasets using the CrossReferenceIndex.

Commands
--------
xref resolve
    Resolve cross-references for an entity.
xref extract
    Extract cross-references from all datasets.
xref clear-cache
    Clear cached cross-references.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal

import click
from rich.console import Console
from rich.table import Table

from glazing.references.index import CrossReferenceIndex

console = Console()

DatasetName = Literal["verbnet", "propbank", "wordnet", "framenet"]


@click.group()
def xref() -> None:
    """Manage cross-references between datasets."""


@xref.command(name="resolve")
@click.argument("entity_id")
@click.option(
    "--source",
    type=click.Choice(["verbnet", "propbank", "wordnet", "framenet"]),
    required=True,
    help="Source dataset for the entity.",
)
@click.option(
    "--fuzzy",
    is_flag=True,
    help="Use fuzzy matching for entity ID.",
)
@click.option(
    "--threshold",
    type=click.FloatRange(0.0, 1.0),
    default=0.8,
    help="Minimum similarity threshold for fuzzy matching (0.0-1.0).",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Directory for caching cross-references.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON.",
)
def resolve_xref(  # noqa: PLR0913, PLR0912, C901
    entity_id: str,
    source: DatasetName,
    fuzzy: bool,
    threshold: float,
    cache_dir: str | Path | None,
    output_json: bool,
) -> None:
    """Resolve cross-references for an entity.

    Examples
    --------
    Resolve PropBank roleset references:
        $ glazing xref resolve "give.01" --source propbank

    Use fuzzy matching for typos:
        $ glazing xref resolve "giv.01" --source propbank --fuzzy

    Show output as JSON:
        $ glazing xref resolve "give-13.1" --source verbnet --json
    """
    try:
        # Convert cache_dir to Path if provided
        if cache_dir is not None:
            cache_dir = Path(cache_dir)

        # Create cross-reference index
        xref_index = CrossReferenceIndex(
            auto_extract=True,
            cache_dir=cache_dir,
            show_progress=not output_json,  # Don't show progress for JSON output
        )

        # Resolve references
        source_dataset = source  # DatasetType is a Literal, not a callable
        refs = xref_index.resolve(entity_id, source_dataset, fuzzy=fuzzy, threshold=threshold)

        if output_json:
            # Output as JSON
            console.print(json.dumps(refs, indent=2))
        else:
            # Display as formatted table
            console.print(f"\n[bold cyan]Cross-References for {source}:{entity_id}[/bold cyan]")

            # Create table for results
            table = Table(title="Resolved Cross-References")
            table.add_column("Dataset", style="cyan", no_wrap=True)
            table.add_column("Entity IDs", style="green")
            table.add_column("Confidence", style="yellow")

            # Add VerbNet references
            if refs["verbnet_classes"]:
                class_ids = ", ".join(refs["verbnet_classes"][:5])
                if len(refs["verbnet_classes"]) > 5:
                    class_ids += f" (+{len(refs['verbnet_classes']) - 5} more)"
                avg_confidence = sum(
                    refs["confidence_scores"].get(f"verbnet:{cls}", 1.0)
                    for cls in refs["verbnet_classes"]
                ) / len(refs["verbnet_classes"])
                table.add_row("VerbNet", class_ids, f"{avg_confidence:.3f}")

            # Add PropBank references
            if refs["propbank_rolesets"]:
                roleset_ids = ", ".join(refs["propbank_rolesets"][:5])
                if len(refs["propbank_rolesets"]) > 5:
                    roleset_ids += f" (+{len(refs['propbank_rolesets']) - 5} more)"
                avg_confidence = sum(
                    refs["confidence_scores"].get(f"propbank:{rs}", 1.0)
                    for rs in refs["propbank_rolesets"]
                ) / len(refs["propbank_rolesets"])
                table.add_row("PropBank", roleset_ids, f"{avg_confidence:.3f}")

            # Add FrameNet references
            if refs["framenet_frames"]:
                frame_names = ", ".join(refs["framenet_frames"][:5])
                if len(refs["framenet_frames"]) > 5:
                    frame_names += f" (+{len(refs['framenet_frames']) - 5} more)"
                avg_confidence = sum(
                    refs["confidence_scores"].get(f"framenet:{frame}", 1.0)
                    for frame in refs["framenet_frames"]
                ) / len(refs["framenet_frames"])
                table.add_row("FrameNet", frame_names, f"{avg_confidence:.3f}")

            # Add WordNet references
            if refs["wordnet_synsets"]:
                synset_ids = ", ".join(refs["wordnet_synsets"][:5])
                if len(refs["wordnet_synsets"]) > 5:
                    synset_ids += f" (+{len(refs['wordnet_synsets']) - 5} more)"
                avg_confidence = sum(
                    refs["confidence_scores"].get(f"wordnet:{syn}", 1.0)
                    for syn in refs["wordnet_synsets"]
                ) / len(refs["wordnet_synsets"])
                table.add_row("WordNet", synset_ids, f"{avg_confidence:.3f}")

            if not any(
                [
                    refs["verbnet_classes"],
                    refs["propbank_rolesets"],
                    refs["framenet_frames"],
                    refs["wordnet_synsets"],
                ]
            ):
                console.print("[yellow]No cross-references found.[/yellow]")
            else:
                console.print(table)

    except RuntimeError as e:
        console.print(f"[red]✗ Failed to resolve references: {e}[/red]")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@xref.command(name="extract")
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Directory for caching cross-references.",
)
@click.option(
    "--progress/--no-progress",
    default=True,
    help="Show progress during extraction.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force re-extraction even if cache exists.",
)
def extract_xref(
    cache_dir: str | Path | None,
    progress: bool,
    force: bool,
) -> None:
    """Extract cross-references from all datasets.

    This command loads all datasets and extracts cross-references,
    caching them for future use.

    Examples
    --------
    Extract with progress bar:
        $ glazing xref extract

    Extract to custom cache directory:
        $ glazing xref extract --cache-dir ~/.cache/glazing

    Force re-extraction:
        $ glazing xref extract --force
    """
    try:
        # Convert cache_dir to Path if provided
        if cache_dir is not None:
            cache_dir = Path(cache_dir)

        # Create cross-reference index
        xref_index = CrossReferenceIndex(
            auto_extract=False,  # We'll extract manually
            cache_dir=cache_dir,
            show_progress=progress,
        )

        # Clear cache if forcing
        if force:
            xref_index.clear_cache()
            console.print("[yellow]Cleared existing cache.[/yellow]")

        # Extract references
        xref_index.extract_all()

        console.print("[bold green]✓[/bold green] Cross-references extracted successfully.")

    except RuntimeError as e:
        console.print(f"[red]✗ Extraction failed: {e}[/red]")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@xref.command(name="clear-cache")
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Directory containing cached cross-references.",
)
@click.confirmation_option(prompt="Are you sure you want to clear the cache?")
def clear_cache(cache_dir: str | Path | None) -> None:
    """Clear cached cross-references.

    Examples
    --------
    Clear default cache:
        $ glazing xref clear-cache

    Clear custom cache directory:
        $ glazing xref clear-cache --cache-dir ~/.cache/glazing
    """
    try:
        # Convert cache_dir to Path if provided
        if cache_dir is not None:
            cache_dir = Path(cache_dir)

        # Create cross-reference index
        xref_index = CrossReferenceIndex(
            auto_extract=False,
            cache_dir=cache_dir,
            show_progress=False,
        )

        # Clear the cache
        xref_index.clear_cache()

        console.print("[bold green]✓[/bold green] Cache cleared successfully.")

    except (RuntimeError, ValueError, TypeError) as e:
        console.print(f"[red]✗ Failed to clear cache: {e}[/red]")
        sys.exit(1)
