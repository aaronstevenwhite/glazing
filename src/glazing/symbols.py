"""Base symbol models for all datasets.

This module provides Pydantic v2 models for parsed symbols across all datasets,
ensuring consistent normalization and type safety. All symbol parsers inherit
from BaseSymbol to provide unified structure and validation.

Classes
-------
BaseSymbol
    Base model for all parsed symbols with validation and normalization.

Functions
---------
validate_symbol_type
    Validate symbol type matches expected values.
validate_dataset_name
    Validate dataset name matches supported datasets.

Type Aliases
------------
DatasetName
    Literal type for valid dataset names.
SymbolType
    Literal type for valid symbol types.

Examples
--------
>>> from glazing.symbols import BaseSymbol
>>> symbol = BaseSymbol(
...     raw_string="Motion_Directional",
...     normalized="motion_directional",
...     symbol_type="frame",
...     dataset="framenet"
... )
>>> symbol.confidence
1.0
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Type aliases for dataset names
type DatasetName = Literal["framenet", "propbank", "verbnet", "wordnet"]

# Type aliases for symbol types
type SymbolType = Literal[
    "frame",
    "frame_element",
    "frame_relation",
    "roleset",
    "argument",
    "verb_class",
    "thematic_role",
    "synset",
    "sense_key",
    "lemma_key",
]


class BaseSymbol(BaseModel):
    """Base model for all parsed symbols.

    Attributes
    ----------
    raw_string : str
        Original unparsed string.
    normalized : str
        Strongly normalized version (lowercase, spaces to underscores).
    symbol_type : SymbolType
        Type of symbol.
    dataset : DatasetName
        Source dataset.
    confidence : float
        Confidence score (1.0 for exact, <1.0 for fuzzy matches).
    """

    raw_string: str = Field(..., min_length=1)
    normalized: str = Field(..., min_length=1)
    symbol_type: SymbolType
    dataset: DatasetName
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("normalized")
    @classmethod
    def validate_normalized(cls, v: str) -> str:
        """Ensure normalized field follows rules."""
        # Must be lowercase
        if v != v.lower():
            msg = f"Normalized field must be lowercase: {v}"
            raise ValueError(msg)
        # No spaces allowed (should be underscores)
        if " " in v:
            msg = f"Normalized field cannot contain spaces: {v}"
            raise ValueError(msg)
        # No consecutive underscores
        if "__" in v:
            msg = f"Normalized field cannot have consecutive underscores: {v}"
            raise ValueError(msg)
        # Must not start or end with underscore
        if v.startswith("_") or v.endswith("_"):
            msg = f"Normalized field cannot start/end with underscore: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def normalize_string(cls, s: str) -> str:
        """Apply standard normalization rules.

        Parameters
        ----------
        s : str
            String to normalize.

        Returns
        -------
        str
            Normalized string.
        """
        # Convert to lowercase
        normalized = s.lower()

        # Replace spaces and hyphens with underscores
        normalized = re.sub(r"[\s\-]+", "_", normalized)

        # Collapse multiple underscores
        normalized = re.sub(r"_{2,}", "_", normalized)

        # Strip leading/trailing underscores
        normalized = normalized.strip("_")

        # If empty after normalization, raise error
        if not normalized:
            msg = f"String normalizes to empty: {s!r}"
            raise ValueError(msg)

        return normalized
