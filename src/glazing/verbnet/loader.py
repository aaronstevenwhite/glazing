"""VerbNet data loader.

This module provides functionality for loading VerbNet verb classes
from JSON Lines files, with support for cross-reference resolution,
inheritance handling, and lazy loading.

Classes
-------
VerbNetLoader
    Load and manage VerbNet verb classes with automatic loading.

Functions
---------
load_verb_classes
    Load all verb classes from a JSON Lines file.
load_verb_class
    Load a specific verb class by ID.

Examples
--------
>>> from glazing.verbnet.loader import VerbNetLoader
>>> # Data loads automatically on initialization
>>> loader = VerbNetLoader()
>>> classes = loader.classes  # Access loaded verb classes via property
>>> verb_class = loader.get_verb_class("give-13.1")
>>> member = loader.get_member("give#2")
>>>
>>> # Or disable autoload for manual control
>>> loader = VerbNetLoader(autoload=False)
>>> classes = loader.load()  # Load manually when needed
"""

from __future__ import annotations

import json
import re
from collections.abc import Generator
from pathlib import Path

from pydantic import ConfigDict, Field

from glazing.base import GlazingBaseModel
from glazing.initialize import get_default_data_path
from glazing.utils.cache import QueryCache
from glazing.verbnet.inheritance import RoleInheritanceResolver
from glazing.verbnet.models import Member, ThematicRole, VerbClass
from glazing.verbnet.types import VerbClassID, VerbNetKey


class VerbNetLoader(GlazingBaseModel):
    """Load and manage VerbNet verb classes with automatic loading.

    By default, data is loaded automatically on initialization.

    Parameters
    ----------
    data_path : Path | str | None, optional
        Path to VerbNet JSON Lines file. If None, uses default path.
    lazy : bool, default=False
        Whether to use lazy loading for verb classes.
    autoload : bool, default=True
        Whether to automatically load data on initialization.
        Only applies when lazy=False.
    cache_size : int, default=1000
        Maximum number of verb classes to cache in memory.

    Attributes
    ----------
    data_path : Path
        Path to the data file.
    lazy : bool
        Whether lazy loading is enabled.
    classes : dict[VerbClassID, VerbClass]
        Property that returns loaded verb classes, loading them if needed.
    cache : QueryCache | None
        Cache for loaded verb classes (only when lazy=True).
    class_index : dict[VerbClassID, int]
        Index mapping class IDs to file positions.
    member_index : dict[VerbNetKey, VerbClassID]
        Index mapping member keys to class IDs.
    inheritance_resolver : RoleInheritanceResolver
        Resolver for thematic role inheritance.

    Methods
    -------
    load()
        Load all verb classes into memory.
    get_verb_class(class_id)
        Get a specific verb class by ID.
    get_member(verbnet_key)
        Get a specific member by verbnet_key.
    get_effective_roles(class_id)
        Get effective roles considering inheritance.
    build_indices()
        Build class and member indices.

    Examples
    --------
    >>> # Automatic loading (default)
    >>> loader = VerbNetLoader()
    >>> classes = loader.classes  # Already loaded
    >>> verb_class = loader.get_verb_class("give-13.1")
    >>> print(f"Found {len(verb_class.members)} members")
    Found 15 members

    >>> # Manual loading
    >>> loader = VerbNetLoader(autoload=False)
    >>> classes = loader.load()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data_path: Path
    lazy: bool = False
    cache: QueryCache | None = Field(default=None, exclude=True)
    class_index: dict[VerbClassID, int] = Field(default_factory=dict)
    member_index: dict[VerbNetKey, VerbClassID] = Field(default_factory=dict)
    classes_cache: dict[VerbClassID, VerbClass] | None = Field(default=None, exclude=True)
    inheritance_resolver: RoleInheritanceResolver = Field(
        default_factory=RoleInheritanceResolver, exclude=True
    )

    def __init__(  # type: ignore[no-untyped-def]
        self,
        data_path: Path | str | None = None,
        lazy: bool = False,
        autoload: bool = True,
        cache_size: int = 1000,
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize VerbNet loader.

        Parameters
        ----------
        data_path : Path | str | None, optional
            Path to VerbNet JSON Lines file.
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
            data_path = get_default_data_path("verbnet.jsonl")

        # Initialize fields before calling super()
        data = {"data_path": Path(data_path), "lazy": lazy, **kwargs}
        super().__init__(**data)

        # Set cache after initialization
        self.cache = QueryCache(max_size=cache_size) if lazy else None
        self.classes_cache = None if lazy else {}

        if not self.data_path.exists():
            msg = f"Data file not found: {self.data_path}"
            raise FileNotFoundError(msg)

        # Build indices on initialization
        self.build_indices()

        # Autoload data if requested and not lazy loading
        if autoload and not lazy:
            self.load()

    def load(self) -> dict[VerbClassID, VerbClass]:
        """Load all verb classes into memory.

        Returns
        -------
        dict[VerbClassID, VerbClass]
            All verb classes mapped by class ID.

        Raises
        ------
        ValueError
            If data file contains invalid JSON.
        """
        if self.classes_cache is not None and self.classes_cache:
            return self.classes_cache

        classes = {}
        with self.data_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                try:
                    data = json.loads(stripped_line)
                    verb_class = VerbClass.model_validate(data)
                    classes[verb_class.id] = verb_class
                except (json.JSONDecodeError, ValueError) as e:
                    msg = f"Error parsing line {line_num}: {e}"
                    raise ValueError(msg) from e

        if not self.lazy:
            self.classes_cache = classes

        return classes

    @property
    def classes(self) -> dict[VerbClassID, VerbClass]:
        """Get loaded verb classes.

        Returns
        -------
        dict[VerbClassID, VerbClass]
            Dictionary of verb classes mapped by class ID.
            Loads automatically if not yet loaded.
        """
        if self.classes_cache is None:
            self.load()
        return self.classes_cache if self.classes_cache else {}

    def get_verb_class(self, class_id: VerbClassID) -> VerbClass | None:
        """Get a specific verb class by ID.

        Parameters
        ----------
        class_id : VerbClassID
            Verb class ID to look up.

        Returns
        -------
        VerbClass | None
            The verb class if found, None otherwise.
        """
        # Check cache first if lazy loading
        if self.lazy and self.cache:
            cached = self.cache.get_query_result("verb_class", {"id": class_id})
            if cached is not None and isinstance(cached, VerbClass):
                return cached

        # Check in-memory classes if not lazy loading
        if self.classes_cache is not None:
            return self.classes_cache.get(class_id)

        # Load from file if lazy loading
        if class_id not in self.class_index:
            return None

        line_offset = self.class_index[class_id]
        verb_class = self._load_class_at_offset(line_offset)

        # Cache the result
        if self.lazy and self.cache and verb_class:
            self.cache.cache_query_result("verb_class", {"id": class_id}, verb_class)  # type: ignore[arg-type]

        return verb_class

    def get_member(self, verbnet_key: VerbNetKey) -> Member | None:
        """Get a specific member by verbnet_key.

        Parameters
        ----------
        verbnet_key : VerbNetKey
            Member verbnet_key (e.g., "give#2").

        Returns
        -------
        Member | None
            The member if found, None otherwise.
        """
        # Check cache first
        if self.lazy and self.cache:
            cached = self.cache.get_query_result("member", {"key": verbnet_key})
            if cached is not None and isinstance(cached, Member):
                return cached

        # Look up class from member index
        if verbnet_key not in self.member_index:
            return None

        class_id = self.member_index[verbnet_key]
        verb_class = self.get_verb_class(class_id)

        if not verb_class:
            return None

        # Search for member in class and subclasses
        member = self._find_member_in_class(verb_class, verbnet_key)

        # Cache the result if found
        if member and self.lazy and self.cache:
            self.cache.cache_query_result("member", {"key": verbnet_key}, member)  # type: ignore[arg-type]

        return member

    def _find_member_in_class(
        self, verb_class: VerbClass, verbnet_key: VerbNetKey
    ) -> Member | None:
        """Find a member in a class or its subclasses.

        Parameters
        ----------
        verb_class : VerbClass
            The class to search in.
        verbnet_key : VerbNetKey
            The member key to find.

        Returns
        -------
        Member | None
            The member if found.
        """
        # Check direct members
        for member in verb_class.members:
            if member.verbnet_key == verbnet_key:
                return member

        # Check subclass members
        for subclass in verb_class.subclasses:
            for member in subclass.members:
                if member.verbnet_key == verbnet_key:
                    return member

        return None

    def get_effective_roles(self, class_id: VerbClassID) -> list[ThematicRole]:
        """Get effective roles for a class considering inheritance.

        Parameters
        ----------
        class_id : VerbClassID
            Verb class ID.

        Returns
        -------
        list[ThematicRole]
            Effective roles after applying inheritance.
        """
        verb_class = self.get_verb_class(class_id)
        if not verb_class:
            return []

        # Get parent roles if this is a subclass
        parent_roles = None
        if verb_class.parent_class:
            parent_class = self.get_verb_class(verb_class.parent_class)
            if parent_class:
                parent_roles = self.get_effective_roles(parent_class.id)

        return self.inheritance_resolver.get_effective_roles(verb_class, parent_roles)

    def build_indices(self) -> None:
        """Build class and member indices for fast lookup.

        This method scans the JSON Lines file to build indices
        without loading all data into memory.
        """
        self.class_index.clear()
        self.member_index.clear()

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
                    class_id = data.get("id")
                    if class_id:
                        self.class_index[class_id] = current_offset

                        # Index members
                        members = data.get("members", [])
                        for member_data in members:
                            verbnet_key = member_data.get("verbnet_key")
                            if verbnet_key:
                                self.member_index[verbnet_key] = class_id

                        # Index subclass members recursively
                        self._index_subclasses(data.get("subclasses", []), class_id)

                except (json.JSONDecodeError, KeyError):
                    pass  # Skip invalid lines

                offset = f.tell()

    def _index_subclasses(
        self, subclasses: list[dict[str, object]], parent_id: VerbClassID
    ) -> None:
        """Index members in subclasses recursively.

        Parameters
        ----------
        subclasses : list[dict]
            Subclass data.
        parent_id : VerbClassID
            Parent class ID.
        """
        for subclass_data in subclasses:
            subclass_id = subclass_data.get("id")
            if subclass_id:
                # Subclasses are embedded, not separate entries
                members = subclass_data.get("members", [])
                if isinstance(members, list):
                    for member_data in members:
                        verbnet_key = member_data.get("verbnet_key")
                        if verbnet_key:
                            # Map to the top-level parent class
                            self.member_index[verbnet_key] = parent_id

                # Recursively index nested subclasses
                nested_subclasses = subclass_data.get("subclasses", [])
                if isinstance(nested_subclasses, list):
                    self._index_subclasses(nested_subclasses, parent_id)

    def iter_verb_classes(self, batch_size: int = 100) -> Generator[list[VerbClass], None, None]:
        """Iterate over verb classes in batches.

        Parameters
        ----------
        batch_size : int, default=100
            Number of verb classes per batch.

        Yields
        ------
        list[VerbClass]
            Batch of verb classes.
        """
        batch = []
        with self.data_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    data = json.loads(stripped_line)
                    verb_class = VerbClass.model_validate(data)
                    batch.append(verb_class)

                    if len(batch) >= batch_size:
                        yield batch
                        batch = []

                except (json.JSONDecodeError, ValueError):
                    continue  # Skip invalid lines

        if batch:
            yield batch

    def search_by_pattern(self, pattern: str) -> list[VerbClass]:
        """Search for verb classes by ID pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match class IDs.

        Returns
        -------
        list[VerbClass]
            Matching verb classes.
        """
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []

        for class_id in self.class_index:
            if regex.search(class_id):
                verb_class = self.get_verb_class(class_id)
                if verb_class:
                    matches.append(verb_class)

        return matches

    def get_statistics(self) -> dict[str, int | float | bool]:
        """Get statistics about loaded VerbNet data.

        Returns
        -------
        dict[str, int | float | bool]
            Statistics including counts and coverage.
        """
        stats: dict[str, int | float | bool] = {
            "total_classes": len(self.class_index),
            "total_members": len(self.member_index),
            "cached_classes": self.cache.size() if self.cache else 0,
            "lazying": self.lazy,
        }

        if not self.lazy and self.classes_cache:
            # Calculate additional statistics from loaded data
            total_roles = 0
            total_frames = 0
            total_subclasses = 0

            for verb_class in self.classes_cache.values():
                total_roles += len(verb_class.themroles)
                total_frames += len(verb_class.frames)
                total_subclasses += len(verb_class.subclasses)

            stats.update(
                {
                    "total_roles": total_roles,
                    "total_frames": total_frames,
                    "total_subclasses": total_subclasses,
                    "average_roles_per_class": (
                        float(total_roles) / len(self.class_index) if self.class_index else 0.0
                    ),
                    "average_frames_per_class": (
                        float(total_frames) / len(self.class_index) if self.class_index else 0.0
                    ),
                }
            )

        return stats

    def get_class_hierarchy(self) -> dict[VerbClassID, list[VerbClassID]]:
        """Get the class hierarchy structure.

        Returns
        -------
        dict[VerbClassID, list[VerbClassID]]
            Maps parent class IDs to lists of subclass IDs.
        """
        hierarchy: dict[VerbClassID, list[VerbClassID]] = {}

        # If not lazy loading, use cached data
        if self.classes_cache:
            for class_id, verb_class in self.classes_cache.items():
                subclass_ids = [sub.id for sub in verb_class.subclasses]
                if subclass_ids:
                    hierarchy[class_id] = subclass_ids
        else:
            # Load all classes to build hierarchy
            all_classes = self.load()
            for class_id, verb_class in all_classes.items():
                subclass_ids = [sub.id for sub in verb_class.subclasses]
                if subclass_ids:
                    hierarchy[class_id] = subclass_ids

        return hierarchy

    def _load_class_at_offset(self, offset: int) -> VerbClass | None:
        """Load a verb class from a specific file offset.

        Parameters
        ----------
        offset : int
            File offset to read from.

        Returns
        -------
        VerbClass | None
            The loaded verb class or None if failed.
        """
        try:
            with self.data_path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                line = f.readline().strip()
                if line:
                    data = json.loads(line)
                    return VerbClass.model_validate(data)
        except (json.JSONDecodeError, ValueError, OSError):
            pass
        return None


# Convenience functions


def load_verb_classes(path: Path | str) -> dict[VerbClassID, VerbClass]:
    """Load all VerbNet verb classes from a JSON Lines file.

    Parameters
    ----------
    path : Path | str
        Path to the JSON Lines file.

    Returns
    -------
    dict[VerbClassID, VerbClass]
        All verb classes mapped by class ID.

    Examples
    --------
    >>> verb_classes = load_verb_classes("verbnet.jsonl")
    >>> print(f"Loaded {len(verb_classes)} verb classes")
    """
    loader = VerbNetLoader(path, lazy=False, autoload=False)
    return loader.load()


def load_verb_class(path: Path | str, class_id: VerbClassID) -> VerbClass | None:
    """Load a specific verb class by ID.

    Parameters
    ----------
    path : Path | str
        Path to the JSON Lines file.
    class_id : VerbClassID
        Verb class ID to load.

    Returns
    -------
    VerbClass | None
        The verb class if found.

    Examples
    --------
    >>> verb_class = load_verb_class("verbnet.jsonl", "give-13.1")
    >>> if verb_class:
    ...     print(f"Found {len(verb_class.members)} members")
    """
    loader = VerbNetLoader(path, lazy=True, autoload=False)
    return loader.get_verb_class(class_id)
