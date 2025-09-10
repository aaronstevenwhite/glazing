"""Shared type definitions used across all linguistic resources.

This module defines type aliases and literal types that are used throughout
the glazing package for cross-dataset functionality. These types enable
type-safe cross-referencing between FrameNet, PropBank, VerbNet, and WordNet.

Type Aliases
------------
DatasetType
    The four primary linguistic datasets.
ResourceType
    Extended set including additional resources.
MappingSource
    Provenance of cross-dataset mappings.
LogicType
    Logical operators for restrictions.
MappingConfidenceScore
    Confidence score between 0.0 and 1.0.
VersionString
    Semantic version string format.

Notes
-----
This module uses Python 3.13+ type syntax with the `type` statement
for all type aliases. All types are designed to be imported and used
across the various submodules of the glazing package.

Examples
--------
>>> from glazing.types import DatasetType, MappingSource
>>> dataset: DatasetType = "FrameNet"
>>> source: MappingSource = "manual"
"""

from typing import Annotated, Literal

from pydantic import Field

# Use Python 3.13+ type statement for all aliases

# Primary dataset types
type DatasetType = Literal["FrameNet", "PropBank", "VerbNet", "WordNet"]

# Extended resource types including additional datasets
type ResourceType = Literal[
    "VerbNet", "FrameNet", "WordNet", "PropBank", "AMR", "UMR", "Flickr", "THYME", "Spatial"
]

# Mapping source provenance
type MappingSource = Literal[
    "manual",  # Manually created mapping
    "automatic",  # Automatically generated
    "manual+strict-conv",  # Manual with strict conversion
    "manualchecks",  # Manual with additional checks
    "auto",  # Short for automatic
    "gold",  # Gold standard annotation
    "silver",  # Silver standard (less reliable)
    "legacy",  # From previous version
    "inherited",  # Inherited from parent class/frame
]

# Logical operators for combining restrictions
type LogicType = Literal["or", "and"]

# Confidence score for mappings (0.0 to 1.0)
type MappingConfidenceScore = Annotated[
    float, Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
]

# Version string following semantic versioning
type VersionString = Annotated[
    str,
    Field(
        pattern=r"^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)?$",
        description="Semantic version string (e.g., '1.0.0', '2.1.0-alpha')",
    ),
]

# Mapping type classifications
type MappingType = Literal[
    "direct",  # Direct one-to-one mapping
    "inherited",  # Inherited from parent structure
    "inferred",  # Inferred through analysis
    "partial",  # Partial/incomplete mapping
    "transitive",  # Through intermediate resource
    "manual",  # Manually specified
    "automatic",  # Automatically generated
    "hybrid",  # Combination of methods
]

# Alignment types for cross-dataset alignments
type AlignmentType = Literal[
    "exact",  # Exact match
    "equivalent",  # Semantically equivalent
    "subsumes",  # Source subsumes target
    "subsumed_by",  # Source subsumed by target
    "overlaps",  # Partial overlap
    "related",  # Related but not equivalent
    "contradicts",  # Contradictory mappings
]

# Conflict types in mappings
type ConflictType = Literal[
    "ambiguous",  # Multiple equally valid mappings
    "contradictory",  # Mutually exclusive mappings
    "version_mismatch",  # Different dataset versions
    "inheritance",  # Conflict in inheritance chain
]

# Validation status for mappings
type ValidationStatus = Literal[
    "validated",  # Fully validated
    "unvalidated",  # Not yet validated
    "disputed",  # Under dispute
    "deprecated",  # No longer recommended
]

# Common dataset operations
type OperationType = Literal[
    "search",  # Search operation
    "load",  # Data loading
    "convert",  # Format conversion
    "validate",  # Data validation
    "index",  # Index building
    "cache",  # Cache operation
]

# Regex patterns for common identifier formats
# These are used for validation across modules

# Frame/Class/Roleset ID patterns
FRAME_ID_PATTERN = r"^\d+$"  # FrameNet frame ID (numeric)
VERBNET_CLASS_PATTERN = r"^[a-z_]+-[0-9]+(?:\.[0-9]+)*(?:-[0-9]+)*$"  # e.g., "give-13.1-1"
PROPBANK_ROLESET_PATTERN = r"^[a-zA-Z0-9_.-]+\.\d+$"  # e.g., "give.01"
WORDNET_OFFSET_PATTERN = r"^[0-9]{8}$"  # 8-digit zero-padded

# Sense key patterns
WORDNET_SENSE_KEY_PATTERN = r"^[a-z0-9_.-]+%[1-5]:[0-9]{2}:[0-9]{2}:[a-z0-9_.-]*:[0-9]*$"
VERBNET_KEY_PATTERN = r"^[a-z_-]+#\d+$"  # e.g., "give#2"

# Percentage notation (VerbNet's WordNet reference format)
PERCENTAGE_NOTATION_PATTERN = r"^[a-z_-]+%[1-5]:[0-9]{2}:[0-9]{2}$"  # e.g., "give%2:40:00"

# Name validation patterns
FRAME_NAME_PATTERN = r"^[A-Z][A-Za-z0-9_]*$"  # FrameNet frame names
FE_NAME_PATTERN = r"^[A-Z][A-Za-z0-9_]*$"  # Frame element names
LEMMA_PATTERN = r"^[a-z][a-z0-9_\'-]*$"  # Word lemmas

# Color validation for FrameNet
HEX_COLOR_PATTERN = r"^[0-9A-F]{6}$"  # 6-digit hex color


# Shared error types
class DataNotLoadedError(Exception):
    """Raised when attempting to access data that hasn't been loaded."""


class InvalidReferenceError(Exception):
    """Raised when a cross-reference cannot be resolved."""


class MappingConflictError(Exception):
    """Raised when conflicting mappings are detected."""


class ValidationError(Exception):
    """Raised when data fails validation against schema."""


# Type guards for runtime checking
def is_dataset_type(value: str) -> bool:
    """Check if a string is a valid DatasetType.

    Parameters
    ----------
    value : str
        The string to check.

    Returns
    -------
    bool
        True if the value is a valid DatasetType.
    """
    return value in {"FrameNet", "PropBank", "VerbNet", "WordNet"}


def is_resource_type(value: str) -> bool:
    """Check if a string is a valid ResourceType.

    Parameters
    ----------
    value : str
        The string to check.

    Returns
    -------
    bool
        True if the value is a valid ResourceType.
    """
    return value in {
        "VerbNet",
        "FrameNet",
        "WordNet",
        "PropBank",
        "AMR",
        "UMR",
        "Flickr",
        "THYME",
        "Spatial",
    }


def is_valid_confidence(value: float) -> bool:
    """Check if a float is a valid confidence score.

    Parameters
    ----------
    value : float
        The value to check.

    Returns
    -------
    bool
        True if the value is between 0.0 and 1.0 inclusive.
    """
    return 0.0 <= value <= 1.0
