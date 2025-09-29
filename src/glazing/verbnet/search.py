"""VerbNet search functionality.

This module provides search capabilities for VerbNet data,
including searches by thematic roles, syntactic patterns, semantic predicates,
selectional restrictions, and member verbs.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from glazing.syntax.models import UnifiedSyntaxPattern
from glazing.syntax.parser import SyntaxParser
from glazing.verbnet.models import (
    SelectionalRestriction,
    SelectionalRestrictions,
    VerbClass,
)
from glazing.verbnet.symbol_parser import filter_roles_by_properties
from glazing.verbnet.types import (
    PredicateType,
    RestrictionValue,
    SelectionalRestrictionType,
    ThematicRoleType,
    VerbClassID,
)


class VerbNetSearch:
    """Search interface for VerbNet data.

    Provides methods for finding verb classes by various criteria
    including thematic roles, syntactic patterns, semantic predicates,
    and selectional restrictions.

    Parameters
    ----------
    classes : list[VerbClass] | None
        Initial verb classes to index. If None, creates empty search.

    Attributes
    ----------
    _classes : dict[VerbClassID, VerbClass]
        Mapping from class ID to verb class object.
    _classes_by_member : dict[str, set[VerbClassID]]
        Mapping from member lemma to class IDs.
    _classes_by_role : dict[ThematicRoleType, set[VerbClassID]]
        Mapping from thematic role to class IDs.
    _classes_by_predicate : dict[PredicateType, set[VerbClassID]]
        Mapping from semantic predicate to class IDs.

    Methods
    -------
    add_class(verb_class)
        Add a verb class to the search index.
    by_themroles(roles, only)
        Find classes with specified thematic roles.
    by_syntax(pattern)
        Find classes with matching syntactic patterns.
    by_predicate(predicate)
        Find classes using a specific semantic predicate.
    by_predicates(predicates, require_all)
        Find classes using multiple semantic predicates.
    by_restriction(role, type, value)
        Find classes with selectional restrictions.
    by_members(lemmas)
        Find classes containing specific member verbs.
    complex_search(predicates, themroles, restrictions, syntax)
        Multi-criteria search for verb classes.

    Examples
    --------
    >>> search = VerbNetSearch()
    >>> search.add_class(give_class)
    >>> classes = search.by_themroles(["Agent", "Theme", "Recipient"])
    >>> motion_classes = search.by_predicate("motion")
    """

    def __init__(self, classes: list[VerbClass] | None = None) -> None:
        """Initialize VerbNet search with optional initial classes."""
        self._classes: dict[VerbClassID, VerbClass] = {}
        self._classes_by_member: dict[str, set[VerbClassID]] = defaultdict(set)
        self._classes_by_role: dict[ThematicRoleType, set[VerbClassID]] = defaultdict(set)
        self._classes_by_predicate: dict[PredicateType, set[VerbClassID]] = defaultdict(set)

        if classes:
            for verb_class in classes:
                self.add_class(verb_class)

    def add_class(self, verb_class: VerbClass) -> None:
        """Add a verb class to the search index.

        Parameters
        ----------
        verb_class : VerbClass
            Verb class to add to index.

        Raises
        ------
        ValueError
            If class with same ID already exists.
        """
        if verb_class.id in self._classes:
            msg = f"Class with ID {verb_class.id} already exists"
            raise ValueError(msg)

        self._classes[verb_class.id] = verb_class

        # Index members
        for member in verb_class.members:
            self._classes_by_member[member.name].add(verb_class.id)

        # Index thematic roles
        for role in verb_class.themroles:
            self._classes_by_role[role.type].add(verb_class.id)

        # Index semantic predicates
        for frame in verb_class.frames:
            for predicate in frame.semantics.predicates:
                self._classes_by_predicate[predicate.value].add(verb_class.id)

        # Recursively add subclasses
        for subclass in verb_class.subclasses:
            self.add_class(subclass)

    def by_themroles(self, roles: list[ThematicRoleType], only: bool = False) -> list[VerbClass]:
        """Find classes with specified thematic roles.

        Parameters
        ----------
        roles : list[ThematicRoleType]
            List of thematic role types to search for.
        only : bool
            If True, return only classes with exactly these roles.
            If False, return classes containing at least these roles.

        Returns
        -------
        list[VerbClass]
            Verb classes matching the role criteria.
        """
        if not roles:
            return []

        # Find classes with all specified roles
        matching_ids = None
        for role in roles:
            role_classes = self._classes_by_role.get(role, set())
            if matching_ids is None:
                matching_ids = role_classes.copy()
            else:
                matching_ids &= role_classes

        if matching_ids is None:
            return []

        # Get classes
        classes = [self._classes[cid] for cid in matching_ids]

        # If only exact matches requested, filter further
        if only:
            filtered = []
            role_set = set(roles)
            for verb_class in classes:
                class_roles = {r.type for r in verb_class.themroles}
                if class_roles == role_set:
                    filtered.append(verb_class)
            classes = filtered

        return sorted(classes, key=lambda c: c.id)

    def by_syntax(self, pattern: str) -> list[VerbClass]:
        """Find classes with matching syntactic patterns.

        Supports hierarchical matching where general patterns match specific ones:
        - "NP V PP" matches "NP V PP.instrument", "NP V PP.goal", etc.
        - "NP V NP *" matches any frame with NP V NP followed by anything

        Parameters
        ----------
        pattern : str
            Syntactic pattern to search for (e.g., "NP V PP", "NP V PP.instrument").

        Returns
        -------
        list[VerbClass]
            Verb classes with frames matching the pattern.
        """
        parser = SyntaxParser()
        query_pattern = parser.parse(pattern)
        matching_class_ids = set()

        for verb_class in self._classes.values():
            for frame in verb_class.frames:
                # Extract pattern from VerbNet frame syntax elements
                frame_pattern = parser.parse_verbnet_elements(frame.syntax.elements)

                # Check for pattern match
                if self._patterns_match(query_pattern, frame_pattern):
                    matching_class_ids.add(verb_class.id)
                    break  # Found match in this class

        classes = [self._classes[cid] for cid in matching_class_ids]
        return sorted(classes, key=lambda c: c.id)

    def _allows_pp_expansion(
        self, query_pattern: UnifiedSyntaxPattern, frame_pattern: UnifiedSyntaxPattern
    ) -> bool:
        """Check if query pattern can match frame pattern with PP expansion.

        For example, "NP VERB PREP NP" in query can match "NP VERB PP" in frame.
        """
        query_elements = query_pattern.elements
        frame_elements = frame_pattern.elements

        # Quick check: query should have exactly one more element than frame
        if len(query_elements) != len(frame_elements) + 1:
            return False

        # Look for PREP followed by NP in query that could match PP in frame
        for i in range(len(query_elements) - 1):
            if (
                query_elements[i].constituent == "PREP"
                and query_elements[i + 1].constituent == "NP"
                and i < len(frame_elements)
                and frame_elements[i].constituent == "PP"
            ):
                # Verify all other elements match
                query_before = query_elements[:i]
                query_after = query_elements[i + 2 :]  # Skip PREP and NP
                frame_before = frame_elements[:i]
                frame_after = frame_elements[i + 1 :]  # Skip PP

                if len(query_before) == len(frame_before) and len(query_after) == len(frame_after):
                    return True

        return False

    def _patterns_match(
        self, query_pattern: UnifiedSyntaxPattern, frame_pattern: UnifiedSyntaxPattern
    ) -> bool:
        """Check if query pattern matches frame pattern.

        Handles both exact matches and PP expansion where "PREP NP" matches "PP".
        """
        query_elements = query_pattern.elements
        frame_elements = frame_pattern.elements

        # Try exact match first
        if len(query_elements) == len(frame_elements):
            for q_elem, f_elem in zip(query_elements, frame_elements, strict=False):
                if q_elem.constituent != f_elem.constituent:
                    break
            else:
                return True  # All elements matched exactly

        # Try PP expansion: "PREP NP" in query matches "PP" in frame
        if len(query_elements) == len(frame_elements) + 1:
            query_idx = 0
            frame_idx = 0

            while query_idx < len(query_elements) and frame_idx < len(frame_elements):
                q_elem = query_elements[query_idx]
                f_elem = frame_elements[frame_idx]

                # Check for PREP NP -> PP conversion
                if (
                    q_elem.constituent == "PREP"
                    and query_idx + 1 < len(query_elements)
                    and query_elements[query_idx + 1].constituent == "NP"
                    and f_elem.constituent == "PP"
                ):
                    # PREP NP in query matches PP in frame
                    query_idx += 2  # Skip both PREP and NP
                    frame_idx += 1  # Skip PP
                elif q_elem.constituent == f_elem.constituent:
                    # Direct match
                    query_idx += 1
                    frame_idx += 1
                else:
                    # No match
                    return False

            # Check if we consumed all elements
            return query_idx == len(query_elements) and frame_idx == len(frame_elements)

        return False

    def by_predicate(self, predicate: PredicateType) -> list[VerbClass]:
        """Find classes using a specific semantic predicate.

        Parameters
        ----------
        predicate : PredicateType
            Semantic predicate to search for.

        Returns
        -------
        list[VerbClass]
            Verb classes using the predicate.
        """
        class_ids = self._classes_by_predicate.get(predicate, set())
        classes = [self._classes[cid] for cid in class_ids]
        return sorted(classes, key=lambda c: c.id)

    def by_predicates(
        self, predicates: list[PredicateType], require_all: bool = True
    ) -> list[VerbClass]:
        """Find classes using multiple semantic predicates.

        Parameters
        ----------
        predicates : list[PredicateType]
            List of semantic predicates to search for.
        require_all : bool
            If True, require all predicates. If False, require at least one.

        Returns
        -------
        list[VerbClass]
            Verb classes using the predicates.
        """
        if not predicates:
            return []

        if require_all:
            # Intersection of classes for all predicates
            matching_ids = None
            for predicate in predicates:
                pred_classes = self._classes_by_predicate.get(predicate, set())
                if matching_ids is None:
                    matching_ids = pred_classes.copy()
                else:
                    matching_ids &= pred_classes

            if matching_ids is None:
                return []
        else:
            # Union of classes for any predicate
            matching_ids = set()
            for predicate in predicates:
                matching_ids |= self._classes_by_predicate.get(predicate, set())

        classes = [self._classes[cid] for cid in matching_ids]
        return sorted(classes, key=lambda c: c.id)

    def by_restriction(
        self,
        role: ThematicRoleType,
        restriction_type: SelectionalRestrictionType,
        value: RestrictionValue,
    ) -> list[VerbClass]:
        """Find classes with selectional restrictions.

        Parameters
        ----------
        role : ThematicRoleType
            Thematic role to check restrictions on.
        restriction_type : SelectionalRestrictionType
            Type of selectional restriction.
        value : RestrictionValue
            Restriction value ("+" or "-").

        Returns
        -------
        list[VerbClass]
            Verb classes with matching restrictions.
        """
        matching_classes = []

        for verb_class in self._classes.values():
            for themrole in verb_class.themroles:
                if (
                    themrole.type == role
                    and themrole.sel_restrictions
                    and self._has_restriction(themrole.sel_restrictions, restriction_type, value)
                ):
                    matching_classes.append(verb_class)
                    break

        return sorted(matching_classes, key=lambda c: c.id)

    def _has_restriction(
        self,
        restrictions: SelectionalRestrictions,
        restriction_type: SelectionalRestrictionType,
        value: RestrictionValue,
    ) -> bool:
        """Check if restrictions contain a specific type and value.

        Parameters
        ----------
        restrictions : SelectionalRestrictions
            Restrictions to check.
        restriction_type : SelectionalRestrictionType
            Type to look for.
        value : RestrictionValue
            Value to match.

        Returns
        -------
        bool
            True if restriction found with matching type and value.
        """
        if isinstance(restrictions, SelectionalRestrictions):
            for restriction in restrictions.restrictions:
                if isinstance(restriction, SelectionalRestriction):
                    if restriction.type == restriction_type and restriction.value == value:
                        return True
                elif isinstance(restriction, SelectionalRestrictions) and self._has_restriction(
                    restriction, restriction_type, value
                ):
                    return True
        return False

    def by_members(self, lemmas: list[str]) -> list[VerbClass]:
        """Find classes containing specific member verbs.

        Parameters
        ----------
        lemmas : list[str]
            List of verb lemmas to search for.

        Returns
        -------
        list[VerbClass]
            Verb classes containing any of the specified members.
        """
        matching_ids = set()
        for lemma in lemmas:
            matching_ids |= self._classes_by_member.get(lemma, set())

        classes = [self._classes[cid] for cid in matching_ids]
        return sorted(classes, key=lambda c: c.id)

    def complex_search(
        self,
        predicates: list[PredicateType] | None = None,
        themroles: list[ThematicRoleType] | None = None,
        restrictions: (
            dict[ThematicRoleType, list[tuple[RestrictionValue, SelectionalRestrictionType]]] | None
        ) = None,
        syntax: str | None = None,
    ) -> list[VerbClass]:
        """Multi-criteria search for verb classes.

        Parameters
        ----------
        predicates : list[PredicateType] | None
            Semantic predicates to require.
        themroles : list[ThematicRoleType] | None
            Thematic roles to require.
        restrictions : dict[
            ThematicRoleType, list[tuple[RestrictionValue, SelectionalRestrictionType]]
        ] | None
            Selectional restrictions by role.
        syntax : str | None
            Syntactic pattern to match.

        Returns
        -------
        list[VerbClass]
            Verb classes matching all specified criteria.
        """
        # Start with all classes
        results = set(self._classes.keys())

        # Apply filters progressively
        results = self._filter_by_predicates(results, predicates)
        results = self._filter_by_thematic_roles(results, themroles)

        if not results:  # Early exit if no classes remain
            return []

        results = self._filter_by_restrictions(results, restrictions)
        results = self._filter_by_syntax(results, syntax)

        # Get class objects and sort
        classes = [self._classes[cid] for cid in results]
        return sorted(classes, key=lambda c: c.id)

    def _filter_by_predicates(
        self, class_ids: set[VerbClassID], predicates: list[PredicateType] | None
    ) -> set[VerbClassID]:
        """Filter class IDs by predicates.

        Parameters
        ----------
        class_ids : set[VerbClassID]
            Class IDs to filter.
        predicates : list[PredicateType] | None
            Predicates to require.

        Returns
        -------
        set[VerbClassID]
            Filtered class IDs.
        """
        if not predicates:
            return class_ids

        pred_classes = set()
        for predicate in predicates:
            pred_classes |= self._classes_by_predicate.get(predicate, set())
        return class_ids & pred_classes

    def _filter_by_thematic_roles(
        self, class_ids: set[VerbClassID], themroles: list[ThematicRoleType] | None
    ) -> set[VerbClassID]:
        """Filter class IDs by thematic roles.

        Parameters
        ----------
        class_ids : set[VerbClassID]
            Class IDs to filter.
        themroles : list[ThematicRoleType] | None
            Thematic roles to require.

        Returns
        -------
        set[VerbClassID]
            Filtered class IDs.
        """
        if not themroles:
            return class_ids

        role_classes = None
        for role in themroles:
            role_set = self._classes_by_role.get(role, set())
            if role_classes is None:
                role_classes = role_set.copy()
            else:
                role_classes &= role_set

        return class_ids & role_classes if role_classes else set()

    def _filter_by_restrictions(
        self,
        class_ids: set[VerbClassID],
        restrictions: (
            dict[ThematicRoleType, list[tuple[RestrictionValue, SelectionalRestrictionType]]] | None
        ),
    ) -> set[VerbClassID]:
        """Filter class IDs by selectional restrictions.

        Parameters
        ----------
        class_ids : set[VerbClassID]
            Class IDs to filter.
        restrictions : dict | None
            Selectional restrictions by role.

        Returns
        -------
        set[VerbClassID]
            Filtered class IDs.
        """
        if not restrictions:
            return class_ids

        restriction_classes: set[VerbClassID] = set()
        for role, role_restrictions in restrictions.items():
            role_class_set = self._get_classes_with_role_restrictions(role, role_restrictions)
            if restriction_classes:
                restriction_classes &= role_class_set
            else:
                restriction_classes = role_class_set

        return class_ids & restriction_classes

    def _get_classes_with_role_restrictions(
        self,
        role: ThematicRoleType,
        role_restrictions: list[tuple[RestrictionValue, SelectionalRestrictionType]],
    ) -> set[VerbClassID]:
        """Get classes with specific role restrictions.

        Parameters
        ----------
        role : ThematicRoleType
            Thematic role.
        role_restrictions : list[tuple[RestrictionValue, SelectionalRestrictionType]]
            List of restrictions for the role.

        Returns
        -------
        set[VerbClassID]
            Class IDs with matching restrictions.
        """
        role_class_set: set[str] = set()
        for value, rest_type in role_restrictions:
            role_rest_classes = {c.id for c in self.by_restriction(role, rest_type, value)}
            if role_class_set:
                role_class_set &= role_rest_classes
            else:
                role_class_set = role_rest_classes
        return role_class_set

    def _filter_by_syntax(
        self, class_ids: set[VerbClassID], syntax: str | None
    ) -> set[VerbClassID]:
        """Filter class IDs by syntax.

        Parameters
        ----------
        class_ids : set[VerbClassID]
            Class IDs to filter.
        syntax : str | None
            Syntactic pattern to match.

        Returns
        -------
        set[VerbClassID]
            Filtered class IDs.
        """
        if not syntax:
            return class_ids

        syntax_classes = {c.id for c in self.by_syntax(syntax)}
        return class_ids & syntax_classes

    def get_all_predicates(self) -> list[PredicateType]:
        """Get all unique semantic predicates.

        Returns
        -------
        list[PredicateType]
            Sorted list of unique predicates.
        """
        return sorted(self._classes_by_predicate.keys())

    def get_all_roles(self) -> list[ThematicRoleType]:
        """Get all unique thematic roles.

        Returns
        -------
        list[ThematicRoleType]
            Sorted list of unique roles.
        """
        return sorted(self._classes_by_role.keys())

    def get_all_members(self) -> list[str]:
        """Get all unique member lemmas.

        Returns
        -------
        list[str]
            Sorted list of unique member lemmas.
        """
        return sorted(self._classes_by_member.keys())

    def get_by_id(self, class_id: VerbClassID) -> VerbClass | None:
        """Get a verb class by its ID.

        Parameters
        ----------
        class_id : VerbClassID
            ID of the verb class to retrieve.

        Returns
        -------
        VerbClass | None
            The verb class if found, None otherwise.
        """
        return self._classes.get(class_id)

    def get_all_classes(self) -> list[VerbClass]:
        """Get all verb classes in the search index.

        Returns
        -------
        list[VerbClass]
            All verb classes sorted by ID.
        """
        return sorted(self._classes.values(), key=lambda c: c.id)

    def by_role_properties(
        self,
        optional: bool | None = None,
        indexed: bool | None = None,
        verb_specific: bool | None = None,
        pp_type: str | None = None,
    ) -> list[VerbClass]:
        """Find classes by role properties.

        Parameters
        ----------
        optional : bool | None, optional
            Filter for optional roles (? prefix).
        indexed : bool | None, optional
            Filter for indexed roles (_I, _J suffix).
        verb_specific : bool | None, optional
            Filter for verb-specific roles (V_ prefix).
        pp_type : str | None, optional
            Filter for specific PP type.

        Returns
        -------
        list[VerbClass]
            Classes with matching role properties.
        """
        matching_classes = []
        for verb_class in self._classes.values():
            filtered_roles = filter_roles_by_properties(
                verb_class.themroles,
                optional=optional,
                indexed=indexed,
                verb_specific=verb_specific,
                base_role=pp_type,  # pp_type maps to base_role
            )
            if filtered_roles:
                matching_classes.append(verb_class)

        return sorted(matching_classes, key=lambda c: c.id)

    def get_statistics(self) -> dict[str, int]:
        """Get search index statistics.

        Returns
        -------
        dict[str, int]
            Statistics about indexed data.
        """
        total_members = sum(len(c.members) for c in self._classes.values())
        total_frames = sum(len(c.frames) for c in self._classes.values())

        return {
            "class_count": len(self._classes),
            "unique_predicates": len(self._classes_by_predicate),
            "unique_roles": len(self._classes_by_role),
            "unique_members": len(self._classes_by_member),
            "total_members": total_members,
            "total_frames": total_frames,
        }

    @classmethod
    def from_jsonl_file(cls, path: Path | str) -> VerbNetSearch:
        """Load search index from JSON Lines file.

        Parameters
        ----------
        path : Path | str
            Path to JSON Lines file containing verb classes.

        Returns
        -------
        VerbNetSearch
            Search index populated with classes from file.

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

        classes = []
        with path.open(encoding="utf-8") as f:
            for line_raw in f:
                line = line_raw.strip()
                if line:
                    verb_class = VerbClass.model_validate_json(line)
                    classes.append(verb_class)

        return cls(classes)
