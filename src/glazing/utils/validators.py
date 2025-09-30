"""Custom validators for the glazing package.

This module provides reusable Pydantic validators and validation utilities
for common patterns across all linguistic datasets.

Functions
---------
create_pattern_validator
    Factory function to create regex pattern validators.
create_range_validator
    Factory function to create numeric range validators.
validate_non_empty_string
    Ensure a string is not empty or only whitespace.
validate_non_empty_list
    Ensure a list is not empty.
validate_unique_list
    Ensure all items in a list are unique.
normalize_whitespace
    Normalize whitespace in strings.

Classes
-------
PatternValidator
    Reusable regex pattern validator class.
RangeValidator
    Reusable numeric range validator class.

Notes
-----
These validators are designed to be used with Pydantic v2 field_validator
and model_validator decorators. They provide consistent validation behavior
across all dataset-specific models.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

type ValueType = str | int | float | bool | None | list[ValueType] | dict[str, ValueType]


class PatternValidator:
    """Reusable regex pattern validator.

    Parameters
    ----------
    pattern : str
        The regex pattern to match.
    field_name : str
        Human-readable name of the field being validated.
    flags : int, default=0
        Regex flags (e.g., re.IGNORECASE).

    Methods
    -------
    __call__(value)
        Validate a value against the pattern.

    Examples
    --------
    >>> validator = PatternValidator(r'^[A-Z][a-z]+$', 'name')
    >>> validator('John')  # Returns 'John'
    >>> validator('john')  # Raises ValueError
    """

    def __init__(self, pattern: str, field_name: str, flags: int = 0) -> None:
        """Initialize the pattern validator."""
        self.pattern = re.compile(pattern, flags)
        self.field_name = field_name
        self.pattern_str = pattern

    def __call__(self, value: str) -> str:
        """Validate a value against the pattern.

        Parameters
        ----------
        value : str
            The value to validate.

        Returns
        -------
        str
            The validated value.

        Raises
        ------
        ValueError
            If the value doesn't match the pattern.
        """
        if not isinstance(value, str):
            msg = f"{self.field_name} must be a string"
            raise TypeError(msg)

        if not self.pattern.match(value):
            msg = (
                f"Invalid {self.field_name} format: '{value}' "
                f"does not match pattern '{self.pattern_str}'"
            )
            raise ValueError(msg)
        return value

    def __repr__(self) -> str:
        """String representation of the validator."""
        return f"PatternValidator(pattern={self.pattern_str!r}, field_name={self.field_name!r})"


class RangeValidator:
    """Reusable numeric range validator.

    Parameters
    ----------
    min_value : float | None
        Minimum allowed value (inclusive).
    max_value : float | None
        Maximum allowed value (inclusive).
    field_name : str
        Human-readable name of the field being validated.

    Methods
    -------
    __call__(value)
        Validate a value is within the range.

    Examples
    --------
    >>> validator = RangeValidator(0, 100, 'percentage')
    >>> validator(50)  # Returns 50
    >>> validator(150)  # Raises ValueError
    """

    def __init__(
        self,
        min_value: float | None = None,
        max_value: float | None = None,
        field_name: str = "value",
    ) -> None:
        """Initialize the range validator."""
        if min_value is not None and max_value is not None and min_value > max_value:
            msg = f"min_value ({min_value}) cannot be greater than max_value ({max_value})"
            raise ValueError(msg)

        self.min_value = min_value
        self.max_value = max_value
        self.field_name = field_name

    def __call__(self, value: float | int) -> float | int:
        """Validate a value is within the range.

        Parameters
        ----------
        value : float | int
            The value to validate.

        Returns
        -------
        float | int
            The validated value.

        Raises
        ------
        ValueError
            If the value is outside the range.
        """
        if not isinstance(value, int | float):
            msg = f"{self.field_name} must be numeric"
            raise TypeError(msg)

        if self.min_value is not None and value < self.min_value:
            msg = f"{self.field_name} must be at least {self.min_value}, got {value}"
            raise ValueError(msg)

        if self.max_value is not None and value > self.max_value:
            msg = f"{self.field_name} must be at most {self.max_value}, got {value}"
            raise ValueError(msg)

        return value

    def __repr__(self) -> str:
        """String representation of the validator."""
        return (
            f"RangeValidator(min_value={self.min_value}, "
            f"max_value={self.max_value}, field_name={self.field_name!r})"
        )


def create_pattern_validator(pattern: str, field_name: str, flags: int = 0) -> Callable[[str], str]:
    """Factory function to create a pattern validator.

    Parameters
    ----------
    pattern : str
        The regex pattern to match.
    field_name : str
        Human-readable name of the field.
    flags : int, default=0
        Regex flags.

    Returns
    -------
    Callable[[str], str]
        A validator function.

    Examples
    --------
    >>> validate_email = create_pattern_validator(
    ...     r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
    ...     'email address'
    ... )
    >>> validate_email('user@example.com')  # Returns 'user@example.com'
    """
    return PatternValidator(pattern, field_name, flags)


def create_range_validator(
    min_value: float | None = None, max_value: float | None = None, field_name: str = "value"
) -> Callable[[float | int], float | int]:
    """Factory function to create a range validator.

    Parameters
    ----------
    min_value : float | None
        Minimum allowed value.
    max_value : float | None
        Maximum allowed value.
    field_name : str
        Human-readable name of the field.

    Returns
    -------
    Callable[[float | int], float | int]
        A validator function.

    Examples
    --------
    >>> validate_age = create_range_validator(0, 150, 'age')
    >>> validate_age(25)  # Returns 25
    """
    return RangeValidator(min_value, max_value, field_name)


def validate_non_empty_string(value: str, field_name: str = "string") -> str:
    """Ensure a string is not empty or only whitespace.

    Parameters
    ----------
    value : str
        The string to validate.
    field_name : str
        Name of the field being validated.

    Returns
    -------
    str
        The validated string (stripped of leading/trailing whitespace).

    Raises
    ------
    ValueError
        If the string is empty or only whitespace.
    """
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)

    stripped = value.strip()
    if not stripped:
        msg = f"{field_name} cannot be empty or only whitespace"
        raise ValueError(msg)

    return stripped


def validate_non_empty_list[T](value: list[T], field_name: str = "list") -> list[T]:
    """Ensure a list is not empty.

    Parameters
    ----------
    value : list[T]
        The list to validate.
    field_name : str
        Name of the field being validated.

    Returns
    -------
    list[T]
        The validated list.

    Raises
    ------
    ValueError
        If the list is empty.
    """
    if not isinstance(value, list):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)

    if not value:
        msg = f"{field_name} cannot be empty"
        raise ValueError(msg)

    return value


def validate_unique_list[T](value: list[T], field_name: str = "list") -> list[T]:
    """Ensure all items in a list are unique.

    Parameters
    ----------
    value : list[T]
        The list to validate.
    field_name : str
        Name of the field being validated.

    Returns
    -------
    list[T]
        The validated list.

    Raises
    ------
    ValueError
        If the list contains duplicate items.
    """
    if not isinstance(value, list):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)

    # Check for duplicates
    seen = set()
    duplicates = []
    for item in value:
        # Handle unhashable types
        try:
            if item in seen:
                duplicates.append(item)
            else:
                seen.add(item)
        except TypeError:
            # For unhashable types, fall back to linear search
            if value.count(item) > 1 and item not in duplicates:
                duplicates.append(item)

    if duplicates:
        msg = f"{field_name} contains duplicate items: {duplicates}"
        raise ValueError(msg)

    return value


def normalize_whitespace(value: str) -> str:
    """Normalize whitespace in a string.

    Replaces multiple consecutive whitespace characters with a single space
    and strips leading/trailing whitespace.

    Parameters
    ----------
    value : str
        The string to normalize.

    Returns
    -------
    str
        The normalized string.

    Examples
    --------
    >>> normalize_whitespace('  hello   world  ')
    'hello world'
    """
    if not isinstance(value, str):
        return value

    # Replace multiple whitespace with single space
    normalized = re.sub(r"\s+", " ", value)
    # Strip leading/trailing whitespace
    return normalized.strip()


def validate_mutually_exclusive(
    values: dict[str, ValueType], field_groups: list[list[str]], require_one: bool = False
) -> dict[str, ValueType]:
    """Validate that fields are mutually exclusive.

    Parameters
    ----------
    values : dict[str, ValueType]
        The values dictionary from a Pydantic model.
    field_groups : list[list[str]]
        Groups of field names that are mutually exclusive.
    require_one : bool, default=False
        If True, exactly one field from each group must be set.

    Returns
    -------
    dict[str, ValueType]
        The validated values.

    Raises
    ------
    ValueError
        If mutually exclusive fields are both set.

    Examples
    --------
    >>> values = {'source_id': '123', 'source_ids': None}
    >>> validate_mutually_exclusive(values, [['source_id', 'source_ids']])
    """
    for group in field_groups:
        set_fields = [field for field in group if field in values and values[field] is not None]

        if len(set_fields) > 1:
            msg = f"Fields {set_fields} are mutually exclusive. Only one can be set."
            raise ValueError(msg)

        if require_one and len(set_fields) == 0:
            msg = f"Exactly one of {group} must be set."
            raise ValueError(msg)

    return values


def validate_conditional_requirement(
    values: dict[str, ValueType],
    condition_field: str,
    condition_value: ValueType,
    required_fields: list[str],
) -> dict[str, ValueType]:
    """Validate that fields are required when a condition is met.

    Parameters
    ----------
    values : dict[str, ValueType]
        The values dictionary from a Pydantic model.
    condition_field : str
        The field to check for the condition.
    condition_value : ValueType
        The value that triggers the requirement.
    required_fields : list[str]
        Fields that are required when the condition is met.

    Returns
    -------
    dict[str, ValueType]
        The validated values.

    Raises
    ------
    ValueError
        If required fields are missing when the condition is met.
    """
    if values.get(condition_field) == condition_value:
        missing_fields = [
            field for field in required_fields if field not in values or values[field] is None
        ]

        if missing_fields:
            msg = (
                f"Fields {missing_fields} are required when {condition_field} is {condition_value}"
            )
            raise ValueError(msg)

    return values


# Commonly used validators for linguistic data


def create_lemma_validator() -> PatternValidator:
    """Create a validator for word lemmas."""
    return PatternValidator(r"^[a-z][a-z0-9_\'-]*$", "lemma")


def create_uppercase_name_validator(field_name: str = "name") -> PatternValidator:
    """Create a validator for uppercase-starting names (frames, FEs)."""
    return PatternValidator(r"^[A-Z][A-Za-z0-9_]*$", field_name)


def create_identifier_validator(pattern: str, field_name: str) -> PatternValidator:
    """Create a validator for dataset-specific identifiers."""
    return PatternValidator(pattern, field_name)


def create_confidence_validator() -> RangeValidator:
    """Create a validator for confidence scores (0.0-1.0)."""
    return RangeValidator(0.0, 1.0, "confidence score")


def create_percentage_validator() -> RangeValidator:
    """Create a validator for percentage values (0-100)."""
    return RangeValidator(0, 100, "percentage")
