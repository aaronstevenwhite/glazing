"""PropBank search functionality.

This module provides search capabilities for PropBank data,
including searches by predicate lemma, roleset ID, semantic roles,
and external resource mappings.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from glazing.propbank.models import Arg, Example, Frameset, Rel, Roleset
from glazing.propbank.symbol_parser import filter_args_by_properties
from glazing.propbank.types import (
    ArgumentNumber,
    FunctionTag,
    PredicateLemma,
    RolesetID,
)
from glazing.syntax.models import SyntaxElement, UnifiedSyntaxPattern
from glazing.syntax.parser import SyntaxParser
from glazing.types import ResourceType


class PropBankSearch:
    """Search interface for PropBank data.

    Provides methods for finding framesets and rolesets by various criteria
    including predicate lemma, roleset ID, semantic roles, function tags,
    and external resource mappings.

    Parameters
    ----------
    framesets : list[Frameset] | None
        Initial framesets to index. If None, creates empty search.

    Attributes
    ----------
    _framesets : dict[PredicateLemma, Frameset]
        Mapping from predicate lemma to frameset object.
    _rolesets : dict[RolesetID, Roleset]
        Mapping from roleset ID to roleset object.
    _rolesets_by_role : dict[ArgumentNumber, set[RolesetID]]
        Mapping from argument number to roleset IDs.
    _rolesets_by_function : dict[FunctionTag, set[RolesetID]]
        Mapping from function tag to roleset IDs.
    _rolesets_by_resource : dict[ResourceType, set[RolesetID]]
        Mapping from resource type to roleset IDs.

    Methods
    -------
    add_frameset(frameset)
        Add a frameset to the search index.
    by_lemma(lemma)
        Find frameset by predicate lemma.
    by_roleset_id(roleset_id)
        Find roleset by ID.
    by_pattern(pattern, case_sensitive)
        Find framesets matching a lemma pattern.
    by_role(arg_num, function_tag)
        Find rolesets with specific semantic roles.
    by_resource(resource_type, class_name)
        Find rolesets linked to external resources.
    search_aliases(pattern, case_sensitive)
        Search for rolesets by alias patterns.
    get_all_lemmas()
        Get all unique predicate lemmas.
    get_all_rolesets()
        Get all rolesets.
    get_statistics()
        Get search index statistics.

    Examples
    --------
    >>> search = PropBankSearch()
    >>> search.add_frameset(give_frameset)
    >>> frameset = search.by_lemma("give")
    >>> rolesets = search.by_role("0", "PAG")
    """

    def __init__(self, framesets: list[Frameset] | None = None) -> None:
        """Initialize PropBank search with optional initial framesets."""
        self._framesets: dict[PredicateLemma, Frameset] = {}
        self._rolesets: dict[RolesetID, Roleset] = {}
        self._rolesets_by_role: dict[ArgumentNumber, set[RolesetID]] = defaultdict(set)
        self._rolesets_by_function: dict[FunctionTag, set[RolesetID]] = defaultdict(set)
        self._rolesets_by_resource: dict[ResourceType, set[RolesetID]] = defaultdict(set)
        self._rolesets_by_alias: dict[str, set[RolesetID]] = defaultdict(set)

        if framesets:
            for frameset in framesets:
                self.add_frameset(frameset)

    def add_frameset(self, frameset: Frameset) -> None:
        """Add a frameset to the search index.

        Parameters
        ----------
        frameset : Frameset
            Frameset to add to index.

        Raises
        ------
        ValueError
            If frameset with same lemma already exists.
        """
        if frameset.predicate_lemma in self._framesets:
            msg = f"Frameset with lemma {frameset.predicate_lemma} already exists"
            raise ValueError(msg)

        self._framesets[frameset.predicate_lemma] = frameset

        # Index rolesets
        for roleset in frameset.rolesets:
            if roleset.id in self._rolesets:
                msg = f"Roleset with ID {roleset.id} already exists"
                raise ValueError(msg)

            self._rolesets[roleset.id] = roleset

            # Index by semantic roles
            for role in roleset.roles:
                self._rolesets_by_role[role.n].add(roleset.id)
                self._rolesets_by_function[role.f].add(roleset.id)

            # Index by external resources
            for lexlink in roleset.lexlinks:
                self._rolesets_by_resource[lexlink.resource].add(roleset.id)

            # Index by aliases
            if roleset.aliases:
                for alias in roleset.aliases.alias:
                    self._rolesets_by_alias[alias.text].add(roleset.id)

    def by_lemma(self, lemma: PredicateLemma) -> Frameset | None:
        """Find frameset by predicate lemma.

        Parameters
        ----------
        lemma : PredicateLemma
            Predicate lemma to look up.

        Returns
        -------
        Frameset | None
            Frameset if found, None otherwise.
        """
        return self._framesets.get(lemma)

    def by_roleset_id(self, roleset_id: RolesetID) -> Roleset | None:
        """Find roleset by ID.

        Parameters
        ----------
        roleset_id : RolesetID
            Roleset ID to look up.

        Returns
        -------
        Roleset | None
            Roleset if found, None otherwise.
        """
        return self._rolesets.get(roleset_id)

    def by_pattern(self, pattern: str, case_sensitive: bool = False) -> list[Frameset]:
        """Find framesets matching a lemma pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against lemmas.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[Frameset]
            Framesets with lemmas matching the pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_framesets = []
        for lemma, frameset in self._framesets.items():
            if regex.search(lemma):
                matching_framesets.append(frameset)

        return sorted(matching_framesets, key=lambda f: f.predicate_lemma)

    def by_role(
        self, arg_num: ArgumentNumber | None = None, function_tag: FunctionTag | None = None
    ) -> list[Roleset]:
        """Find rolesets with specific semantic roles.

        Parameters
        ----------
        arg_num : ArgumentNumber | None
            Argument number to search for (e.g., "0", "1", "M").
        function_tag : FunctionTag | None
            Function tag to search for (e.g., "PAG", "PPT").

        Returns
        -------
        list[Roleset]
            Rolesets matching the role criteria.
        """
        if arg_num is None and function_tag is None:
            return []

        if arg_num is not None and function_tag is not None:
            # Find rolesets with both arg_num and function_tag
            arg_rolesets = self._rolesets_by_role.get(arg_num, set())
            func_rolesets = self._rolesets_by_function.get(function_tag, set())
            matching_ids = arg_rolesets & func_rolesets
        elif arg_num is not None:
            # Find by argument number only
            matching_ids = self._rolesets_by_role.get(arg_num, set())
        else:
            # Find by function tag only
            if function_tag is None:  # This should never happen due to the initial check
                msg = "Internal error: function_tag is None in else branch"
                raise RuntimeError(msg)
            matching_ids = self._rolesets_by_function.get(function_tag, set())

        rolesets = [self._rolesets[rid] for rid in matching_ids]
        return sorted(rolesets, key=lambda r: r.id)

    def by_resource(
        self, resource_type: ResourceType, class_name: str | None = None
    ) -> list[Roleset]:
        """Find rolesets linked to external resources.

        Parameters
        ----------
        resource_type : ResourceType
            Type of resource (e.g., "VerbNet", "FrameNet").
        class_name : str | None
            Specific class/frame name to match.

        Returns
        -------
        list[Roleset]
            Rolesets linked to the specified resource.
        """
        roleset_ids = self._rolesets_by_resource.get(resource_type, set())
        rolesets = [self._rolesets[rid] for rid in roleset_ids]

        if class_name is not None:
            filtered = []
            for roleset in rolesets:
                for lexlink in roleset.lexlinks:
                    if lexlink.resource == resource_type and lexlink.class_name == class_name:
                        filtered.append(roleset)
                        break
            rolesets = filtered

        return sorted(rolesets, key=lambda r: r.id)

    def search_aliases(self, pattern: str, case_sensitive: bool = False) -> list[Roleset]:
        """Search for rolesets by alias patterns.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against aliases.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[Roleset]
            Rolesets with aliases matching the pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_ids = set()
        for alias, roleset_ids in self._rolesets_by_alias.items():
            if regex.search(alias):
                matching_ids.update(roleset_ids)

        rolesets = [self._rolesets[rid] for rid in matching_ids]
        return sorted(rolesets, key=lambda r: r.id)

    def get_all_lemmas(self) -> list[PredicateLemma]:
        """Get all unique predicate lemmas.

        Returns
        -------
        list[PredicateLemma]
            Sorted list of unique lemmas.
        """
        return sorted(self._framesets.keys())

    def get_all_rolesets(self) -> list[Roleset]:
        """Get all rolesets.

        Returns
        -------
        list[Roleset]
            All rolesets in the index, sorted by ID.
        """
        return sorted(self._rolesets.values(), key=lambda r: r.id)

    def get_all_function_tags(self) -> list[FunctionTag]:
        """Get all unique function tags.

        Returns
        -------
        list[FunctionTag]
            Sorted list of unique function tags.
        """
        return sorted(self._rolesets_by_function.keys())

    def get_all_framesets(self) -> list[Frameset]:
        """Get all framesets in the search index.

        Returns
        -------
        list[Frameset]
            All framesets sorted by predicate lemma.
        """
        return sorted(self._framesets.values(), key=lambda f: f.predicate_lemma)

    def by_arg_properties(
        self,
        is_core: bool | None = None,
        modifier_type: str | None = None,
        prefix: str | None = None,
        arg_number: str | None = None,
    ) -> list[Roleset]:
        """Find rolesets by argument properties.

        Parameters
        ----------
        is_core : bool | None, optional
            Filter for core arguments (ARG0-6).
        modifier_type : str | None, optional
            Filter for specific modifier type (e.g., "LOC", "TMP").
        prefix : str | None, optional
            Filter for continuation or reference prefix ("C" or "R").
        arg_number : str | None, optional
            Filter for specific argument number (e.g., "0", "1", "2").

        Returns
        -------
        list[Roleset]
            Rolesets with matching argument properties.
        """
        matching_rolesets = []
        for frameset in self._framesets.values():
            for roleset in frameset.rolesets:
                filtered_args = filter_args_by_properties(
                    roleset.roles,
                    is_core=is_core,
                    modifier_type=modifier_type.lower() if modifier_type else None,  # type: ignore[arg-type]
                    has_prefix=True if prefix in ["C", "R"] else None,
                    arg_number=arg_number,
                )
                if filtered_args:
                    matching_rolesets.append(roleset)

        return sorted(matching_rolesets, key=lambda r: r.id)

    def get_statistics(self) -> dict[str, int]:
        """Get search index statistics.

        Returns
        -------
        dict[str, int]
            Statistics about indexed data.
        """
        total_roles = sum(len(r.roles) for r in self._rolesets.values())
        total_examples = sum(len(r.examples) for r in self._rolesets.values())
        total_lexlinks = sum(len(r.lexlinks) for r in self._rolesets.values())

        return {
            "frameset_count": len(self._framesets),
            "roleset_count": len(self._rolesets),
            "unique_function_tags": len(self._rolesets_by_function),
            "unique_arg_numbers": len(self._rolesets_by_role),
            "total_roles": total_roles,
            "total_examples": total_examples,
            "total_lexlinks": total_lexlinks,
        }

    @classmethod
    def from_jsonl_file(cls, path: Path | str) -> PropBankSearch:
        """Load search index from JSON Lines file.

        Parameters
        ----------
        path : Path | str
            Path to JSON Lines file containing framesets.

        Returns
        -------
        PropBankSearch
            Search index populated with framesets from file.

        Raises
        ------
        FileNotFoundError
            If file does not exist.
        ValueError
            If file contains invalid data.
        """
        path = Path(path)
        if not path.exists():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        framesets = []
        with path.open(encoding="utf-8") as f:
            for line_raw in f:
                line = line_raw.strip()
                if line:
                    frameset = Frameset.model_validate_json(line)
                    framesets.append(frameset)

        return cls(framesets)

    def by_syntax(self, pattern: str) -> list[Roleset]:
        """Find rolesets with examples matching a syntactic pattern.

        Parameters
        ----------
        pattern : str
            Syntactic pattern (e.g., "NP V NP", "NP V PP").

        Returns
        -------
        list[Roleset]
            Rolesets with examples matching the syntactic pattern.
        """
        parser = SyntaxParser()
        parsed_pattern = parser.parse(pattern)

        matching_rolesets = []
        for frameset in self._framesets.values():
            for roleset in frameset.rolesets:
                for example in roleset.examples:
                    if example.propbank and self._example_matches_pattern(example, parsed_pattern):
                        matching_rolesets.append(roleset)
                        break

        # Remove duplicates while preserving order
        seen_ids = set()
        unique_rolesets = []
        for roleset in matching_rolesets:
            if roleset.id not in seen_ids:
                seen_ids.add(roleset.id)
                unique_rolesets.append(roleset)

        return sorted(unique_rolesets, key=lambda r: r.id)

    def _example_matches_pattern(
        self, example: Example, parsed_pattern: UnifiedSyntaxPattern
    ) -> bool:
        """Check if an example matches the syntactic pattern."""
        if not example.propbank or not example.propbank.args:
            return False

        # Extract syntactic pattern from PropBank annotation
        extracted_pattern = self._extract_pattern_from_example(example)
        if not extracted_pattern:
            return False

        # Use hierarchical matching
        if len(parsed_pattern.elements) != len(extracted_pattern.elements):
            return False

        for search_elem, example_elem in zip(
            parsed_pattern.elements, extracted_pattern.elements, strict=False
        ):
            matches, _ = search_elem.matches_hierarchically(example_elem)
            if not matches:
                return False

        return True

    def _extract_pattern_from_example(self, example: Example) -> UnifiedSyntaxPattern | None:
        """Extract syntactic pattern from PropBank example."""
        if not example.propbank or not example.propbank.args:
            return None

        positioned_elements = self._get_positioned_elements(example)
        elements = self._sort_and_extract_elements(positioned_elements)
        self._ensure_verb_in_elements(elements)

        if not elements:
            return None

        return UnifiedSyntaxPattern(
            elements=elements,
            source_pattern=" ".join(e.constituent for e in elements),
            source_dataset="propbank",
        )

    def _get_positioned_elements(self, example: Example) -> list[tuple[int, SyntaxElement]]:
        """Get positioned elements from PropBank example."""
        positioned_elements = []

        # Add arguments
        if example.propbank is None:
            return []
        for arg in example.propbank.args:
            element = self._map_propbank_arg_to_element(arg)
            if element is not None:
                position = self._get_arg_position(arg)
                positioned_elements.append((position, element))

        # Add verb if we have its position
        if example.propbank.rel:
            rel_position = self._get_rel_position(example.propbank.rel)
            if rel_position is not None:
                verb_element = SyntaxElement(constituent="VERB")
                positioned_elements.append((rel_position, verb_element))

        return positioned_elements

    def _map_propbank_arg_to_element(self, arg: Arg) -> SyntaxElement | None:
        """Map PropBank argument to syntax element with semantic role."""
        arg_type = arg.type

        if arg_type in ["ARG0", "ARG1", "ARG2", "ARG3", "ARG4", "ARG5"]:
            return SyntaxElement(constituent="NP", semantic_role=arg_type)
        if arg_type.startswith("ARGM-"):
            return self._map_modifier_arg_to_element(arg_type)
        return None

    def _map_modifier_arg_to_element(self, arg_type: str) -> SyntaxElement:
        """Map PropBank modifier argument to syntax element with features."""
        modifier = arg_type.split("-", 1)[1] if "-" in arg_type else ""

        role_mappings = {
            "LOC": "location",
            "DIR": "direction",
            "GOL": "goal",
            "TMP": "temporal",
            "MNR": "manner",
            "PRP": "purpose",
            "CAU": "cause",
            "ADV": "adverbial",
            "DIS": "discourse",
            "EXT": "extent",
            "NEG": "negation",
            "MOD": "modal",
        }

        semantic_role = role_mappings.get(modifier)
        features = {}

        # Add modifier type as feature
        if modifier:
            features["modifier"] = modifier.lower()

        if semantic_role:
            return SyntaxElement(constituent="PP", semantic_role=semantic_role, features=features)
        return SyntaxElement(constituent="PP", features=features)

    def _sort_and_extract_elements(
        self, positioned_elements: list[tuple[int, SyntaxElement]]
    ) -> list[SyntaxElement]:
        """Sort positioned elements and extract the syntax elements."""
        positioned_elements.sort(key=lambda x: x[0])
        return [elem for pos, elem in positioned_elements]

    def _ensure_verb_in_elements(self, elements: list[SyntaxElement]) -> None:
        """Ensure a verb is present in the elements list."""
        if not any(e.constituent == "VERB" for e in elements):
            # Insert verb after first NP (typical SVO order)
            np_indices = [i for i, e in enumerate(elements) if e.constituent == "NP"]
            if np_indices:
                elements.insert(np_indices[0] + 1, SyntaxElement(constituent="VERB"))
            else:
                elements.insert(0, SyntaxElement(constituent="VERB"))

    def _get_arg_position(self, arg: Arg) -> int:
        """Get argument position, handling '?' as high value."""
        if arg.start == "?":
            return 999
        return int(arg.start)

    def _get_rel_position(self, rel: Rel) -> int | None:
        """Get relation position, handling '?' as None."""
        if not rel or rel.relloc == "?":
            return None
        try:
            return int(rel.relloc)
        except (ValueError, TypeError):
            return None
