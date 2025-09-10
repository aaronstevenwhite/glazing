"""Tests for custom validators."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from glazing.utils.validators import (
    PatternValidator,
    RangeValidator,
    create_confidence_validator,
    create_identifier_validator,
    create_lemma_validator,
    create_pattern_validator,
    create_percentage_validator,
    create_range_validator,
    create_uppercase_name_validator,
    normalize_whitespace,
    validate_conditional_requirement,
    validate_mutually_exclusive,
    validate_non_empty_list,
    validate_non_empty_string,
    validate_unique_list,
)


class TestPatternValidator:
    """Test the PatternValidator class."""

    def test_basic_pattern_validation(self):
        """Test basic pattern matching."""
        validator = PatternValidator(r"^\d{3}$", "three digits")

        assert validator("123") == "123"
        assert validator("456") == "456"

        with pytest.raises(ValueError) as exc_info:
            validator("12")  # Too short
        assert "three digits" in str(exc_info.value)

        with pytest.raises(ValueError):
            validator("abc")  # Not digits

    def test_case_insensitive_pattern(self):
        """Test pattern with regex flags."""
        validator = PatternValidator(r"^hello$", "greeting", flags=re.IGNORECASE)

        assert validator("hello") == "hello"
        assert validator("HELLO") == "HELLO"
        assert validator("Hello") == "Hello"

        with pytest.raises(ValueError):
            validator("hi")

    def test_non_string_input(self):
        """Test that non-strings are rejected."""
        validator = PatternValidator(r"^\d+$", "number")

        with pytest.raises(TypeError):
            validator(123)  # Integer, not string

    def test_repr(self):
        """Test string representation."""
        validator = PatternValidator(r"^\d{3}$", "three digits")
        repr_str = repr(validator)
        assert "PatternValidator" in repr_str
        assert "three digits" in repr_str


class TestRangeValidator:
    """Test the RangeValidator class."""

    def test_basic_range_validation(self):
        """Test basic range validation."""
        validator = RangeValidator(0, 100, "percentage")

        assert validator(0) == 0
        assert validator(50) == 50
        assert validator(100) == 100

        with pytest.raises(ValueError) as exc_info:
            validator(-1)
        assert "percentage" in str(exc_info.value)

        with pytest.raises(ValueError):
            validator(101)

    def test_min_only(self):
        """Test range with only minimum."""
        validator = RangeValidator(min_value=0, field_name="positive")

        assert validator(0) == 0
        assert validator(1000000) == 1000000

        with pytest.raises(ValueError):
            validator(-1)

    def test_max_only(self):
        """Test range with only maximum."""
        validator = RangeValidator(max_value=100, field_name="limited")

        assert validator(-1000) == -1000
        assert validator(100) == 100

        with pytest.raises(ValueError):
            validator(101)

    def test_float_values(self):
        """Test with float values."""
        validator = RangeValidator(0.0, 1.0, "probability")

        assert validator(0.0) == 0.0
        assert validator(0.5) == 0.5
        assert validator(1.0) == 1.0

        with pytest.raises(ValueError):
            validator(1.01)

    def test_invalid_range(self):
        """Test that invalid ranges are rejected."""
        with pytest.raises(ValueError):
            RangeValidator(min_value=100, max_value=0)  # Min > Max

    def test_non_numeric_input(self):
        """Test that non-numeric inputs are rejected."""
        validator = RangeValidator(0, 100)

        with pytest.raises(TypeError):
            validator("50")  # String, not number

    def test_repr(self):
        """Test string representation."""
        validator = RangeValidator(0, 100, "percentage")
        repr_str = repr(validator)
        assert "RangeValidator" in repr_str
        assert "percentage" in repr_str


class TestFactoryFunctions:
    """Test validator factory functions."""

    def test_create_pattern_validator(self):
        """Test pattern validator factory."""
        validator = create_pattern_validator(r"^\d{4}$", "year")

        assert validator("2024") == "2024"
        with pytest.raises(ValueError):
            validator("24")

    def test_create_range_validator(self):
        """Test range validator factory."""
        validator = create_range_validator(1, 10, "rating")

        assert validator(5) == 5
        with pytest.raises(ValueError):
            validator(11)

    def test_create_lemma_validator(self):
        """Test lemma validator factory."""
        validator = create_lemma_validator()

        assert validator("abandon") == "abandon"
        assert validator("spray_paint") == "spray_paint"

        with pytest.raises(ValueError):
            validator("Abandon")  # Uppercase

    def test_create_uppercase_name_validator(self):
        """Test uppercase name validator factory."""
        validator = create_uppercase_name_validator("frame")

        assert validator("Abandonment") == "Abandonment"
        assert validator("Activity_finish") == "Activity_finish"

        with pytest.raises(ValueError):
            validator("abandonment")  # Lowercase

    def test_create_identifier_validator(self):
        """Test identifier validator factory."""
        validator = create_identifier_validator(r"^ID\d{3}$", "custom ID")

        assert validator("ID123") == "ID123"
        with pytest.raises(ValueError):
            validator("123")

    def test_create_confidence_validator(self):
        """Test confidence validator factory."""
        validator = create_confidence_validator()

        assert validator(0.0) == 0.0
        assert validator(0.5) == 0.5
        assert validator(1.0) == 1.0

        with pytest.raises(ValueError):
            validator(1.1)

    def test_create_percentage_validator(self):
        """Test percentage validator factory."""
        validator = create_percentage_validator()

        assert validator(0) == 0
        assert validator(50) == 50
        assert validator(100) == 100

        with pytest.raises(ValueError):
            validator(101)


class TestStringValidators:
    """Test string validation functions."""

    def test_validate_non_empty_string(self):
        """Test non-empty string validation."""
        assert validate_non_empty_string("hello") == "hello"
        assert validate_non_empty_string("  hello  ") == "hello"  # Strips whitespace

        with pytest.raises(ValueError):
            validate_non_empty_string("")

        with pytest.raises(ValueError):
            validate_non_empty_string("   ")  # Only whitespace

        with pytest.raises(TypeError):
            validate_non_empty_string(123)  # Not a string

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        assert normalize_whitespace("hello  world") == "hello world"
        assert normalize_whitespace("  hello   world  ") == "hello world"
        assert normalize_whitespace("hello\n\tworld") == "hello world"
        assert normalize_whitespace("hello") == "hello"

        # Non-strings pass through
        assert normalize_whitespace(123) == 123
        assert normalize_whitespace(None) is None


class TestListValidators:
    """Test list validation functions."""

    def test_validate_non_empty_list(self):
        """Test non-empty list validation."""
        assert validate_non_empty_list([1, 2, 3]) == [1, 2, 3]
        assert validate_non_empty_list(["a"]) == ["a"]

        with pytest.raises(ValueError):
            validate_non_empty_list([])

        with pytest.raises(TypeError):
            validate_non_empty_list("not a list")

    def test_validate_unique_list(self):
        """Test unique list validation."""
        assert validate_unique_list([1, 2, 3]) == [1, 2, 3]
        assert validate_unique_list(["a", "b", "c"]) == ["a", "b", "c"]

        with pytest.raises(ValueError) as exc_info:
            validate_unique_list([1, 2, 2, 3])
        assert "duplicate" in str(exc_info.value)

        with pytest.raises(ValueError):
            validate_unique_list(["a", "b", "a"])

        # Test with unhashable types
        list2 = [{"a": 1}, {"b": 2}]
        assert validate_unique_list(list2) == list2

        # Duplicate dicts
        list3 = [{"a": 1}, {"a": 1}]
        with pytest.raises(ValueError):
            validate_unique_list(list3)


class TestConditionalValidators:
    """Test conditional validation functions."""

    def test_validate_mutually_exclusive(self):
        """Test mutually exclusive field validation."""
        # Valid - only one field set
        values1 = {"field1": "value", "field2": None}
        result1 = validate_mutually_exclusive(values1, [["field1", "field2"]])
        assert result1 == values1

        # Invalid - both fields set
        values2 = {"field1": "value", "field2": "other"}
        with pytest.raises(ValueError) as exc_info:
            validate_mutually_exclusive(values2, [["field1", "field2"]])
        assert "mutually exclusive" in str(exc_info.value)

        # Multiple groups
        values3 = {"a": 1, "b": None, "c": 2, "d": None}
        result3 = validate_mutually_exclusive(values3, [["a", "b"], ["c", "d"]])
        assert result3 == values3

    def test_validate_mutually_exclusive_require_one(self):
        """Test mutually exclusive with require_one option."""
        # Valid - exactly one field set
        values1 = {"field1": "value", "field2": None}
        result1 = validate_mutually_exclusive(values1, [["field1", "field2"]], require_one=True)
        assert result1 == values1

        # Invalid - no fields set
        values2 = {"field1": None, "field2": None}
        with pytest.raises(ValueError) as exc_info:
            validate_mutually_exclusive(values2, [["field1", "field2"]], require_one=True)
        assert "Exactly one" in str(exc_info.value)

    def test_validate_conditional_requirement(self):
        """Test conditional field requirements."""
        # Condition not met - no requirements
        values1 = {"status": "draft", "published_date": None}
        result1 = validate_conditional_requirement(
            values1, "status", "published", ["published_date"]
        )
        assert result1 == values1

        # Condition met - requirements satisfied
        values2 = {"status": "published", "published_date": datetime.now(UTC)}
        result2 = validate_conditional_requirement(
            values2, "status", "published", ["published_date"]
        )
        assert result2 == values2

        # Condition met - requirements not satisfied
        values3 = {"status": "published", "published_date": None}
        with pytest.raises(ValueError) as exc_info:
            validate_conditional_requirement(values3, "status", "published", ["published_date"])
        assert "required when" in str(exc_info.value)
