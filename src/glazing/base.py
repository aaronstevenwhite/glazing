"""Base models and utilities for the glazing package.

This module provides base classes and common functionality used throughout
the glazing package. All dataset-specific models inherit from these base
classes to ensure consistent behavior and validation.

Classes
-------
GlazingBaseModel
    Extended Pydantic BaseModel with JSON Lines support.
CrossReferenceBase
    Base class for cross-dataset references.
MappingBase
    Base class for dataset mappings.

Functions
---------
validate_pattern
    Validate a string against a regex pattern.
validate_confidence_score
    Validate a confidence score is between 0.0 and 1.0.

Notes
-----
This module uses Pydantic v2 for data validation and serialization.
All models support JSON Lines export/import for efficient data storage.
"""

from __future__ import annotations

import json
import re
from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from glazing.framenet.types import FE_NAME_PATTERN, FRAME_NAME_PATTERN
from glazing.propbank.types import ROLESET_ID_PATTERN as PROPBANK_ROLESET_PATTERN
from glazing.types import (
    FRAME_ID_PATTERN,
    HEX_COLOR_PATTERN,
    LEMMA_PATTERN,
    VERBNET_CLASS_PATTERN,
    VERBNET_KEY_PATTERN,
    ConflictType,
    DatasetType,
    MappingConfidenceScore,
    MappingSource,
    MappingType,
    ValidationStatus,
    VersionString,
)
from glazing.wordnet.types import (
    PERCENTAGE_NOTATION_PATTERN,
    WORDNET_OFFSET_PATTERN,
    WORDNET_SENSE_KEY_PATTERN,
)

type ModelValue = str | int | float | bool | None | list[ModelValue] | dict[str, ModelValue]


class GlazingBaseModel(BaseModel):
    """Base model class for all glazing data models.

    Extends Pydantic's BaseModel with JSON Lines support and common
    validation functionality used across all linguistic datasets.

    Attributes
    ----------
    model_config : ConfigDict
        Pydantic configuration for the model.

    Methods
    -------
    to_jsonl()
        Export model to JSON Lines format.
    from_jsonl(lines)
        Load model from JSON Lines format.
    to_json_lines_file(path)
        Write model to JSON Lines file.
    from_json_lines_file(path)
        Load model from JSON Lines file.

    Examples
    --------
    >>> class MyModel(GlazingBaseModel):
    ...     name: str
    ...     value: int
    >>> model = MyModel(name="test", value=42)
    >>> jsonl = model.to_jsonl()
    >>> loaded = MyModel.from_jsonl(jsonl)
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=False,
        json_schema_extra={"description": "Base model for glazing package data structures"},
    )

    def to_jsonl(self) -> str:
        """Export model to JSON Lines format.

        Returns
        -------
        str
            JSON Lines string representation of the model.
        """
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> Self:
        """Load model from a JSON Lines string.

        Parameters
        ----------
        line : str
            Single line of JSON Lines format.

        Returns
        -------
        Self
            Instance of the model class.

        Raises
        ------
        ValueError
            If the JSON is invalid or doesn't match the model schema.
        """
        data = json.loads(line)
        return cls.model_validate(data)

    def to_json_lines_file(self, path: Path | str) -> None:
        """Write model to a JSON Lines file.

        Parameters
        ----------
        path : Path | str
            Path to the output file.
        """
        path = Path(path)
        with path.open("w", encoding="utf-8") as f:
            f.write(self.to_jsonl())
            f.write("\n")

    @classmethod
    def from_json_lines_file(
        cls, path: Path | str, skip_errors: bool = False
    ) -> Generator[Self, None, None]:
        """Load models from a JSON Lines file.

        Parameters
        ----------
        path : Path | str
            Path to the JSON Lines file.
        skip_errors : bool, default=False
            If True, skip lines that fail validation.

        Yields
        ------
        Self
            Instances of the model class.

        Raises
        ------
        ValueError
            If skip_errors is False and a line fails validation.
        """
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            for line_num, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    yield cls.from_jsonl(line)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    if not skip_errors:
                        msg = f"Error on line {line_num}: {e}"
                        raise ValueError(msg) from e

    @classmethod
    def validate_many(
        cls, items: Iterable[dict[str, ModelValue]]
    ) -> list[tuple[Self | None, Exception | None]]:
        """Validate multiple items and return results with errors.

        Parameters
        ----------
        items : Iterable[dict[str, ModelValue]]
            Items to validate.

        Returns
        -------
        list[tuple[Self | None, Exception | None]]
            List of (model, error) tuples. If validation succeeds,
            error is None. If validation fails, model is None.
        """
        results: list[tuple[Self | None, Exception | None]] = []
        for item in items:
            try:
                model = cls.model_validate(item)
                results.append((model, None))
            except (ValueError, TypeError) as e:
                results.append((None, e))
        return results


class CrossReferenceBase(GlazingBaseModel):
    """Base class for cross-dataset references.

    Provides common fields and validation for references between
    FrameNet, PropBank, VerbNet, and WordNet.

    Attributes
    ----------
    source_dataset : DatasetType
        The source dataset.
    source_id : str
        Identifier in the source dataset.
    target_dataset : DatasetType
        The target dataset.
    target_id : str | list[str]
        Identifier(s) in the target dataset.
    mapping_type : MappingType
        Type of mapping relationship.
    confidence : MappingConfidenceScore | None
        Confidence score for the mapping.
    mapping_source : MappingSource | None
        Provenance of the mapping.
    notes : str | None
        Additional notes about the mapping.
    """

    source_dataset: DatasetType
    source_id: str
    target_dataset: DatasetType
    target_id: str | list[str]
    mapping_type: MappingType = "direct"
    confidence: MappingConfidenceScore | None = None
    mapping_source: MappingSource | None = None
    notes: str | None = None

    @field_validator("source_id", "target_id")
    @classmethod
    def validate_ids(cls, v: str | list[str]) -> str | list[str]:
        """IDs must be non-empty strings."""
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("ID cannot be empty")
        elif isinstance(v, list):
            if not v:
                raise ValueError("ID list cannot be empty")
            for item in v:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("All IDs must be non-empty strings")
        return v

    @model_validator(mode="after")
    def validate_datasets(self) -> Self:
        """Source and target must be different datasets."""
        if self.source_dataset == self.target_dataset and self.mapping_type not in (
            "inherited",
            "transitive",
        ):
            msg = f"Source and target datasets cannot be the same for {self.mapping_type} mappings"
            raise ValueError(msg)
        return self

    def get_confidence_score(self) -> float:
        """Get confidence score with default fallback.

        Returns
        -------
        float
            Confidence score, or 0.5 if not specified.
        """
        return self.confidence if self.confidence is not None else 0.5

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if this is a high-confidence mapping.

        Parameters
        ----------
        threshold : float, default=0.8
            Minimum confidence score for high confidence.

        Returns
        -------
        bool
            True if confidence exceeds threshold.
        """
        return self.get_confidence_score() >= threshold


class MappingBase(GlazingBaseModel):
    """Base class for mapping metadata.

    Provides common fields for tracking mapping provenance,
    validation status, and versioning.

    Attributes
    ----------
    created_date : datetime
        When the mapping was created.
    created_by : str
        Person or system that created the mapping.
    modified_date : datetime | None
        When the mapping was last modified.
    modified_by : str | None
        Person or system that last modified the mapping.
    version : VersionString
        Dataset version this mapping was created for.
    validation_status : ValidationStatus
        Current validation status.
    validation_method : str | None
        How the mapping was validated.
    """

    created_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str
    modified_date: datetime | None = None
    modified_by: str | None = None
    version: VersionString
    validation_status: ValidationStatus = "unvalidated"
    validation_method: str | None = None

    @model_validator(mode="after")
    def validate_modification(self) -> Self:
        """If modified_by is set, modified_at must also be set."""
        if self.modified_date and not self.modified_by:
            raise ValueError("modified_by required when modified_date is set")
        if self.modified_by and not self.modified_date:
            raise ValueError("modified_date required when modified_by is set")
        return self

    def mark_validated(self, method: str, validator: str | None = None) -> None:
        """Mark the mapping as validated.

        Parameters
        ----------
        method : str
            Validation method used.
        validator : str | None
            Person or system that performed validation.
        """
        # Temporarily disable validation to set both fields
        original_config = self.model_config.get("validate_assignment", True)
        self.model_config["validate_assignment"] = False

        try:
            self.validation_status = "validated"
            self.validation_method = method
            if validator:
                self.modified_by = validator
                self.modified_date = datetime.now(UTC)
        finally:
            self.model_config["validate_assignment"] = original_config


# Common field validators as standalone functions


def validate_pattern(value: str, pattern: str, field_name: str) -> str:
    """Validate a string against a regex pattern.

    Parameters
    ----------
    value : str
        The value to validate.
    pattern : str
        The regex pattern to match.
    field_name : str
        Name of the field being validated (for error messages).

    Returns
    -------
    str
        The validated value.

    Raises
    ------
    ValueError
        If the value doesn't match the pattern.
    """
    if not re.match(pattern, value):
        msg = f"Invalid {field_name} format: {value}"
        raise ValueError(msg)
    return value


def validate_frame_id(value: int | str) -> str:
    """Check FrameNet frame ID format (positive integer)."""
    str_value = str(value)
    return validate_pattern(str_value, FRAME_ID_PATTERN, "frame ID")


def validate_frame_name(value: str) -> str:
    """Check FrameNet frame name format."""
    return validate_pattern(value, FRAME_NAME_PATTERN, "frame name")


def validate_fe_name(value: str) -> str:
    """Check FrameNet FE name format."""
    return validate_pattern(value, FE_NAME_PATTERN, "frame element name")


def validate_verbnet_class(value: str) -> str:
    """Check VerbNet class ID format (e.g., give-13.1)."""
    return validate_pattern(value, VERBNET_CLASS_PATTERN, "VerbNet class ID")


def validate_verbnet_key(value: str) -> str:
    """Check VerbNet member key format."""
    return validate_pattern(value, VERBNET_KEY_PATTERN, "VerbNet key")


def validate_propbank_roleset(value: str) -> str:
    """Check PropBank roleset ID format (lemma.##)."""
    return validate_pattern(value, PROPBANK_ROLESET_PATTERN, "PropBank roleset ID")


def validate_wordnet_offset(value: str) -> str:
    """Check WordNet synset offset format."""
    return validate_pattern(value, WORDNET_OFFSET_PATTERN, "WordNet offset")


def validate_wordnet_sense_key(value: str) -> str:
    """Check WordNet sense key format."""
    return validate_pattern(value, WORDNET_SENSE_KEY_PATTERN, "WordNet sense key")


def validate_percentage_notation(value: str) -> str:
    """Check VerbNet's WordNet notation (lemma%#:#:#::)."""
    return validate_pattern(value, PERCENTAGE_NOTATION_PATTERN, "percentage notation")


def validate_lemma(value: str) -> str:
    """Check that lemma contains valid characters."""
    return validate_pattern(value, LEMMA_PATTERN, "lemma")


def validate_hex_color(value: str) -> str:
    """Check hex color format (#RRGGBB)."""
    return validate_pattern(value, HEX_COLOR_PATTERN, "hex color")


def validate_confidence_score(value: float) -> float:
    """Validate a confidence score is between 0.0 and 1.0.

    Parameters
    ----------
    value : float
        The confidence score to validate.

    Returns
    -------
    float
        The validated confidence score.

    Raises
    ------
    ValueError
        If the value is not between 0.0 and 1.0.
    """
    if not 0.0 <= value <= 1.0:
        msg = f"Confidence score must be between 0.0 and 1.0, got {value}"
        raise ValueError(msg)
    return value


class ConflictResolution(GlazingBaseModel):
    """Model for representing mapping conflict resolution.

    Attributes
    ----------
    conflict_type : ConflictType
        Type of conflict detected.
    resolution_strategy : str
        Strategy used to resolve the conflict.
    selected_mapping : CrossReferenceBase | None
        The mapping selected after resolution.
    rejected_mappings : list[CrossReferenceBase]
        Mappings that were rejected.
    resolution_confidence : MappingConfidenceScore
        Confidence in the resolution.
    """

    conflict_type: ConflictType
    resolution_strategy: str
    selected_mapping: CrossReferenceBase | None = None
    rejected_mappings: list[CrossReferenceBase] = Field(default_factory=list)
    resolution_confidence: MappingConfidenceScore

    @model_validator(mode="after")
    def validate_resolution(self) -> Self:
        """Resolution status must match presence of resolved_by/resolved_at."""
        if not self.selected_mapping and not self.rejected_mappings:
            raise ValueError("Resolution must have either selected or rejected mappings")
        return self
