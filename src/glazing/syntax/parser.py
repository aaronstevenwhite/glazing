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
        - "NP V PP.instrument" - PP with semantic role
        - "NP V PP.with" - PP with specific preposition
        - "NP V PP.with.instrument" - PP with both
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
        >>> p = parser.parse("NP V PP")
        >>> assert len(p.elements) == 3
        >>> assert p.elements[2].constituent == "PP"
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

        Handles constituent types with optional role/preposition specifications.
        Automatically detects whether a specification is a preposition or
        semantic role.

        Parameters
        ----------
        part : str
            Element string like "NP", "PP.instrument", "PP.with".

        Returns
        -------
        SyntaxElement
            Parsed element with appropriate fields set.
        """
        if "." not in part:
            # Simple constituent without specifications
            const = self._normalize_constituent(part)
            return SyntaxElement(constituent=const)

        # Handle dotted notation (PP.xxx)
        base, *specs = part.split(".")
        base = self._normalize_constituent(base)
        elem = SyntaxElement(constituent=base)

        for spec in specs:
            # Detect if it's a preposition or semantic role
            if spec.lower() in self.COMMON_PREPOSITIONS:
                # It's a preposition
                elem.preposition = spec.lower()
            else:
                # It's a semantic role
                elem.semantic_role = spec

        return elem

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
        """
        # Map common variants to canonical forms
        normalized = const.upper()
        if normalized == "V":
            return "VERB"

        # Cast to ensure type compatibility - Python's type system
        # doesn't know that these specific values are BaseConstituentType
        return cast(BaseConstituentType, normalized)

    def parse_verbnet_description(self, description: str) -> UnifiedSyntaxPattern:
        """Parse VerbNet description.primary format.

        Special parser for VerbNet's description format which uses
        notation like "NP V PP.instrument".

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
        # For now, use the main parser (format is compatible)
        return self.parse(description)

    def parse_verbnet_elements(self, elements: list[VNSyntaxElement]) -> UnifiedSyntaxPattern:
        """Parse VerbNet syntax.elements format.

        Converts VerbNet's syntax element list into unified pattern.

        Parameters
        ----------
        elements : list
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

                # Add preposition value
                if value:
                    pp_elem.preposition = value.lower()

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
                    np_elem.argument_role = value
                pattern_elements.append(np_elem)

            else:
                # Other constituents
                const = self._normalize_constituent(pos)
                pattern_elements.append(SyntaxElement(constituent=const))

        return UnifiedSyntaxPattern(elements=pattern_elements)
