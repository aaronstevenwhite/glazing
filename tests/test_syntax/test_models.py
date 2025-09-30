"""Test syntax models and hierarchical matching."""

from glazing.syntax.models import SyntaxElement, UnifiedSyntaxPattern


class TestSyntaxElement:
    """Test SyntaxElement class and hierarchical matching."""

    def test_basic_creation(self):
        """Test basic SyntaxElement creation."""
        element = SyntaxElement(constituent="NP")
        assert element.constituent == "NP"
        assert element.semantic_role is None
        assert element.head is None
        assert element.features == {}
        assert element.is_wildcard is False
        assert element.is_optional is False

    def test_pp_with_semantic_role(self):
        """Test PP with semantic role."""
        element = SyntaxElement(constituent="PP", semantic_role="instrument")
        assert element.constituent == "PP"
        assert element.semantic_role == "instrument"
        assert element.head is None

    def test_pp_with_head(self):
        """Test PP with specific head."""
        element = SyntaxElement(constituent="PP", head="with")
        assert element.constituent == "PP"
        assert element.semantic_role is None
        assert element.head == "with"

    def test_wildcard_element(self):
        """Test wildcard element."""
        element = SyntaxElement(constituent="*", is_wildcard=True)
        assert element.constituent == "*"
        assert element.is_wildcard is True

    def test_optional_element(self):
        """Test optional element."""
        element = SyntaxElement(constituent="PP", is_optional=True)
        assert element.constituent == "PP"
        assert element.is_optional is True

    def test_element_with_features(self):
        """Test element with morphological features."""
        element = SyntaxElement(constituent="V", features={"form": "ing"})
        assert element.constituent == "V"
        assert element.features == {"form": "ing"}

    def test_element_with_multiple_features(self):
        """Test element with multiple features."""
        element = SyntaxElement(constituent="VP", features={"form": "inf", "tense": "past"})
        assert element.constituent == "VP"
        assert element.features == {"form": "inf", "tense": "past"}

    def test_hierarchical_matching_exact_match(self):
        """Test exact match returns perfect confidence."""
        elem1 = SyntaxElement(constituent="NP")
        elem2 = SyntaxElement(constituent="NP")

        matches, confidence = elem1.matches_hierarchically(elem2)
        assert matches is True
        assert confidence == 1.0

    def test_hierarchical_matching_general_to_specific_pp(self):
        """Test general PP matches specific PP with perfect confidence."""
        general_pp = SyntaxElement(constituent="PP")
        specific_pp = SyntaxElement(constituent="PP", semantic_role="instrument")

        # General should match specific perfectly
        matches, confidence = general_pp.matches_hierarchically(specific_pp)
        assert matches is True
        assert confidence == 1.0

    def test_hierarchical_matching_specific_to_general_pp(self):
        """Test specific PP does not match general PP."""
        general_pp = SyntaxElement(constituent="PP")
        specific_pp = SyntaxElement(constituent="PP", semantic_role="instrument")

        # Specific should not match general
        matches, confidence = specific_pp.matches_hierarchically(general_pp)
        assert matches is False
        assert confidence == 0.0

    def test_hierarchical_matching_different_heads(self):
        """Test PP with different heads don't match."""
        pp_with = SyntaxElement(constituent="PP", head="with")
        pp_for = SyntaxElement(constituent="PP", head="for")

        matches, confidence = pp_with.matches_hierarchically(pp_for)
        assert matches is False
        assert confidence == 0.0

    def test_hierarchical_matching_different_semantic_roles(self):
        """Test PP with different semantic roles don't match."""
        pp_instrument = SyntaxElement(constituent="PP", semantic_role="instrument")
        pp_location = SyntaxElement(constituent="PP", semantic_role="location")

        matches, confidence = pp_instrument.matches_hierarchically(pp_location)
        assert matches is False
        assert confidence == 0.0

    def test_hierarchical_matching_different_constituents(self):
        """Test different constituents don't match."""
        np = SyntaxElement(constituent="NP")
        pp = SyntaxElement(constituent="PP")

        matches, confidence = np.matches_hierarchically(pp)
        assert matches is False
        assert confidence == 0.0

    def test_hierarchical_matching_wildcard(self):
        """Test wildcard matching behavior."""
        wildcard = SyntaxElement(constituent="*", is_wildcard=True)
        np = SyntaxElement(constituent="NP")

        # Wildcard should match anything with perfect confidence (maximally general)
        matches, confidence = wildcard.matches_hierarchically(np)
        assert matches is True
        assert confidence == 1.0  # Perfect confidence - wildcards are maximally general

    def test_hierarchical_matching_optional(self):
        """Test optional element matching behavior."""
        optional_pp = SyntaxElement(constituent="PP", is_optional=True)
        pp = SyntaxElement(constituent="PP")

        matches, confidence = optional_pp.matches_hierarchically(pp)
        assert matches is True
        assert confidence == 1.0

    def test_hierarchical_matching_pp_head_to_semantic(self):
        """Test PP with head doesn't match PP with semantic role."""
        pp_with = SyntaxElement(constituent="PP", head="with")
        pp_instrument = SyntaxElement(constituent="PP", semantic_role="instrument")

        # Different dimensions (head vs semantic role) don't match
        matches, confidence = pp_with.matches_hierarchically(pp_instrument)
        assert matches is False
        assert confidence == 0.0

    def test_string_representation(self):
        """Test string representation of elements."""
        simple_np = SyntaxElement(constituent="NP")
        assert str(simple_np) == "NP"

        pp_with_role = SyntaxElement(constituent="PP", semantic_role="instrument")
        assert str(pp_with_role) == "PP.instrument"

        pp_with_head = SyntaxElement(constituent="PP", head="with")
        assert str(pp_with_head) == "PP[with]"

        v_with_features = SyntaxElement(constituent="V", features={"form": "ing"})
        assert str(v_with_features) == "V[ING]"

        wildcard = SyntaxElement(constituent="*", is_wildcard=True)
        assert str(wildcard) == "*"


class TestUnifiedSyntaxPattern:
    """Test UnifiedSyntaxPattern class."""

    def test_basic_creation(self):
        """Test basic pattern creation."""
        elements = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="NP"),
        ]
        pattern = UnifiedSyntaxPattern(
            elements=elements, normalized="NP VERB NP", source_pattern="NP V NP"
        )

        assert len(pattern.elements) == 3
        assert pattern.normalized == "NP VERB NP"
        assert pattern.source_pattern == "NP V NP"
        assert pattern.source_dataset is None

    def test_with_source_dataset(self):
        """Test pattern with source dataset."""
        elements = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="PP", semantic_role="instrument"),
        ]
        pattern = UnifiedSyntaxPattern(
            elements=elements,
            normalized="NP VERB PP.instrument",
            source_pattern="NP V PP.instrument",
            source_dataset="verbnet",
        )

        assert pattern.source_dataset == "verbnet"

    def test_string_representation(self):
        """Test string representation of pattern."""
        elements = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="PP", preposition="with"),
        ]
        pattern = UnifiedSyntaxPattern(
            elements=elements, normalized="NP VERB PP.with", source_pattern="NP V PP.with"
        )

        pattern_str = str(pattern)
        assert "NP VERB PP.with" in pattern_str

    def test_equality(self):
        """Test pattern equality comparison."""
        elements1 = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="NP"),
        ]
        elements2 = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="NP"),
        ]

        pattern1 = UnifiedSyntaxPattern(
            elements=elements1, normalized="NP VERB NP", source_pattern="NP V NP"
        )
        pattern2 = UnifiedSyntaxPattern(
            elements=elements2, normalized="NP VERB NP", source_pattern="NP V NP"
        )

        assert pattern1 == pattern2

    def test_inequality_different_elements(self):
        """Test pattern inequality with different elements."""
        elements1 = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="NP"),
        ]
        elements2 = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="PP"),
        ]

        pattern1 = UnifiedSyntaxPattern(
            elements=elements1, normalized="NP VERB NP", source_pattern="NP V NP"
        )
        pattern2 = UnifiedSyntaxPattern(
            elements=elements2, normalized="NP VERB PP", source_pattern="NP V PP"
        )

        assert pattern1 != pattern2

    def test_hierarchical_pattern_matching(self):
        """Test hierarchical matching between patterns."""
        # General pattern: NP V PP
        general_elements = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="PP"),
        ]
        general_pattern = UnifiedSyntaxPattern(
            elements=general_elements, normalized="NP VERB PP", source_pattern="NP V PP"
        )

        # Specific pattern: NP V PP.instrument
        specific_elements = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="VERB"),
            SyntaxElement(constituent="PP", semantic_role="instrument"),
        ]
        specific_pattern = UnifiedSyntaxPattern(
            elements=specific_elements,
            normalized="NP VERB PP.instrument",
            source_pattern="NP V PP.instrument",
        )

        # Test that general pattern elements match specific pattern elements
        assert len(general_pattern.elements) == len(specific_pattern.elements)

        for general_elem, specific_elem in zip(
            general_pattern.elements, specific_pattern.elements, strict=False
        ):
            matches, confidence = general_elem.matches_hierarchically(specific_elem)
            assert matches is True
            assert confidence > 0.0


class TestMorphologicalFeatures:
    """Test morphological feature support."""

    def test_verb_ing_feature(self):
        """Test V[ING] morphological feature."""
        v_ing = SyntaxElement(constituent="V", features={"form": "ing"})
        v_plain = SyntaxElement(constituent="V")

        # General verb should match specific V[ING]
        matches, confidence = v_plain.matches_hierarchically(v_ing)
        assert matches is True
        assert confidence == 1.0

        # Specific V[ING] should not match general verb
        matches, confidence = v_ing.matches_hierarchically(v_plain)
        assert matches is False
        assert confidence == 0.0

    def test_verb_inf_feature(self):
        """Test V[INF] morphological feature."""
        v_inf = SyntaxElement(constituent="V", features={"form": "inf"})
        v_plain = SyntaxElement(constituent="V")

        # General verb should match specific V[INF]
        matches, confidence = v_plain.matches_hierarchically(v_inf)
        assert matches is True
        assert confidence == 1.0

    def test_pp_head_matching(self):
        """Test PP[with] head matching."""
        pp_with = SyntaxElement(constituent="PP", head="with")
        pp_plain = SyntaxElement(constituent="PP")

        # General PP should match specific PP[with]
        matches, confidence = pp_plain.matches_hierarchically(pp_with)
        assert matches is True
        assert confidence == 1.0

        # Same heads should match
        pp_with2 = SyntaxElement(constituent="PP", head="with")
        matches, confidence = pp_with.matches_hierarchically(pp_with2)
        assert matches is True
        assert confidence == 1.0

    def test_feature_compatibility(self):
        """Test feature compatibility checking."""
        v_ing = SyntaxElement(constituent="V", features={"form": "ing"})
        v_inf = SyntaxElement(constituent="V", features={"form": "inf"})

        # Different features shouldn't match
        matches, confidence = v_ing.matches_hierarchically(v_inf)
        assert matches is False
        assert confidence == 0.0

    def test_unified_pattern_from_verbnet(self):
        """Test UnifiedSyntaxPattern.from_verbnet_synrestrs."""
        elements = [
            SyntaxElement(constituent="NP"),
            SyntaxElement(constituent="V"),
            SyntaxElement(constituent="NP"),
        ]
        synrestrs = [
            {"type": "oc_ing", "value": "+"},
            {"type": "oc_to_inf", "value": "-"},
        ]

        pattern = UnifiedSyntaxPattern.from_verbnet_synrestrs(
            elements=elements, synrestrs=synrestrs, source_pattern="NP V NP"
        )

        # Check that features were extracted
        verb_elem = pattern.elements[1]
        assert verb_elem.features.get("form") == "ing"

    def test_pattern_normalization(self):
        """Test pattern feature normalization."""
        elements = [
            SyntaxElement(constituent="V", features={"form": "ING"}),
            SyntaxElement(constituent="VP", features={"form": "progressive"}),
        ]
        pattern = UnifiedSyntaxPattern(elements=elements)
        normalized = pattern.normalize_features()

        # Check normalization
        assert normalized.elements[0].features["form"] == "ing"
        assert normalized.elements[1].features["form"] == "ing"
