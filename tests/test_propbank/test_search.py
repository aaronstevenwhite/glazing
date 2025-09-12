"""Tests for PropBank search functionality."""

import re

import pytest

from glazing.propbank.models import (
    Alias,
    Aliases,
    Frameset,
    LexLink,
    Role,
    Roleset,
)
from glazing.propbank.search import PropBankSearch


class TestPropBankSearch:
    """Tests for PropBankSearch class."""

    @pytest.fixture
    def sample_framesets(self):
        """Create sample framesets for testing."""
        # Create give frameset
        give_frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(
                    id="give.01",
                    name="transfer",
                    aliases=Aliases(
                        alias=[
                            Alias(text="give", pos="v"),
                            Alias(text="giving", pos="n"),
                        ]
                    ),
                    roles=[
                        Role(n="0", f="PAG", descr="giver"),
                        Role(n="1", f="PPT", descr="thing given"),
                        Role(n="2", f="GOL", descr="entity given to"),
                    ],
                    lexlinks=[
                        LexLink(
                            class_name="give-13.1",
                            confidence=0.95,
                            resource="VerbNet",
                            version="3.4",
                            src="manual",
                        ),
                        LexLink(
                            class_name="Giving",
                            confidence=0.9,
                            resource="FrameNet",
                            version="1.7",
                            src="manual",
                        ),
                    ],
                ),
                Roleset(
                    id="give.02",
                    name="emit",
                    aliases=Aliases(alias=[Alias(text="give", pos="v")]),
                    roles=[
                        Role(n="0", f="PAG", descr="emitter"),
                        Role(n="1", f="PPT", descr="thing emitted"),
                    ],
                ),
            ],
        )

        # Create abandon frameset
        abandon_frameset = Frameset(
            predicate_lemma="abandon",
            rolesets=[
                Roleset(
                    id="abandon.01",
                    name="leave behind",
                    aliases=Aliases(
                        alias=[
                            Alias(text="abandon", pos="v"),
                            Alias(text="abandonment", pos="n"),
                        ]
                    ),
                    roles=[
                        Role(n="0", f="PAG", descr="abandoner"),
                        Role(n="1", f="PPT", descr="thing abandoned"),
                        Role(n="M", f="LOC", descr="location"),
                    ],
                    lexlinks=[
                        LexLink(
                            class_name="leave-51.2",
                            confidence=0.85,
                            resource="VerbNet",
                            version="3.4",
                            src="automatic",
                        ),
                    ],
                ),
            ],
        )

        return [give_frameset, abandon_frameset]

    def test_init_empty(self):
        """Test initialization with empty index."""
        search = PropBankSearch()
        assert search.get_statistics()["frameset_count"] == 0
        assert search.get_all_lemmas() == []
        assert search.get_all_rolesets() == []

    def test_init_with_framesets(self, sample_framesets):
        """Test initialization with framesets."""
        search = PropBankSearch(sample_framesets)
        stats = search.get_statistics()
        assert stats["frameset_count"] == 2
        assert stats["roleset_count"] == 3  # give.01, give.02, abandon.01
        assert stats["total_roles"] == 8  # 3 + 2 + 3

    def test_add_frameset(self, sample_framesets):
        """Test adding framesets to index."""
        search = PropBankSearch()
        search.add_frameset(sample_framesets[0])

        assert search.get_statistics()["frameset_count"] == 1
        assert search.by_lemma("give") == sample_framesets[0]
        assert search.by_roleset_id("give.01") is not None

    def test_add_duplicate_frameset(self, sample_framesets):
        """Test adding duplicate frameset raises error."""
        search = PropBankSearch()
        search.add_frameset(sample_framesets[0])

        with pytest.raises(ValueError, match="already exists"):
            search.add_frameset(sample_framesets[0])

    def test_by_lemma(self, sample_framesets):
        """Test getting frameset by lemma."""
        search = PropBankSearch(sample_framesets)

        frameset = search.by_lemma("give")
        assert frameset is not None
        assert frameset.predicate_lemma == "give"
        assert len(frameset.rolesets) == 2

        assert search.by_lemma("nonexistent") is None

    def test_by_roleset_id(self, sample_framesets):
        """Test getting roleset by ID."""
        search = PropBankSearch(sample_framesets)

        roleset = search.by_roleset_id("give.01")
        assert roleset is not None
        assert roleset.name == "transfer"
        assert len(roleset.roles) == 3

        assert search.by_roleset_id("give.99") is None

    def test_by_pattern(self, sample_framesets):
        """Test searching framesets by pattern."""
        search = PropBankSearch(sample_framesets)

        # Test exact match
        results = search.by_pattern("give")
        assert len(results) == 1
        assert results[0].predicate_lemma == "give"

        # Test partial match
        results = search.by_pattern(".*ive")
        assert len(results) == 1
        assert results[0].predicate_lemma == "give"

        # Test case insensitive
        results = search.by_pattern("GIVE", case_sensitive=False)
        assert len(results) == 1

        # Test case sensitive
        results = search.by_pattern("GIVE", case_sensitive=True)
        assert len(results) == 0

        # Test no matches
        results = search.by_pattern("NoMatch")
        assert len(results) == 0

    def test_by_role_arg_num(self, sample_framesets):
        """Test finding rolesets by argument number."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets with ARG0
        results = search.by_role(arg_num="0")
        assert len(results) == 3  # All rolesets have ARG0

        # Find rolesets with ARG2
        results = search.by_role(arg_num="2")
        assert len(results) == 1  # Only give.01
        assert results[0].id == "give.01"

        # Find rolesets with ARGM
        results = search.by_role(arg_num="M")
        assert len(results) == 1  # Only abandon.01
        assert results[0].id == "abandon.01"

    def test_by_role_function_tag(self, sample_framesets):
        """Test finding rolesets by function tag."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets with PAG (agent)
        results = search.by_role(function_tag="PAG")
        assert len(results) == 3  # All rolesets

        # Find rolesets with GOL (goal)
        results = search.by_role(function_tag="GOL")
        assert len(results) == 1  # Only give.01
        assert results[0].id == "give.01"

        # Find rolesets with LOC (location)
        results = search.by_role(function_tag="LOC")
        assert len(results) == 1  # Only abandon.01
        assert results[0].id == "abandon.01"

    def test_by_role_combined(self, sample_framesets):
        """Test finding rolesets by both arg num and function tag."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets with ARG0 as PAG
        results = search.by_role(arg_num="0", function_tag="PAG")
        assert len(results) == 3  # All rolesets

        # Find rolesets with ARG2 as GOL
        results = search.by_role(arg_num="2", function_tag="GOL")
        assert len(results) == 1
        assert results[0].id == "give.01"

        # Find rolesets with ARGM as LOC
        results = search.by_role(arg_num="M", function_tag="LOC")
        assert len(results) == 1
        assert results[0].id == "abandon.01"

    def test_by_resource(self, sample_framesets):
        """Test finding rolesets by external resource."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets linked to VerbNet
        results = search.by_resource("VerbNet")
        assert len(results) == 2  # give.01 and abandon.01

        # Find rolesets linked to FrameNet
        results = search.by_resource("FrameNet")
        assert len(results) == 1  # Only give.01
        assert results[0].id == "give.01"

        # Find specific VerbNet class
        results = search.by_resource("VerbNet", "give-13.1")
        assert len(results) == 1
        assert results[0].id == "give.01"

        # Find specific FrameNet frame
        results = search.by_resource("FrameNet", "Giving")
        assert len(results) == 1
        assert results[0].id == "give.01"

    def test_search_aliases(self, sample_framesets):
        """Test searching by aliases."""
        search = PropBankSearch(sample_framesets)

        # Search for "giving"
        results = search.search_aliases("giving")
        assert len(results) == 1
        assert results[0].id == "give.01"

        # Search for "abandonment"
        results = search.search_aliases("abandonment")
        assert len(results) == 1
        assert results[0].id == "abandon.01"

        # Search with pattern
        results = search.search_aliases(".*ment")
        assert len(results) == 1
        assert results[0].id == "abandon.01"

        # Case insensitive
        results = search.search_aliases("GIVING", case_sensitive=False)
        assert len(results) == 1

    def test_get_all_lemmas(self, sample_framesets):
        """Test getting all lemmas."""
        search = PropBankSearch(sample_framesets)

        lemmas = search.get_all_lemmas()
        assert len(lemmas) == 2
        assert "abandon" in lemmas
        assert "give" in lemmas
        # Check sorted
        assert lemmas == sorted(lemmas)

    def test_get_all_rolesets(self, sample_framesets):
        """Test getting all rolesets."""
        search = PropBankSearch(sample_framesets)

        rolesets = search.get_all_rolesets()
        assert len(rolesets) == 3
        roleset_ids = [r.id for r in rolesets]
        assert "abandon.01" in roleset_ids
        assert "give.01" in roleset_ids
        assert "give.02" in roleset_ids
        # Check sorted
        assert roleset_ids == sorted(roleset_ids)

    def test_get_all_function_tags(self, sample_framesets):
        """Test getting all function tags."""
        search = PropBankSearch(sample_framesets)

        tags = search.get_all_function_tags()
        assert len(tags) == 4  # PAG, PPT, GOL, LOC
        assert "GOL" in tags
        assert "LOC" in tags
        assert "PAG" in tags
        assert "PPT" in tags
        # Check sorted
        assert tags == sorted(tags)

    def test_get_statistics(self, sample_framesets):
        """Test getting index statistics."""
        search = PropBankSearch(sample_framesets)

        stats = search.get_statistics()
        assert stats["frameset_count"] == 2
        assert stats["roleset_count"] == 3
        assert stats["unique_function_tags"] == 4  # PAG, PPT, GOL, LOC
        assert stats["unique_arg_numbers"] == 4  # 0, 1, 2, M
        assert stats["total_roles"] == 8
        assert stats["total_lexlinks"] == 3  # 2 + 1

    def test_invalid_regex_pattern(self, sample_framesets):
        """Test invalid regex patterns raise error."""
        search = PropBankSearch(sample_framesets)

        with pytest.raises(re.error):
            search.by_pattern("[invalid")

        with pytest.raises(re.error):
            search.search_aliases("(unclosed")
