"""CLI commands for searching across linguistic datasets.

This module provides commands for searching and querying converted datasets
in JSON Lines format.

Commands
--------
search query
    Search across datasets with a text query.
search entity
    Get details about a specific entity.
search role
    Search for semantic roles across datasets.
search cross-ref
    Find cross-references between datasets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from glazing.framenet.models import Frame
from glazing.propbank.models import Frameset
from glazing.search import SearchResult, UnifiedSearch
from glazing.verbnet.models import VerbClass
from glazing.wordnet.models import Synset

console = Console()

DatasetName = Literal["all", "verbnet", "propbank", "wordnet", "framenet"]


def _display_verbnet_details(entity: VerbClass) -> None:
    """Display VerbNet-specific entity details."""
    if hasattr(entity, "members"):
        console.print(f"[white]Members:[/white] {len(entity.members)}")
    if hasattr(entity, "themroles"):
        roles = ", ".join(r.type for r in entity.themroles)
        console.print(f"[white]Thematic Roles:[/white] {roles}")
    if hasattr(entity, "frames"):
        entity_frames = getattr(entity, "frames", [])
        console.print(f"[white]Frames:[/white] {len(entity_frames)}")


def _display_propbank_details(entity: Frameset) -> None:
    """Display PropBank-specific entity details."""
    if hasattr(entity, "rolesets"):
        console.print(f"[white]Rolesets:[/white] {len(entity.rolesets)}")
        for rs in entity.rolesets[:3]:  # Show first 3
            console.print(f"  • {rs.id}: {rs.name}")


def _display_wordnet_details(entity: Synset) -> None:
    """Display WordNet-specific entity details."""
    if hasattr(entity, "words"):
        entity_words = getattr(entity, "words", [])
        words = ", ".join(getattr(w, "lemma", str(w)) for w in entity_words[:5])
        console.print(f"[white]Words:[/white] {words}")
    if hasattr(entity, "definition"):
        console.print(f"[white]Definition:[/white] {entity.definition}")


def _display_framenet_details(entity: Frame) -> None:
    """Display FrameNet-specific entity details."""
    if hasattr(entity, "frame_elements"):
        console.print(f"[white]Frame Elements:[/white] {len(entity.frame_elements)}")
        for fe in entity.frame_elements[:5]:  # Show first 5
            console.print(f"  • {fe.name} ({fe.core_type})")


def _display_entity_details(
    entity: VerbClass | Frameset | Synset | Frame, entity_id: str, dataset: str
) -> None:
    """Display formatted entity details based on dataset type.

    Parameters
    ----------
    entity
        Entity object to display.
    entity_id : str
        Entity identifier.
    dataset : str
        Dataset name.
    """
    console.print(f"\n[bold cyan]{dataset.upper()} Entity Details[/bold cyan]")
    console.print(f"[white]ID:[/white] {entity_id}")

    if dataset == "verbnet" and isinstance(entity, VerbClass):
        _display_verbnet_details(entity)
    elif dataset == "propbank" and isinstance(entity, Frameset):
        _display_propbank_details(entity)
    elif dataset == "wordnet" and isinstance(entity, Synset):
        _display_wordnet_details(entity)
    elif dataset == "framenet" and isinstance(entity, Frame):
        _display_framenet_details(entity)


def _load_dataset_files(search: UnifiedSearch, data_dir: Path, dataset: str) -> None:
    """Load files for a specific dataset into the search index.

    Parameters
    ----------
    search : UnifiedSearch
        Search object to load into.
    data_dir : Path
        Directory containing JSON Lines files.
    dataset : str
        Dataset name to load.
    """
    if dataset == "verbnet":
        file = data_dir / "verbnet.jsonl"
        if file.exists():
            search.load_verbnet_from_jsonl(str(file))
    elif dataset == "propbank":
        file = data_dir / "propbank.jsonl"
        if file.exists():
            search.load_propbank_from_jsonl(str(file))
    elif dataset == "wordnet":
        # Load all WordNet files
        for pos in ["noun", "verb", "adj", "adv"]:
            synset_file = data_dir / f"synsets_{pos}.jsonl"
            index_file = data_dir / f"index_{pos}.jsonl"
            if synset_file.exists() and index_file.exists():
                search.load_wordnet_from_jsonl(str(synset_file), str(index_file), pos)
    elif dataset == "framenet":
        file = data_dir / "framenet.jsonl"
        if file.exists():
            search.load_framenet_from_jsonl(str(file))


def load_search_index(data_dir: str | Path, datasets: list[str] | None = None) -> UnifiedSearch:
    """Load search index from converted JSON Lines files.

    Parameters
    ----------
    data_dir : Path
        Directory containing converted JSON Lines files.
    datasets : list[str] | None
        List of datasets to load, or None for all.

    Returns
    -------
    UnifiedSearch
        Initialized search object.
    """
    search = UnifiedSearch()
    data_dir = Path(data_dir)  # Ensure it's a Path object

    if datasets is None:
        datasets = ["verbnet", "propbank", "wordnet", "framenet"]

    # Load each dataset's JSON Lines files
    for dataset in datasets:
        _load_dataset_files(search, data_dir, dataset)

    return search


@click.group()
def search() -> None:
    """Search across converted linguistic datasets."""


@search.command(name="query")
@click.argument("query_text")
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Directory containing converted JSON Lines files.",
)
@click.option(
    "--dataset",
    type=click.Choice(["all", "verbnet", "propbank", "wordnet", "framenet"]),
    default="all",
    help="Dataset to search in.",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of results to show.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON.",
)
def search_query(
    query_text: str,
    data_dir: str | Path,
    dataset: DatasetName,
    limit: int,
    output_json: bool,
) -> None:
    """Search across datasets with a text query.

    Examples
    --------
    Search all datasets:
        $ glazing search query "give" --data-dir output/

    Search only VerbNet:
        $ glazing search query "transfer" --data-dir output/ --dataset verbnet
    """
    try:
        # Determine which datasets to load
        datasets_to_load: list[str] | None = None if dataset == "all" else [dataset]

        # Load search index
        search_engine = load_search_index(data_dir, datasets_to_load)

        # Perform search
        results = search_engine.search(query_text)

        if output_json:
            # Output as JSON
            json_results = []
            for result in results[:limit]:
                json_results.append(
                    {
                        "dataset": result.dataset,
                        "id": result.id,
                        "type": result.type,
                        "name": result.name,
                        "description": result.description,
                        "score": result.score,
                    }
                )
            console.print(json.dumps(json_results, indent=2))
        else:
            # Output as formatted table
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            table = Table(title=f"Search Results for '{query_text}'")
            table.add_column("Dataset", style="cyan", no_wrap=True)
            table.add_column("Type", style="magenta")
            table.add_column("ID/Name", style="green")
            table.add_column("Description", style="white")
            table.add_column("Score", style="yellow")

            for result in results[:limit]:
                table.add_row(
                    result.dataset.upper(),
                    result.type,
                    f"{result.id}\n{result.name}" if result.name != result.id else result.id,
                    (
                        result.description[:80] + "..."
                        if len(result.description) > 80
                        else result.description
                    ),
                    f"{result.score:.2f}",
                )

            console.print(table)

            if len(results) > limit:
                console.print(f"\n[dim]Showing {limit} of {len(results)} results.[/dim]")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Data files not found: {e}[/red]")
        console.print(
            "[yellow]Tip: Make sure you've converted the datasets first "
            "using 'glazing convert dataset'[/yellow]"
        )
        sys.exit(1)
    except (ValueError, TypeError, RuntimeError) as e:
        console.print(f"[red]✗ Search failed: {e}[/red]")
        sys.exit(1)


@search.command(name="entity")
@click.argument("entity_id")
@click.option(
    "--dataset",
    type=click.Choice(["verbnet", "propbank", "wordnet", "framenet"]),
    required=True,
    help="Dataset the entity belongs to.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Directory containing converted JSON Lines files.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON.",
)
def get_entity(
    entity_id: str,
    dataset: str,
    data_dir: str | Path,
    output_json: bool,
) -> None:
    """Get details about a specific entity.

    Examples
    --------
    Get VerbNet class details:
        $ glazing search entity "give-13.1" --dataset verbnet --data-dir output/

    Get PropBank roleset details:
        $ glazing search entity "give.01" --dataset propbank --data-dir output/
    """
    try:
        # Load search index for specific dataset
        search_engine = load_search_index(data_dir, [dataset])

        # Get entity details
        entity = search_engine.get_entity(entity_id, dataset)

        if entity is None:
            console.print(f"[yellow]Entity '{entity_id}' not found in {dataset}.[/yellow]")
            return

        if output_json:
            # Output as JSON
            console.print(entity.model_dump_json(indent=2))
        else:
            _display_entity_details(entity, entity_id, dataset)

    except (ValueError, TypeError, RuntimeError) as e:
        console.print(f"[red]✗ Failed to get entity: {e}[/red]")
        sys.exit(1)


@search.command(name="role")
@click.argument("role_name")
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Directory containing converted JSON Lines files.",
)
@click.option(
    "--dataset",
    type=click.Choice(["all", "verbnet", "propbank", "framenet"]),
    default="all",
    help="Dataset to search in.",
)
def search_role(
    role_name: str,
    data_dir: str | Path,
    dataset: str,
) -> None:
    """Search for semantic roles across datasets.

    Examples
    --------
    Search for Agent role:
        $ glazing search role "Agent" --data-dir output/

    Search for ARG0 in PropBank:
        $ glazing search role "ARG0" --data-dir output/ --dataset propbank
    """
    try:
        # Determine which datasets to load
        datasets_to_load = ["verbnet", "propbank", "framenet"] if dataset == "all" else [dataset]

        # Load search index
        search_engine = load_search_index(data_dir, datasets_to_load)

        # Search for roles
        results = search_engine.search_semantic_roles(role_name)

        if not results:
            console.print(f"[yellow]No roles matching '{role_name}' found.[/yellow]")
            return

        # Group results by dataset
        by_dataset: dict[str, list[SearchResult]] = {}
        for result in results:
            if result.dataset not in by_dataset:
                by_dataset[result.dataset] = []
            by_dataset[result.dataset].append(result)

        # Display results
        tree = Tree(f"[bold]Semantic Roles matching '{role_name}'[/bold]")

        for ds, items in by_dataset.items():
            ds_branch = tree.add(f"[cyan]{ds.upper()}[/cyan] ({len(items)} matches)")
            for item in items[:5]:  # Show first 5 per dataset
                ds_branch.add(f"{item.id}: {item.description[:60]}...")
            if len(items) > 5:
                ds_branch.add(f"[dim]... and {len(items) - 5} more[/dim]")

        console.print(tree)

    except (ValueError, TypeError, RuntimeError) as e:
        console.print(f"[red]✗ Role search failed: {e}[/red]")
        sys.exit(1)


@search.command(name="cross-ref")
@click.option(
    "--source",
    type=click.Choice(["verbnet", "propbank", "wordnet", "framenet"]),
    required=True,
    help="Source dataset.",
)
@click.option(
    "--target",
    type=click.Choice(["verbnet", "propbank", "wordnet", "framenet"]),
    required=True,
    help="Target dataset.",
)
@click.option(
    "--id",
    "entity_id",
    required=True,
    help="Entity ID in source dataset.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Directory containing converted JSON Lines files.",
)
def find_cross_ref(
    source: str,
    target: str,
    entity_id: str,
    data_dir: str | Path,
) -> None:
    """Find cross-references between datasets.

    Examples
    --------
    Find PropBank references for VerbNet class:
        $ glazing search cross-ref --source verbnet --target propbank \
            --id "give-13.1" --data-dir output/

    Find VerbNet references for PropBank roleset:
        $ glazing search cross-ref --source propbank --target verbnet \
            --id "give.01" --data-dir output/
    """
    try:
        # Load search index
        search_engine = load_search_index(data_dir, [source, target])

        # Find cross-references
        references = search_engine.find_cross_references(entity_id, source, target)

        if not references:
            console.print(
                f"[yellow]No {target} references found for {source} entity '{entity_id}'.[/yellow]"
            )
            return

        # Display results
        table = Table(title=f"Cross-References: {source.upper()} → {target.upper()}")
        table.add_column("Source", style="cyan")
        table.add_column("Target", style="green")
        table.add_column("Type", style="magenta")
        table.add_column("Confidence", style="yellow")

        for ref in references:
            table.add_row(
                f"{source}: {entity_id}",
                f"{target}: {ref['target_id']}",
                str(ref.get("mapping_type", "direct")),
                f"{ref.get('confidence', 1.0):.2f}",
            )

        console.print(table)

    except (ValueError, TypeError, RuntimeError) as e:
        console.print(f"[red]✗ Cross-reference search failed: {e}[/red]")
        sys.exit(1)
