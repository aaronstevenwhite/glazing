"""Unified syntactic search across linguistic datasets.

This module provides a unified interface for searching syntactic patterns
across FrameNet, PropBank, VerbNet, and WordNet, with support for hierarchical
type matching and wildcards.

Classes
-------
SyntaxElement
    Single syntactic constituent with optional semantic role.
UnifiedSyntaxPattern
    Complete syntactic pattern with hierarchical matching.
SyntaxParser
    Parser for converting string patterns to unified format.

Examples
--------
>>> from glazing.syntax import SyntaxParser
>>> parser = SyntaxParser()
>>> pattern = parser.parse("NP V PP")
>>> # Matches "NP V PP.instrument", "NP V PP.goal", etc.
"""

from glazing.syntax.models import SyntaxElement, UnifiedSyntaxPattern
from glazing.syntax.parser import SyntaxParser

__all__ = ["SyntaxElement", "SyntaxParser", "UnifiedSyntaxPattern"]
