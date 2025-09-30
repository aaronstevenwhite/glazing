"""Unified syntactic pattern models with hierarchical type matching.

This module defines the core data models for unified syntactic patterns,
supporting hierarchical matching where general types match specific subtypes
with full confidence.

Type Aliases
------------
BaseConstituentType
    Base syntactic constituent types (NP, VP, PP, etc.)
SemanticRoleType
    Semantic role names across datasets
PrepositionValue
    Preposition values (single or multiple)

Classes
-------
SyntaxElement
    Single syntactic constituent with optional semantic specifications.
UnifiedSyntaxPattern
    Complete syntactic pattern with hierarchical matching capabilities.

Examples
--------
>>> from glazing.syntax.models import SyntaxElement, UnifiedSyntaxPattern
>>> # General PP matches all PP subtypes
>>> general_pp = SyntaxElement(constituent="PP")
>>> specific_pp = SyntaxElement(constituent="PP", semantic_role="instrument")
>>> matches, conf = general_pp.matches_hierarchically(specific_pp)
>>> assert matches and conf == 1.0  # Perfect match!
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from glazing.types import DatasetType

# Type aliases for syntactic constituents
type BaseConstituentType = Literal[
    "NP",  # Noun phrase
    "VP",  # Verb phrase
    "V",  # Verb (shorthand)
    "VERB",  # Verb (full form)
    "PP",  # Prepositional phrase
    "P",  # Preposition (shorthand)
    "PREP",  # Preposition (full form)
    "AP",  # Adjectival phrase
    "A",  # Adjective (shorthand)
    "ADJ",  # Adjective (full form)
    "N",  # Noun (shorthand)
    "NOUN",  # Noun (full form)
    "D",  # Determiner (shorthand)
    "DET",  # Determiner (full form)
    "ADV",  # Adverb
    "ADVP",  # Adverbial phrase
    "S",  # Sentence/clause
    "SBAR",  # Subordinate clause
    "WH",  # Wh-phrase
    "TO",  # To-infinitive
    "C",  # Complementizer (shorthand)
    "COMP",  # Complementizer (full form)
    "*",  # Wildcard
]

# Semantic role types (unified across datasets)
type SemanticRoleType = str  # "instrument", "goal", "Agent", "Theme", "ARG0", etc.

# Head values for lexical items
type HeadValue = str  # "with", "the", "quickly", etc.


class SyntaxElement(BaseModel):
    """Syntactic element with hierarchical matching.

    Represents a single syntactic constituent that may have semantic
    specifications (role, head) and matching flags (wildcard, optional).

    Attributes
    ----------
    constituent : BaseConstituentType
        The syntactic category (NP, PP, VERB, etc.)
    semantic_role : SemanticRoleType | None
        Semantic role (instrument, Agent, etc.)
    head : HeadValue | None
        Specific lexical head (with, the, quickly, etc.)
    features : dict[str, str]
        Morphological features (form: ing, tense: past, etc.)
    is_wildcard : bool
        Whether this is a wildcard element (*)
    is_optional : bool
        Whether this element is optional

    Methods
    -------
    matches_hierarchically(other)
        Check if this element matches another with confidence score.
    """

    constituent: BaseConstituentType
    semantic_role: SemanticRoleType | None = None  # For PP.instrument
    head: HeadValue | None = None  # For PP[with], DET[the], etc.
    features: dict[str, str] = Field(default_factory=dict)  # For V[ING], VP[INF], etc.
    is_wildcard: bool = False
    is_optional: bool = False

    def matches_hierarchically(self, other: SyntaxElement) -> tuple[bool, float]:
        """Check if this element matches another hierarchically.

        General types match specific subtypes with full confidence (1.0).
        Confidence < 1.0 only for wildcards, optional elements, or fuzzy matches.

        Parameters
        ----------
        other : SyntaxElement
            The element to match against.

        Returns
        -------
        tuple[bool, float]
            (matches, confidence) where confidence is 1.0 for perfect matches.

        Examples
        --------
        >>> general_pp = SyntaxElement(constituent="PP")
        >>> specific_pp = SyntaxElement(constituent="PP", semantic_role="instrument")
        >>> matches, conf = general_pp.matches_hierarchically(specific_pp)
        >>> assert matches and conf == 1.0  # General matches specific perfectly
        """
        # Wildcard matches everything with perfect confidence (maximally general)
        if self.is_wildcard:
            return (True, 1.0)
        if other.is_wildcard:
            return (True, 1.0)

        # Check base constituent compatibility
        if not self._constituents_compatible(other):
            return (False, 0.0)

        # Handle PP hierarchical matching
        if self.constituent in ["PP", "PREP"]:
            return self._match_pp_hierarchically(other)

        # Handle NP with roles
        if self.constituent == "NP":
            return self._match_np_hierarchically(other)

        # Handle other constituents with features
        return self._match_general_hierarchically(other)

    def __str__(self) -> str:
        """String representation of the syntax element."""
        if self.is_wildcard:
            return "*"

        result = str(self.constituent)

        # Add features in bracket notation
        if self.features:
            feature_parts = []
            for key, value in sorted(self.features.items()):
                if key == "form" and value.upper() in ["ING", "INF"]:
                    feature_parts.append(value.upper())
                else:
                    feature_parts.append(f"{key}:{value}")
            if feature_parts:
                result = f"{result}[{','.join(feature_parts)}]"

        # Add head in bracket notation
        if self.head:
            result = f"{result}[{self.head}]"

        # Add semantic role with dot notation
        if self.semantic_role:
            result = f"{result}.{self.semantic_role}"

        return result

    def _constituents_compatible(self, other: SyntaxElement) -> bool:
        """Check if constituent types are compatible."""
        # Normalize V <-> VERB
        if {self.constituent, other.constituent} <= {"V", "VERB"}:
            return True
        # PP matches PREP (PP = PREP NP conceptually)
        if {self.constituent, other.constituent} <= {"PP", "PREP"}:
            return True
        return self.constituent == other.constituent

    def _match_pp_hierarchically(self, other: SyntaxElement) -> tuple[bool, float]:  # noqa: PLR0911
        """Match PP elements hierarchically.

        Key principle: General PP matches ALL specific PPs with confidence 1.0
        """
        # General PP matches ANY specific PP perfectly
        if not self.semantic_role and not self.head and not self.features:
            # This is general PP - matches all PP subtypes
            return (True, 1.0)  # Perfect match!

        # PP.role matches same role only (case-insensitive)
        if self.semantic_role:
            matches = bool(
                other.semantic_role and self.semantic_role.lower() == other.semantic_role.lower()
            )
            return (matches, 1.0 if matches else 0.0)

        # PP[with] matches if heads match
        if self.head and other.head:
            # Check head overlap (support multiple heads like "for at on")
            self_heads = set(self.head.lower().split())
            other_heads = set(other.head.lower().split())
            matches = bool(self_heads & other_heads)
            return (matches, 1.0 if matches else 0.0)

        # Check features match
        if self.features and other.features:
            # Features must be compatible
            for key, value in self.features.items():
                if key in other.features and other.features[key] != value:
                    return (False, 0.0)
            return (True, 1.0)

        # PP[with] doesn't match PP.instrument (different dimensions)
        if (self.head and other.semantic_role) or (self.semantic_role and other.head):
            return (False, 0.0)

        return (False, 0.0)

    def _match_np_hierarchically(self, other: SyntaxElement) -> tuple[bool, float]:  # noqa: PLR0911
        """Match NP elements with optional semantic roles, heads, and features."""
        # General NP matches any NP perfectly
        if not self.semantic_role and not self.head and not self.features:
            return (True, 1.0)

        # Check semantic role match (case-insensitive)
        if (
            self.semantic_role
            and other.semantic_role
            and self.semantic_role.lower() != other.semantic_role.lower()
        ):
            return (False, 0.0)

        # Check head match
        if self.head and other.head and self.head.lower() != other.head.lower():
            return (False, 0.0)

        # Check features match (case-insensitive for values)
        if self.features and other.features:
            for key, value in self.features.items():
                if key in other.features and other.features[key].lower() != value.lower():
                    return (False, 0.0)

        # If we have specific requirements, other must have them too
        if self.semantic_role and not other.semantic_role:
            return (False, 0.0)
        if self.head and not other.head:
            return (False, 0.0)

        return (True, 1.0)

    def _match_general_hierarchically(self, other: SyntaxElement) -> tuple[bool, float]:  # noqa: PLR0911
        """Match general constituents with optional features, heads, and semantic roles."""
        # General element (no specific requirements) matches any specific element
        if not self.semantic_role and not self.head and not self.features:
            return (True, 1.0)

        # Check semantic role match (case-insensitive)
        if (
            self.semantic_role
            and other.semantic_role
            and self.semantic_role.lower() != other.semantic_role.lower()
        ):
            return (False, 0.0)

        # Check head match
        if self.head and other.head and self.head.lower() != other.head.lower():
            return (False, 0.0)

        # Check features match (case-insensitive for values)
        if self.features and other.features:
            for key, value in self.features.items():
                if key in other.features and other.features[key].lower() != value.lower():
                    return (False, 0.0)

        # If we have specific requirements, other must have them too
        if self.semantic_role and not other.semantic_role:
            return (False, 0.0)
        if self.head and not other.head:
            return (False, 0.0)
        if self.features and not other.features:
            return (False, 0.0)

        return (True, 1.0)


class UnifiedSyntaxPattern(BaseModel):
    """Unified syntactic pattern with hierarchical matching.

    Represents a complete syntactic pattern that can match other patterns
    using hierarchical type matching and wildcards.

    Attributes
    ----------
    elements : list[SyntaxElement]
        Ordered list of syntactic elements.
    normalized : str
        Canonical string representation.
    source_dataset : DatasetType | None
        Dataset this pattern came from.
    source_pattern : str
        Original pattern string.

    Methods
    -------
    matches_hierarchically(other, allow_wildcards)
        Match against another pattern with confidence scoring.
    """

    elements: list[SyntaxElement]
    normalized: str = Field(default="")
    source_dataset: DatasetType | None = None
    source_pattern: str = Field(default="")

    def model_post_init(self, __context: dict[str, str] | None) -> None:
        """Generate normalized form if not provided."""
        if not self.normalized and self.elements:
            parts = []
            for elem in self.elements:
                if elem.is_wildcard:
                    parts.append("*")
                elif elem.constituent == "V":
                    parts.append("VERB")
                else:
                    parts.append(elem.constituent)
            self.normalized = " ".join(parts)

    @classmethod
    def from_verbnet_synrestrs(
        cls,
        elements: list[SyntaxElement],
        synrestrs: list[dict[str, str]] | None = None,
        source_pattern: str = "",
    ) -> UnifiedSyntaxPattern:
        """Create pattern from VerbNet elements with syntactic restrictions.

        Parameters
        ----------
        elements : list[SyntaxElement]
            Base syntax elements.
        synrestrs : list[dict[str, str]] | None
            VerbNet syntactic restrictions with type and value.
        source_pattern : str
            Original VerbNet pattern string.

        Returns
        -------
        UnifiedSyntaxPattern
            Pattern with morphological features extracted from synrestrs.
        """
        if synrestrs:
            feature_elements = []
            for elem in elements:
                new_elem = SyntaxElement(
                    constituent=elem.constituent,
                    semantic_role=elem.semantic_role,
                    head=elem.head,
                    features=elem.features.copy(),
                    is_wildcard=elem.is_wildcard,
                    is_optional=elem.is_optional,
                )

                # Extract morphological features from synrestrs
                if elem.constituent in ["V", "VERB", "VP"]:
                    for synrestr in synrestrs:
                        restr_type = synrestr.get("type", "")
                        restr_value = synrestr.get("value", "")

                        if restr_value == "+" and restr_type in [
                            "oc_ing",
                            "ac_ing",
                            "be_sc_ing",
                        ]:
                            new_elem.features["form"] = "ing"
                        elif restr_value == "+" and restr_type in ["oc_to_inf", "to_inf"]:
                            new_elem.features["form"] = "inf"

                feature_elements.append(new_elem)
        else:
            feature_elements = elements

        return cls(
            elements=feature_elements,
            source_pattern=source_pattern,
            source_dataset="verbnet",
        )

    def normalize_features(self) -> UnifiedSyntaxPattern:
        """Create normalized pattern with standardized feature representation.

        Returns
        -------
        UnifiedSyntaxPattern
            Pattern with normalized morphological features.
        """
        normalized_elements = []
        for elem in self.elements:
            new_elem = SyntaxElement(
                constituent=elem.constituent,
                semantic_role=elem.semantic_role,
                head=elem.head,
                features={},
                is_wildcard=elem.is_wildcard,
                is_optional=elem.is_optional,
            )

            # Normalize features
            for key, value in elem.features.items():
                if key == "form":
                    if value.lower() in ["ing", "progressive", "gerund"]:
                        new_elem.features["form"] = "ing"
                    elif value.lower() in ["inf", "infinitive", "to_inf"]:
                        new_elem.features["form"] = "inf"
                    else:
                        new_elem.features[key] = value.lower()
                else:
                    new_elem.features[key] = value.lower()

            normalized_elements.append(new_elem)

        return UnifiedSyntaxPattern(
            elements=normalized_elements,
            source_pattern=self.source_pattern,
            source_dataset=self.source_dataset,
        )

    def _handle_pp_expansion(
        self,
        q_elem: SyntaxElement,
        t_elem: SyntaxElement,
        target_idx: int,
        other: UnifiedSyntaxPattern,
    ) -> int:
        """Handle PP -> PREP NP expansion."""
        if (
            q_elem.constituent == "PP"
            and t_elem.constituent == "PREP"
            and target_idx < len(other.elements)
            and other.elements[target_idx].constituent == "NP"
        ):
            # Skip the NP that follows PREP in target
            return target_idx + 1
        return target_idx

    def _handle_wildcard_match(
        self,
        query_idx: int,
        target_idx: int,
        total_score: float,
        matched_count: int,
        other: UnifiedSyntaxPattern,
    ) -> tuple[bool, float] | None:
        """Handle wildcard element matching."""
        if query_idx == len(self.elements) - 1:
            # Last element is wildcard, matches remaining
            remaining = len(other.elements) - target_idx
            if remaining > 0:
                total_score += 0.95  # Slight penalty for wildcard
                matched_count += 1
            return (True, total_score / max(matched_count, 1))
        return None

    def _handle_remaining_elements(
        self, query_idx: int, total_score: float, matched_count: int
    ) -> tuple[bool, float]:
        """Handle remaining query elements."""
        while query_idx < len(self.elements):
            elem = self.elements[query_idx]
            if elem.is_optional:
                # Optional elements at end
                total_score += 0.9
                matched_count += 1
            elif elem.is_wildcard:
                # Trailing wildcard matches empty
                total_score += 0.95
                matched_count += 1
            else:
                # Required element not matched
                return (False, 0.0)
            query_idx += 1

        # Calculate final confidence
        if matched_count > 0:
            final_score = total_score / matched_count
            return (True, final_score)
        return (False, 0.0)

    def matches_hierarchically(
        self, other: UnifiedSyntaxPattern, allow_wildcards: bool = True
    ) -> tuple[bool, float]:
        """Match patterns hierarchically with confidence scoring.

        Parameters
        ----------
        other : UnifiedSyntaxPattern
            Pattern to match against.
        allow_wildcards : bool
            Whether to process wildcard elements.

        Returns
        -------
        tuple[bool, float]
            (matches, confidence) where confidence = 1.0 for perfect matches.

        Examples
        --------
        >>> # "NP V PP" matches "NP V PP.instrument" perfectly
        >>> general = UnifiedSyntaxPattern(elements=[
        ...     SyntaxElement(constituent="NP"),
        ...     SyntaxElement(constituent="VERB"),
        ...     SyntaxElement(constituent="PP")
        ... ])
        >>> specific = UnifiedSyntaxPattern(elements=[
        ...     SyntaxElement(constituent="NP"),
        ...     SyntaxElement(constituent="VERB"),
        ...     SyntaxElement(constituent="PP", semantic_role="instrument")
        ... ])
        >>> matches, conf = general.matches_hierarchically(specific)
        >>> assert matches and conf == 1.0
        """
        query_idx = 0
        target_idx = 0
        total_score = 0.0
        matched_count = 0

        while query_idx < len(self.elements) and target_idx < len(other.elements):
            q_elem = self.elements[query_idx]
            t_elem = other.elements[target_idx]

            # Try to match elements
            matches, score = q_elem.matches_hierarchically(t_elem)

            if matches:
                total_score += score
                matched_count += 1
                query_idx += 1
                target_idx += 1
                target_idx = self._handle_pp_expansion(q_elem, t_elem, target_idx, other)

            elif q_elem.is_optional:
                # Optional element doesn't match, small penalty
                total_score += 0.9
                matched_count += 1
                query_idx += 1

            elif q_elem.is_wildcard and allow_wildcards:
                # Check if it's the last wildcard
                result = self._handle_wildcard_match(
                    query_idx, target_idx, total_score, matched_count, other
                )
                if result is not None:
                    return result
                # Wildcard in middle
                total_score += 0.95
                matched_count += 1
                query_idx += 1
                target_idx += 1
            else:
                return (False, 0.0)

        return self._handle_remaining_elements(query_idx, total_score, matched_count)
