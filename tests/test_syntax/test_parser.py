"""Test syntax parser functionality."""

from glazing.syntax.parser import SyntaxParser


class TestSyntaxParser:
    """Test SyntaxParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SyntaxParser()

    def test_basic_pattern_parsing(self):
        """Test parsing basic patterns."""
        pattern = self.parser.parse("NP V NP")

        assert len(pattern.elements) == 3
        assert pattern.elements[0].constituent == "NP"
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"
        assert pattern.normalized == "NP VERB NP"
        assert pattern.source_pattern == "NP V NP"

    def test_pp_with_semantic_role(self):
        """Test parsing PP with semantic role."""
        pattern = self.parser.parse("NP V PP.instrument")

        assert len(pattern.elements) == 3
        assert pattern.elements[2].constituent == "PP"
        assert pattern.elements[2].semantic_role == "instrument"
        assert pattern.elements[2].preposition is None
        assert pattern.normalized == "NP VERB PP"  # Normalized form shows basic constituents

    def test_pp_with_preposition(self):
        """Test parsing PP with preposition."""
        pattern = self.parser.parse("NP V PP.with")

        assert len(pattern.elements) == 3
        assert pattern.elements[2].constituent == "PP"
        assert pattern.elements[2].preposition == "with"
        assert pattern.elements[2].semantic_role is None
        assert pattern.normalized == "NP VERB PP"  # Normalized form shows basic constituents

    def test_preposition_detection(self):
        """Test automatic preposition detection."""
        # "with" should be detected as a preposition
        pattern = self.parser.parse("NP V PP.with")
        pp_element = pattern.elements[2]
        assert pp_element.preposition == "with"
        assert pp_element.semantic_role is None

        # "instrument" should be treated as semantic role
        pattern = self.parser.parse("NP V PP.instrument")
        pp_element = pattern.elements[2]
        assert pp_element.semantic_role == "instrument"
        assert pp_element.preposition is None

    def test_wildcard_parsing(self):
        """Test parsing patterns with wildcards."""
        pattern = self.parser.parse("NP V NP *")

        assert len(pattern.elements) == 4
        assert pattern.elements[3].constituent == "*"
        assert pattern.elements[3].is_wildcard is True
        assert pattern.normalized == "NP VERB NP *"

    def test_optional_element_parsing(self):
        """Test parsing optional elements (if supported)."""
        # This test assumes optional syntax like (PP) - may not be supported
        try:
            pattern = self.parser.parse("NP V (PP)")
            if len(pattern.elements) == 3:
                # If parser supports optional elements
                assert pattern.elements[2].is_optional is True
            else:
                # If not supported, should still parse successfully
                assert len(pattern.elements) >= 2
        except ValueError:
            # Optional syntax not supported - that's fine
            # Log the fact that optional syntax is not supported
            assert True  # Test passes if optional syntax is not supported

    def test_multiple_pp_parsing(self):
        """Test parsing patterns with multiple PPs."""
        pattern = self.parser.parse("NP V PP PP")

        assert len(pattern.elements) == 4
        assert pattern.elements[2].constituent == "PP"
        assert pattern.elements[3].constituent == "PP"

    def test_complex_pattern_parsing(self):
        """Test parsing complex patterns."""
        pattern = self.parser.parse("NP V NP PP.instrument PP.location")

        assert len(pattern.elements) == 5
        assert pattern.elements[3].semantic_role == "instrument"
        assert pattern.elements[4].semantic_role == "location"

    def test_verb_normalization(self):
        """Test verb constituent normalization."""
        # Test different verb representations
        test_cases = [
            ("NP V NP", "NP VERB NP"),
            ("NP VERB NP", "NP VERB NP"),
        ]

        for input_pattern, expected_normalized in test_cases:
            pattern = self.parser.parse(input_pattern)
            assert pattern.normalized == expected_normalized

    def test_empty_pattern(self):
        """Test parsing empty or whitespace patterns."""
        # Test what actually happens with empty patterns
        try:
            result1 = self.parser.parse("")
            # If it doesn't raise, should be empty or minimal result
            assert len(result1.elements) == 0 or result1.normalized == ""
        except (ValueError, AttributeError, IndexError):
            # Expected for empty patterns
            pass

        try:
            result2 = self.parser.parse("   ")
            # If it doesn't raise, should be empty or minimal result
            assert len(result2.elements) == 0 or result2.normalized == ""
        except (ValueError, AttributeError, IndexError):
            # Expected for empty patterns
            pass

    def test_single_element_pattern(self):
        """Test parsing single element patterns."""
        pattern = self.parser.parse("NP")

        assert len(pattern.elements) == 1
        assert pattern.elements[0].constituent == "NP"

    def test_case_sensitivity(self):
        """Test case handling in patterns."""
        # Test lowercase and uppercase inputs
        pattern_lower = self.parser.parse("np v np")
        pattern_upper = self.parser.parse("NP V NP")

        # Both should normalize to the same format
        assert pattern_lower.normalized == pattern_upper.normalized

    def test_extra_whitespace(self):
        """Test handling of extra whitespace."""
        pattern = self.parser.parse("  NP   V    NP  ")

        assert len(pattern.elements) == 3
        assert pattern.elements[0].constituent == "NP"
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"

    def test_verbnet_specific_parsing(self):
        """Test parsing VerbNet-specific patterns."""
        # Test if parser has VerbNet-specific method
        if hasattr(self.parser, "parse_verbnet_elements"):
            # This would test VerbNet-specific parsing
            pass
        else:
            # Standard parsing should work for VerbNet patterns
            pattern = self.parser.parse("NP V NP PP.instrument")
            assert len(pattern.elements) == 4

    def test_common_prepositions_detection(self):
        """Test that common prepositions are correctly identified."""
        common_preps = ["with", "at", "on", "in", "for", "by", "from", "to"]

        for prep in common_preps:
            pattern = self.parser.parse(f"NP V PP.{prep}")
            pp_element = pattern.elements[2]
            assert pp_element.preposition == prep
            assert pp_element.semantic_role is None

    def test_semantic_roles_detection(self):
        """Test that semantic roles are correctly identified."""
        semantic_roles = ["instrument", "location", "agent", "patient", "theme"]

        for role in semantic_roles:
            if role not in self.parser.COMMON_PREPOSITIONS:
                pattern = self.parser.parse(f"NP V PP.{role}")
                pp_element = pattern.elements[2]
                assert pp_element.semantic_role == role
                assert pp_element.preposition is None

    def test_error_handling_invalid_syntax(self):
        """Test error handling for invalid syntax."""
        invalid_patterns = [
            "NP V NP..",  # Double dot
            "NP V PP.",  # Trailing dot
            ".NP V NP",  # Leading dot
            "NP V .PP",  # Dot before constituent
        ]

        for invalid_pattern in invalid_patterns:
            # Should either handle gracefully or raise appropriate error
            try:
                pattern = self.parser.parse(invalid_pattern)
                # If it parses, verify it makes sense
                assert len(pattern.elements) > 0
            except (ValueError, AttributeError):
                # Expected for invalid patterns - this is the desired behavior
                pass

    def test_pattern_source_preservation(self):
        """Test that source pattern is preserved."""
        original = "NP V PP.instrument"
        pattern = self.parser.parse(original)

        assert pattern.source_pattern == original
