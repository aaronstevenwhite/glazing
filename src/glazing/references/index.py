"""Cross-reference index with automatic extraction.

This module provides an ergonomic interface for cross-reference extraction
and resolution with automatic caching and fuzzy matching support.

Classes
-------
CrossReferenceIndex
    Automatic cross-reference extraction and resolution.
ResolvedReferences
    Container for resolved cross-references.

Functions
---------
get_default_index
    Get or create the default global index.
"""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from glazing.framenet.loader import FrameNetLoader
from glazing.propbank.loader import PropBankLoader
from glazing.references.extractor import ReferenceExtractor
from glazing.references.models import CrossReference
from glazing.references.resolver import ReferenceResolver
from glazing.types import DatasetType
from glazing.utils.fuzzy_match import find_best_match
from glazing.verbnet.loader import VerbNetLoader
from glazing.wordnet.loader import WordNetLoader
from glazing.wordnet.models import Sense

if TYPE_CHECKING:
    pass


console = Console()


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:  # noqa: ANN401
        """Serialize datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class ResolvedReferences(TypedDict):
    """Container for resolved cross-references.

    Attributes
    ----------
    source_dataset : DatasetType
        Source dataset name.
    source_id : str
        Source entity ID.
    verbnet_classes : list[str]
        Related VerbNet class IDs.
    propbank_rolesets : list[str]
        Related PropBank roleset IDs.
    framenet_frames : list[str]
        Related FrameNet frame names.
    wordnet_synsets : list[str]
        Related WordNet synset IDs.
    confidence_scores : dict[str, float]
        Confidence scores for each mapping.
    """

    source_dataset: DatasetType
    source_id: str
    verbnet_classes: list[str]
    propbank_rolesets: list[str]
    framenet_frames: list[str]
    wordnet_synsets: list[str]
    confidence_scores: dict[str, float]


class CrossReferenceIndex:
    """Automatic cross-reference extraction and resolution.

    This class provides an ergonomic interface for working with cross-references
    between linguistic datasets. It automatically extracts references on first
    use and caches them for performance.

    Parameters
    ----------
    auto_extract : bool, default=True
        Whether to automatically extract references on first use.
    cache_dir : Path | None, default=None
        Directory for caching extracted references.
    show_progress : bool, default=True
        Whether to show progress during extraction.

    Attributes
    ----------
    extractor : ReferenceExtractor
        The underlying reference extractor.
    resolver : ReferenceResolver
        The reference resolver.
    is_extracted : bool
        Whether references have been extracted.

    Methods
    -------
    extract_all()
        Extract references from all datasets.
    resolve(entity_id, source, fuzzy)
        Resolve cross-references for an entity.
    find_mappings(source_id, source_dataset, target_dataset)
        Find direct mappings between datasets.
    clear_cache()
        Clear the cached references.

    Examples
    --------
    >>> xref = CrossReferenceIndex()
    >>> refs = xref.resolve("give.01", source="propbank")
    >>> print(refs["verbnet_classes"])
    ['give-13.1']
    """

    def __init__(
        self,
        auto_extract: bool = True,
        cache_dir: Path | None = None,
        show_progress: bool = True,
    ) -> None:
        """Initialize the cross-reference index."""
        self.extractor = ReferenceExtractor()
        self.resolver: ReferenceResolver | None = None
        self.is_extracted = False
        self.auto_extract = auto_extract
        self.show_progress = show_progress

        # Set cache directory
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "glazing" / "xrefs"
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "xref_index.json"

        # Load from cache if available
        if self.cache_file.exists():
            self._load_from_cache()
        elif auto_extract:
            self.extract_all()

    def extract_all(self) -> None:
        """Extract references from all datasets.

        This method loads all datasets and extracts cross-references.
        Results are cached for future use.
        """
        if self.is_extracted:
            return

        if self.show_progress:
            console.print("[bold cyan]Extracting cross-references...[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=not self.show_progress,
        ) as progress:
            # Load VerbNet
            task = progress.add_task("Loading VerbNet...", total=None)
            vn_loader = VerbNetLoader()
            verb_classes = list(vn_loader.classes.values()) if vn_loader.classes else []
            progress.update(task, completed=1)

            # Load PropBank
            task = progress.add_task("Loading PropBank...", total=None)
            pb_loader = PropBankLoader()
            framesets = list(pb_loader.framesets.values()) if pb_loader.framesets else []
            progress.update(task, completed=1)

            # Load FrameNet
            task = progress.add_task("Loading FrameNet...", total=None)
            fn_loader = FrameNetLoader()
            frames = fn_loader.frames if fn_loader.frames else []
            progress.update(task, completed=1)

            # Load WordNet
            task = progress.add_task("Loading WordNet...", total=None)
            wn_loader = WordNetLoader()
            synsets = list(wn_loader.synsets.values()) if wn_loader.synsets else []
            # WordNet doesn't have a senses property, skip it
            senses: list[Sense] = []
            progress.update(task, completed=1)

            # Extract references
            task = progress.add_task("Extracting references...", total=None)
            self.extractor.extract_all(
                framenet=frames,
                propbank=framesets,
                verbnet=verb_classes,
                wordnet=(synsets, senses) if synsets and senses else None,
            )
            progress.update(task, completed=1)

        # Create resolver
        self.resolver = ReferenceResolver(self.extractor.mapping_index)
        self.is_extracted = True

        # Cache the extracted references
        self._save_to_cache()

        if self.show_progress:
            console.print("[bold green]✓[/bold green] Cross-references extracted successfully")

    def resolve(
        self,
        entity_id: str,
        source: DatasetType,
        fuzzy: bool = False,
        threshold: float = 0.8,
    ) -> ResolvedReferences:
        """Resolve cross-references for an entity.

        Parameters
        ----------
        entity_id : str
            Entity identifier.
        source : DatasetType
            Source dataset name.
        fuzzy : bool, default=False
            Whether to use fuzzy matching for entity ID.
        threshold : float, default=0.8
            Fuzzy matching threshold.

        Returns
        -------
        ResolvedReferences
            Resolved cross-references with confidence scores.

        Examples
        --------
        >>> xref.resolve("give.01", source="propbank")
        {'verbnet_classes': ['give-13.1'], ...}
        >>> xref.resolve("giv.01", source="propbank", fuzzy=True)
        {'verbnet_classes': ['give-13.1'], ...}
        """
        # Ensure references are extracted
        if not self.is_extracted:
            if self.auto_extract:
                self.extract_all()
            else:
                msg = "References not extracted. Call extract_all() first or set auto_extract=True"
                raise RuntimeError(msg)

        # Handle fuzzy matching if requested
        if fuzzy:
            # Note: threshold parameter kept in public API for future use
            _ = threshold  # Currently unused
            entity_id = self._fuzzy_resolve_entity_id(entity_id, source)

        # Get direct mappings
        mappings = self.extractor.get_mappings_for_entity(entity_id, source)

        # Organize by target dataset - use sets to avoid duplicates
        verbnet_classes = set()
        propbank_rolesets = set()
        framenet_frames = set()
        wordnet_synsets = set()
        confidence_scores: dict[str, float] = {}

        for mapping in mappings:
            target_ids = (
                mapping.target_id if isinstance(mapping.target_id, list) else [mapping.target_id]
            )
            confidence = mapping.confidence.score if mapping.confidence else 1.0

            for target_id in target_ids:
                if mapping.target_dataset == "verbnet":
                    verbnet_classes.add(target_id)
                    # Keep the highest confidence score if we see the same mapping multiple times
                    key = f"verbnet:{target_id}"
                    confidence_scores[key] = max(confidence_scores.get(key, 0), confidence)
                elif mapping.target_dataset == "propbank":
                    propbank_rolesets.add(target_id)
                    key = f"propbank:{target_id}"
                    confidence_scores[key] = max(confidence_scores.get(key, 0), confidence)
                elif mapping.target_dataset == "framenet":
                    framenet_frames.add(target_id)
                    key = f"framenet:{target_id}"
                    confidence_scores[key] = max(confidence_scores.get(key, 0), confidence)
                elif mapping.target_dataset == "wordnet":
                    wordnet_synsets.add(target_id)
                    key = f"wordnet:{target_id}"
                    confidence_scores[key] = max(confidence_scores.get(key, 0), confidence)

        return ResolvedReferences(
            source_dataset=source,
            source_id=entity_id,
            verbnet_classes=sorted(verbnet_classes),
            propbank_rolesets=sorted(propbank_rolesets),
            framenet_frames=sorted(framenet_frames),
            wordnet_synsets=sorted(wordnet_synsets),
            confidence_scores=confidence_scores,
        )

    def find_mappings(
        self,
        source_id: str,
        source_dataset: DatasetType,
        target_dataset: DatasetType,
        fuzzy: bool = False,
    ) -> list[CrossReference]:
        """Find direct mappings between datasets.

        Parameters
        ----------
        source_id : str
            Source entity ID.
        source_dataset : DatasetType
            Source dataset.
        target_dataset : DatasetType
            Target dataset.
        fuzzy : bool, default=False
            Whether to use fuzzy matching.

        Returns
        -------
        list[CrossReference]
            Direct mappings to target dataset.
        """
        if not self.is_extracted:
            if self.auto_extract:
                self.extract_all()
            else:
                msg = "References not extracted. Call extract_all() first"
                raise RuntimeError(msg)

        if fuzzy:
            source_id = self._fuzzy_resolve_entity_id(source_id, source_dataset)

        mappings = self.extractor.get_mappings_for_entity(source_id, source_dataset)
        return [m for m in mappings if m.target_dataset == target_dataset]

    def _fuzzy_resolve_entity_id(self, entity_id: str, dataset: DatasetType) -> str:
        """Resolve entity ID using fuzzy matching.

        Parameters
        ----------
        entity_id : str
            Potentially misspelled entity ID.
        dataset : DatasetType
            Dataset to search in.
        threshold : float
            Minimum similarity threshold.

        Returns
        -------
        str
            Best matching entity ID.
        """
        # Get all entity IDs for the dataset
        candidates = self._get_dataset_entity_ids(dataset)

        # Find best fuzzy match
        best_match = find_best_match(entity_id, candidates)

        if best_match:
            return best_match

        # If no good match, return original
        return entity_id

    def _get_dataset_entity_ids(self, dataset: DatasetType) -> list[str]:
        """Get all entity IDs for a dataset.

        Parameters
        ----------
        dataset : DatasetType
            Dataset name.

        Returns
        -------
        list[str]
            List of entity IDs.
        """
        entity_ids = set()

        # Get from forward index
        for key in self.extractor.mapping_index.forward_index:
            ds, entity_id = key.split(":", 1)
            if ds == dataset:
                entity_ids.add(entity_id)

        # Get from reverse index
        for key in self.extractor.mapping_index.reverse_index:
            ds, entity_id = key.split(":", 1)
            if ds == dataset:
                entity_ids.add(entity_id)

        return sorted(entity_ids)

    def clear_cache(self) -> None:
        """Clear the cached references."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.is_extracted = False
        self.extractor = ReferenceExtractor()
        self.resolver = None

    def _save_to_cache(self) -> None:
        """Save extracted references to cache."""
        if not self.is_extracted:
            return

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Serialize the mapping index
        cache_data = {
            "forward_index": {
                key: [m.model_dump() for m in mappings]
                for key, mappings in self.extractor.mapping_index.forward_index.items()
            },
            "reverse_index": {
                key: [m.model_dump() for m in mappings]
                for key, mappings in self.extractor.mapping_index.reverse_index.items()
            },
            "verbnet_refs": {
                key: refs.model_dump() for key, refs in self.extractor.verbnet_refs.items()
            },
            "propbank_refs": {
                key: refs.model_dump() for key, refs in self.extractor.propbank_refs.items()
            },
        }

        # Write to cache file
        with self.cache_file.open("w") as f:
            json.dump(cache_data, f, indent=2, cls=DateTimeEncoder)

    def _load_from_cache(self) -> None:
        """Load extracted references from cache."""
        if not self.cache_file.exists():
            return

        try:
            with self.cache_file.open() as f:
                cache_data = json.load(f)

            # Reconstruct the mapping index
            for key, mappings_data in cache_data.get("forward_index", {}).items():
                mappings = [CrossReference(**m) for m in mappings_data]
                self.extractor.mapping_index.forward_index[key] = mappings

            for key, mappings_data in cache_data.get("reverse_index", {}).items():
                mappings = [CrossReference(**m) for m in mappings_data]
                self.extractor.mapping_index.reverse_index[key] = mappings

            # Mark as extracted
            self.is_extracted = True
            self.resolver = ReferenceResolver(self.extractor.mapping_index)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            console.print(f"[yellow]Warning: Failed to load cache: {e}[/yellow]")
            self.cache_file.unlink()


# Global default index
_default_index: CrossReferenceIndex | None = None


@lru_cache(maxsize=1)
def get_default_index() -> CrossReferenceIndex:
    """Get or create the default global index.

    Returns
    -------
    CrossReferenceIndex
        The default cross-reference index.

    Examples
    --------
    >>> xref = get_default_index()
    >>> refs = xref.resolve("give.01", source="propbank")
    """
    global _default_index  # noqa: PLW0603
    if _default_index is None:
        _default_index = CrossReferenceIndex(auto_extract=True)
    return _default_index
