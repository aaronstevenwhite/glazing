"""PropBank data loader.

This module provides functionality for loading PropBank framesets and rolesets
from JSON Lines files, with support for cross-reference resolution and lazy loading.

Classes
-------
PropBankLoader
    Load and manage PropBank framesets and rolesets with automatic loading.

Functions
---------
load_framesets
    Load all framesets from a JSON Lines file.
load_frameset
    Load a specific frameset by predicate lemma.

Examples
--------
>>> from glazing.propbank.loader import PropBankLoader
>>> # Data loads automatically on initialization
>>> loader = PropBankLoader()
>>> framesets = loader.framesets  # Access loaded framesets via property
>>> frameset = loader.get_frameset("abandon")
>>> roleset = loader.get_roleset("abandon.01")
>>>
>>> # Or disable autoload for manual control
>>> loader = PropBankLoader(autoload=False)
>>> framesets = loader.load()  # Load manually when needed
"""

from __future__ import annotations

import json
import re
from collections.abc import Generator
from pathlib import Path

from pydantic import ConfigDict, Field

from glazing.base import GlazingBaseModel
from glazing.initialize import get_default_data_path
from glazing.propbank.models import (
    Frameset,
    LexLink,
    RoleLink,
    Roleset,
)
from glazing.propbank.types import PredicateLemma, RolesetID
from glazing.utils.cache import QueryCache


class PropBankLoader(GlazingBaseModel):
    """Load and manage PropBank framesets and rolesets with automatic loading.

    By default, data is loaded automatically on initialization.

    Parameters
    ----------
    data_path : Path | str | None, optional
        Path to PropBank JSON Lines file. If None, uses default path.
    lazy : bool, default=False
        Whether to use lazy loading for framesets.
    autoload : bool, default=True
        Whether to automatically load data on initialization.
        Only applies when lazy=False.
    cache_size : int, default=1000
        Maximum number of framesets to cache in memory.

    Attributes
    ----------
    data_path : Path
        Path to the data file.
    lazy : bool
        Whether lazy loading is enabled.
    framesets : dict[PredicateLemma, Frameset]
        Property that returns loaded framesets, loading them if needed.
    cache : QueryCache
        Cache for loaded framesets (only when lazy=True).
    frameset_index : dict[PredicateLemma, int]
        Index mapping predicates to file positions.
    roleset_index : dict[RolesetID, PredicateLemma]
        Index mapping roleset IDs to predicates.

    Methods
    -------
    load()
        Load all framesets into memory.
    get_frameset(predicate)
        Get a specific frameset by predicate.
    get_roleset(roleset_id)
        Get a specific roleset by ID.
    build_indices()
        Build predicate and roleset indices.
    resolve_cross_references(roleset)
        Resolve cross-references in a roleset.

    Examples
    --------
    >>> # Automatic loading (default)
    >>> loader = PropBankLoader()
    >>> framesets = loader.framesets  # Already loaded
    >>> frameset = loader.get_frameset("give")
    >>> print(f"Found {len(frameset.rolesets)} rolesets")
    Found 3 rolesets

    >>> # Manual loading
    >>> loader = PropBankLoader(autoload=False)
    >>> framesets = loader.load()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data_path: Path
    lazy: bool = False
    cache: QueryCache | None = Field(default=None, exclude=True)
    frameset_index: dict[PredicateLemma, int] = Field(default_factory=dict)
    roleset_index: dict[RolesetID, PredicateLemma] = Field(default_factory=dict)
    framesets_cache: dict[PredicateLemma, Frameset] | None = Field(default=None, exclude=True)

    def __init__(  # type: ignore[no-untyped-def]
        self,
        data_path: Path | str | None = None,
        lazy: bool = False,
        autoload: bool = True,
        cache_size: int = 1000,
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize PropBank loader.

        Parameters
        ----------
        data_path : Path | str | None, optional
            Path to PropBank JSON Lines file.
            If None, uses default path from environment.
        lazy : bool, default=False
            Whether to use lazy loading.
        autoload : bool, default=True
            Whether to automatically load data on initialization.
            Only applies when lazy=False.
        cache_size : int, default=1000
            Maximum cache size.
        **kwargs
            Additional keyword arguments.
        """
        # Use default path if not provided
        if data_path is None:
            data_path = get_default_data_path("propbank.jsonl")

        # Initialize fields before calling super()
        data = {"data_path": Path(data_path), "lazy": lazy, **kwargs}
        super().__init__(**data)

        # Set cache after initialization
        self.cache = QueryCache(max_size=cache_size) if lazy else None
        self.framesets_cache = None if lazy else {}

        if not self.data_path.exists():
            msg = f"Data file not found: {self.data_path}"
            raise FileNotFoundError(msg)

        # Build indices on initialization
        self.build_indices()

        # Autoload data if requested and not lazy loading
        if autoload and not lazy:
            self.load()

    def load(self) -> dict[PredicateLemma, Frameset]:
        """Load all framesets into memory.

        Returns
        -------
        dict[PredicateLemma, Frameset]
            All framesets mapped by predicate lemma.

        Raises
        ------
        ValueError
            If data file contains invalid JSON.
        """
        if self.framesets_cache is not None and self.framesets_cache:
            return self.framesets_cache

        framesets = {}
        with self.data_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                try:
                    data = json.loads(stripped_line)
                    frameset = Frameset.model_validate(data)
                    framesets[frameset.predicate_lemma] = frameset
                except (json.JSONDecodeError, ValueError) as e:
                    msg = f"Error parsing line {line_num}: {e}"
                    raise ValueError(msg) from e

        if not self.lazy:
            self.framesets_cache = framesets

        return framesets

    @property
    def framesets(self) -> dict[PredicateLemma, Frameset]:
        """Get loaded framesets.

        Returns
        -------
        dict[PredicateLemma, Frameset]
            Dictionary of framesets mapped by predicate lemma.
            Loads automatically if not yet loaded.
        """
        if self.framesets_cache is None:
            self.load()
        return self.framesets_cache if self.framesets_cache else {}

    def get_frameset(self, predicate: PredicateLemma) -> Frameset | None:
        """Get a specific frameset by predicate lemma.

        Parameters
        ----------
        predicate : PredicateLemma
            Predicate lemma to look up.

        Returns
        -------
        Frameset | None
            The frameset if found, None otherwise.
        """
        # Check cache first if lazy loading
        if self.lazy and self.cache:
            cached = self.cache.get_query_result("frameset", {"predicate": predicate})
            if cached is not None and isinstance(cached, Frameset):
                return cached

        # Check in-memory framesets if not lazy loading
        if self.framesets_cache is not None:
            return self.framesets_cache.get(predicate)

        # Load from file if lazy loading
        if predicate not in self.frameset_index:
            return None

        line_offset = self.frameset_index[predicate]
        frameset = self._load_frameset_at_offset(line_offset)

        # Cache the result
        if self.lazy and self.cache and frameset:
            self.cache.cache_query_result("frameset", {"predicate": predicate}, frameset)  # type: ignore[arg-type]

        return frameset

    def get_roleset(self, roleset_id: RolesetID) -> Roleset | None:
        """Get a specific roleset by ID.

        Parameters
        ----------
        roleset_id : RolesetID
            Roleset ID (e.g., "abandon.01").

        Returns
        -------
        Roleset | None
            The roleset if found, None otherwise.
        """
        # Check cache first
        if self.lazy and self.cache:
            cached = self.cache.get_query_result("roleset", {"id": roleset_id})
            if cached is not None and isinstance(cached, Roleset):
                return cached

        # Look up predicate from roleset index
        if roleset_id not in self.roleset_index:
            return None

        predicate = self.roleset_index[roleset_id]
        frameset = self.get_frameset(predicate)

        if not frameset:
            return None

        # Find the roleset within the frameset
        for roleset in frameset.rolesets:
            if roleset.id == roleset_id:
                # Resolve cross-references
                self.resolve_cross_references(roleset)
                # Cache the result
                if self.lazy and self.cache:
                    self.cache.cache_query_result("roleset", {"id": roleset_id}, roleset)  # type: ignore[arg-type]
                return roleset

        return None

    def build_indices(self) -> None:
        """Build predicate and roleset indices for fast lookup.

        This method scans the JSON Lines file to build indices
        without loading all data into memory.
        """
        self.frameset_index.clear()
        self.roleset_index.clear()

        with self.data_path.open("r", encoding="utf-8") as f:
            offset = 0
            while True:
                # Save current position before reading
                current_offset = offset
                line = f.readline()

                if not line:
                    break  # End of file

                line = line.strip()
                if not line:
                    offset = f.tell()
                    continue

                try:
                    data = json.loads(line)
                    predicate = data.get("predicate_lemma")
                    if predicate:
                        self.frameset_index[predicate] = current_offset

                        # Index rolesets
                        rolesets = data.get("rolesets", [])
                        for roleset_data in rolesets:
                            roleset_id = roleset_data.get("id")
                            if roleset_id:
                                self.roleset_index[roleset_id] = predicate

                except (json.JSONDecodeError, KeyError):
                    pass  # Skip invalid lines

                offset = f.tell()

    def resolve_cross_references(self, roleset: Roleset) -> None:
        """Resolve cross-references in a roleset.

        This method validates and enhances RoleLinks and LexLinks
        with additional metadata where available.

        Parameters
        ----------
        roleset : Roleset
            The roleset to resolve references for.
        """
        # Resolve RoleLinks
        for role in roleset.roles:
            for rolelink in role.rolelinks:
                self._validate_rolelink(rolelink)

        # Resolve LexLinks
        for lexlink in roleset.lexlinks:
            self._validate_lexlink(lexlink)

    def iter_framesets(self, batch_size: int = 100) -> Generator[list[Frameset], None, None]:
        """Iterate over framesets in batches.

        Parameters
        ----------
        batch_size : int, default=100
            Number of framesets per batch.

        Yields
        ------
        list[Frameset]
            Batch of framesets.
        """
        batch = []
        with self.data_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    data = json.loads(stripped_line)
                    frameset = Frameset.model_validate(data)
                    batch.append(frameset)

                    if len(batch) >= batch_size:
                        yield batch
                        batch = []

                except (json.JSONDecodeError, ValueError):
                    continue  # Skip invalid lines

        if batch:
            yield batch

    def search_by_pattern(self, pattern: str) -> list[Frameset]:
        """Search for framesets by predicate pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match predicates.

        Returns
        -------
        list[Frameset]
            Matching framesets.
        """

        regex = re.compile(pattern, re.IGNORECASE)
        matches = []

        for predicate in self.frameset_index:
            if regex.search(predicate):
                frameset = self.get_frameset(predicate)
                if frameset:
                    matches.append(frameset)

        return matches

    def get_statistics(self) -> dict[str, int | float | bool]:
        """Get statistics about loaded PropBank data.

        Returns
        -------
        dict[str, int | float | bool]
            Statistics including counts and coverage.
        """
        stats: dict[str, int | float | bool] = {
            "total_framesets": len(self.frameset_index),
            "total_rolesets": len(self.roleset_index),
            "cached_framesets": self.cache.size() if self.cache else 0,
            "lazy_loading": self.lazy,
        }

        if not self.lazy and self.framesets_cache:
            # Calculate additional statistics from loaded data
            total_roles = 0
            total_examples = 0

            for frameset in self.framesets_cache.values():
                for roleset in frameset.rolesets:
                    total_roles += len(roleset.roles)
                    total_examples += len(roleset.examples)

            stats.update(
                {
                    "total_roles": total_roles,
                    "total_examples": total_examples,
                    "average_roles_per_roleset": (
                        float(total_roles) / len(self.roleset_index) if self.roleset_index else 0.0
                    ),
                }
            )

        return stats

    def _load_frameset_at_offset(self, offset: int) -> Frameset | None:
        """Load a frameset from a specific file offset.

        Parameters
        ----------
        offset : int
            File offset to read from.

        Returns
        -------
        Frameset | None
            The loaded frameset or None if failed.
        """
        try:
            with self.data_path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                line = f.readline().strip()
                if line:
                    data = json.loads(line)
                    return Frameset.model_validate(data)
        except (json.JSONDecodeError, ValueError, OSError):
            pass
        return None

    def _validate_rolelink(self, rolelink: RoleLink) -> None:
        """Validate a RoleLink reference.

        Parameters
        ----------
        rolelink : RoleLink
            The RoleLink to validate.
        """
        # Basic validation is handled by Pydantic
        # Additional validation could check if referenced classes exist

    def _validate_lexlink(self, lexlink: LexLink) -> None:
        """Validate a LexLink reference.

        Parameters
        ----------
        lexlink : LexLink
            The LexLink to validate.
        """
        # Validate confidence score is in range
        if not 0.0 <= lexlink.confidence <= 1.0:
            msg = f"Invalid confidence score: {lexlink.confidence}"
            raise ValueError(msg)


# Convenience functions


def load_framesets(path: Path | str) -> dict[PredicateLemma, Frameset]:
    """Load all PropBank framesets from a JSON Lines file.

    Parameters
    ----------
    path : Path | str
        Path to the JSON Lines file.

    Returns
    -------
    dict[PredicateLemma, Frameset]
        All framesets mapped by predicate.

    Examples
    --------
    >>> framesets = load_framesets("propbank.jsonl")
    >>> print(f"Loaded {len(framesets)} framesets")
    """
    loader = PropBankLoader(path, lazy=False, autoload=False)
    return loader.load()


def load_frameset(path: Path | str, predicate: PredicateLemma) -> Frameset | None:
    """Load a specific frameset by predicate.

    Parameters
    ----------
    path : Path | str
        Path to the JSON Lines file.
    predicate : PredicateLemma
        Predicate lemma to load.

    Returns
    -------
    Frameset | None
        The frameset if found.

    Examples
    --------
    >>> frameset = load_frameset("propbank.jsonl", "abandon")
    >>> if frameset:
    ...     print(f"Found {len(frameset.rolesets)} rolesets")
    """
    loader = PropBankLoader(path, lazy=True, autoload=False)
    return loader.get_frameset(predicate)
