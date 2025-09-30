"""Parser for converting string patterns to unified syntactic format.

This module provides parsing capabilities for various syntactic pattern
notations, automatically detecting prepositions and semantic roles.

Classes
-------
SyntaxParser
    Main parser for syntactic patterns with support for wildcards,
    optional elements, and hierarchical specifications.

Examples
--------
>>> from glazing.syntax.parser import SyntaxParser
>>> parser = SyntaxParser()
>>> pattern = parser.parse("NP V PP.instrument")
>>> pattern = parser.parse("NP V PP.with")
>>> pattern = parser.parse("NP V NP *")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from glazing.syntax.models import BaseConstituentType, SyntaxElement, UnifiedSyntaxPattern

if TYPE_CHECKING:
    from glazing.verbnet.models import SyntaxElement as VNSyntaxElement


class SyntaxParser:
    """Parse syntactic patterns into unified format.

    Supports various pattern formats including wildcards, optional elements,
    and hierarchical PP specifications with automatic preposition detection.

    Attributes
    ----------
    COMMON_PREPOSITIONS : set[str]
        Set of common English prepositions for automatic detection.

    Methods
    -------
    parse(pattern)
        Parse a pattern string into UnifiedSyntaxPattern.
    """

    # Common English prepositions for automatic detection
    COMMON_PREPOSITIONS: ClassVar[set[str]] = {
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "among",
        "around",
        "at",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "by",
        "down",
        "during",
        "except",
        "for",
        "from",
        "in",
        "inside",
        "into",
        "near",
        "of",
        "off",
        "on",
        "out",
        "outside",
        "over",
        "through",
        "to",
        "toward",
        "under",
        "up",
        "upon",
        "with",
        "within",
        "without",
    }

    def parse(self, pattern: str) -> UnifiedSyntaxPattern:
        """Parse a syntactic pattern string.

        Supports formats:
        - "NP V PP" - general PP (matches all PPs)
        - "NP V PP.location" - PP with semantic role
        - "NP V PP[with]" - PP with specific preposition
        - "NP V[ING] NP" - Verb with morphological feature
        - "NP V VP[ING]" - VP with -ing form
        - "NP V NP.Patient" - NP with semantic role
        - "NP V NP.ARG1" - NP with PropBank role
        - "NP V NP *" - wildcard for any following element
        - "NP V NP?" - optional NP element

        Parameters
        ----------
        pattern : str
            Pattern string to parse.

        Returns
        -------
        UnifiedSyntaxPattern
            Parsed pattern ready for matching.

        Examples
        --------
        >>> parser = SyntaxParser()
        >>> p = parser.parse("NP V PP.location")
        >>> assert len(p.elements) == 3
        >>> assert p.elements[2].semantic_role == "location"
        """
        elements = []
        parts = pattern.strip().split()

        for part in parts:
            if part == "*":
                # Wildcard element
                elements.append(SyntaxElement(constituent="*", is_wildcard=True))
            elif part.endswith("?"):
                # Optional element
                elem = self._parse_element(part[:-1])
                elem.is_optional = True
                elements.append(elem)
            else:
                # Regular element
                elements.append(self._parse_element(part))

        return UnifiedSyntaxPattern(elements=elements, source_pattern=pattern)

    def _parse_element(self, part: str) -> SyntaxElement:
        """Parse a single syntactic element.

        Handles constituent types with optional bracket and dot specifications.
        - Bracket notation: morphological features (V[ING]) or heads (PP[with])
        - Dot notation: semantic roles (NP.Patient, PP.location, NP.ARG1)

        Parameters
        ----------
        part : str
            Element string like "NP", "PP[with]", "V[ING]", "NP.Patient".

        Returns
        -------
        SyntaxElement
            Parsed element with appropriate fields set.
        """
        # Parse bracket notation first: PP[with], V[ING], VP[ING]
        if "[" in part and "]" in part:
            bracket_start = part.index("[")
            bracket_end = part.index("]")
            base = part[:bracket_start]
            bracket_content = part[bracket_start + 1 : bracket_end]
            remainder = part[bracket_end + 1 :]
        else:
            base = part
            bracket_content = ""
            remainder = ""

        # Parse dot notation for semantic roles: NP.Patient, PP.location
        if "." in remainder:
            role_parts = remainder[1:].split(".", 1)
            semantic_role = role_parts[0] if role_parts else None
        elif "." in base:
            base_parts = base.split(".", 2)
            base = base_parts[0]
            semantic_role = base_parts[1] if len(base_parts) > 1 else None
        else:
            semantic_role = None

        const = self._normalize_constituent(base)
        elem = SyntaxElement(constituent=const)

        # Process bracket content (morphological features or heads)
        if bracket_content:
            if const in ["VERB", "V", "VP"]:
                # For verbs/VPs, brackets contain morphological features
                elem.features = self._parse_verb_features(bracket_content)
            else:
                # For other constituents (PP, NP), brackets can contain heads
                elem.head = bracket_content.lower()

        # Set semantic role (can be any string - dataset-specific)
        if semantic_role:
            elem.semantic_role = semantic_role

        return elem

    def _parse_verb_features(self, content: str) -> dict[str, str]:
        """Parse morphological features for verbs.

        Parameters
        ----------
        content : str
            Content within brackets for verb features.

        Returns
        -------
        dict[str, str]
            Morphological features dictionary.

        Raises
        ------
        ValueError
            If an unknown morphological feature is encountered.
        """
        features = {}

        parts = [p.strip() for p in content.split(",")]

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                features[key.strip()] = value.strip()
            elif part.upper() in ["ING", "INF", "BARE", "ED", "EN", "TO"]:
                features["form"] = part.lower()
            else:
                msg = f"Unknown verb morphological feature: '{part}'"
                raise ValueError(msg)

        return features

    def _normalize_constituent(self, const: str) -> BaseConstituentType:
        """Normalize constituent names.

        Converts shorthand forms to canonical forms.

        Parameters
        ----------
        const : str
            Constituent string to normalize.

        Returns
        -------
        BaseConstituentType
            Normalized constituent name.

        Raises
        ------
        ValueError
            If the constituent type is not recognized.
        """
        # Valid constituent types
        valid_constituents = {
            "NP",
            "VP",
            "V",
            "VERB",
            "PP",
            "P",
            "PREP",
            "AP",
            "A",
            "ADJ",
            "N",
            "NOUN",
            "D",
            "DET",
            "ADV",
            "ADVP",
            "S",
            "SBAR",
            "WH",
            "TO",
            "C",
            "COMP",
            "*",
        }

        normalized = const.upper()

        # Apply normalization mappings
        if normalized == "V":
            return "VERB"

        if normalized not in valid_constituents:
            msg = f"Unknown constituent type: '{const}'"
            raise ValueError(msg)

        return cast(BaseConstituentType, normalized)

    def parse_verbnet_description(self, description: str) -> UnifiedSyntaxPattern:
        """Parse VerbNet description.primary format.

        Parameters
        ----------
        description : str
            VerbNet description.primary string.

        Returns
        -------
        UnifiedSyntaxPattern
            Parsed pattern.

        Examples
        --------
        >>> parser = SyntaxParser()
        >>> p = parser.parse_verbnet_description("NP V PP.instrument")
        >>> assert p.elements[2].semantic_role == "instrument"
        """
        return self.parse(description)

    def parse_verbnet_elements(self, elements: list[VNSyntaxElement]) -> UnifiedSyntaxPattern:
        """Parse VerbNet syntax.elements format.

        Converts VerbNet's syntax element list into unified pattern.

        Parameters
        ----------
        elements : list[VNSyntaxElement]
            List of VerbNet syntax elements with pos and value fields.

        Returns
        -------
        UnifiedSyntaxPattern
            Unified pattern extracted from elements.
        """
        pattern_elements = []
        skip_next = False

        for i, elem in enumerate(elements):
            if skip_next:
                skip_next = False
                continue

            pos = elem.pos or ""
            value = getattr(elem, "value", "") or ""

            if pos == "PREP":
                # Start of a PP
                pp_elem = SyntaxElement(constituent="PP")

                # Add head value (specific preposition)
                if value:
                    pp_elem.head = value.lower()

                # Check next element for semantic role
                if i + 1 < len(elements):
                    next_elem = elements[i + 1]
                    if next_elem.pos == "NP" and getattr(next_elem, "value", None):
                        # Has semantic role
                        pp_elem.semantic_role = next_elem.value
                        skip_next = True

                pattern_elements.append(pp_elem)

            elif pos == "NP":
                np_elem = SyntaxElement(constituent="NP")
                if value:  # Has semantic role
                    np_elem.semantic_role = value
                pattern_elements.append(np_elem)

            else:
                # Other constituents
                const = self._normalize_constituent(pos)
                pattern_elements.append(SyntaxElement(constituent=const))

        return UnifiedSyntaxPattern(elements=pattern_elements)
