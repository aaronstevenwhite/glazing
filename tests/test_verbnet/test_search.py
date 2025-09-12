"""Tests for VerbNet search functionality."""

import pytest

from glazing.verbnet.models import (
    Example,
    FrameDescription,
    Member,
    Predicate,
    PredicateArgument,
    SelectionalRestriction,
    SelectionalRestrictions,
    Semantics,
    Syntax,
    SyntaxElement,
    ThematicRole,
    VerbClass,
    VNFrame,
)
from glazing.verbnet.search import VerbNetSearch


class TestVerbNetSearch:
    """Tests for VerbNetSearch class."""

    @pytest.fixture
    def sample_classes(self):
        """Create sample verb classes for testing."""
        # Create give-13.1 class
        give_class = VerbClass(
            id="give-13.1",
            members=[
                Member(name="give", verbnet_key="give#2"),
                Member(name="hand", verbnet_key="hand#1"),
                Member(name="pass", verbnet_key="pass#4"),
            ],
            themroles=[
                ThematicRole(
                    type="Agent",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
                    ),
                ),
                ThematicRole(
                    type="Theme",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None,
                        restrictions=[SelectionalRestriction(value="+", type="concrete")],
                    ),
                ),
                ThematicRole(
                    type="Recipient",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
                    ),
                ),
            ],
            frames=[
                VNFrame(
                    description=FrameDescription(
                        description_number="0.1", primary="NP V NP NP", secondary="Dative"
                    ),
                    examples=[Example(text="John gave Mary the book")],
                    syntax=Syntax(
                        elements=[
                            SyntaxElement(pos="NP", value="Agent"),
                            SyntaxElement(pos="VERB"),
                            SyntaxElement(pos="NP", value="Recipient"),
                            SyntaxElement(pos="NP", value="Theme"),
                        ]
                    ),
                    semantics=Semantics(
                        predicates=[
                            Predicate(
                                value="transfer",
                                args=[
                                    PredicateArgument(type="Event", value="e1"),
                                    PredicateArgument(type="ThemRole", value="Agent"),
                                    PredicateArgument(type="ThemRole", value="Theme"),
                                    PredicateArgument(type="ThemRole", value="Recipient"),
                                ],
                            ),
                            Predicate(
                                value="has_possession",
                                args=[
                                    PredicateArgument(type="Event", value="e2"),
                                    PredicateArgument(type="ThemRole", value="Recipient"),
                                    PredicateArgument(type="ThemRole", value="Theme"),
                                ],
                            ),
                        ]
                    ),
                )
            ],
            subclasses=[],
        )

        # Create run-51.3.2 class (motion)
        run_class = VerbClass(
            id="run-51.3.2",
            members=[
                Member(name="run", verbnet_key="run#1"),
                Member(name="walk", verbnet_key="walk#1"),
                Member(name="jog", verbnet_key="jog#1"),
            ],
            themroles=[
                ThematicRole(
                    type="Agent",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
                    ),
                ),
                ThematicRole(type="Path", sel_restrictions=None),
                ThematicRole(
                    type="Location",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None,
                        restrictions=[SelectionalRestriction(value="+", type="location")],
                    ),
                ),
            ],
            frames=[
                VNFrame(
                    description=FrameDescription(
                        description_number="0.1", primary="NP V PP", secondary="Basic Intransitive"
                    ),
                    examples=[Example(text="John ran to the store")],
                    syntax=Syntax(
                        elements=[
                            SyntaxElement(pos="NP", value="Agent"),
                            SyntaxElement(pos="VERB"),
                            SyntaxElement(pos="PREP", value="to"),
                            SyntaxElement(pos="NP", value="Location"),
                        ]
                    ),
                    semantics=Semantics(
                        predicates=[
                            Predicate(
                                value="motion",
                                args=[
                                    PredicateArgument(type="Event", value="e1"),
                                    PredicateArgument(type="ThemRole", value="Agent"),
                                ],
                            ),
                            Predicate(
                                value="path",
                                args=[
                                    PredicateArgument(type="Event", value="e2"),
                                    PredicateArgument(type="ThemRole", value="Agent"),
                                    PredicateArgument(type="ThemRole", value="Path"),
                                ],
                            ),
                        ]
                    ),
                )
            ],
            subclasses=[],
        )

        # Create break-45.1 class (change of state)
        break_class = VerbClass(
            id="break-45.1",
            members=[
                Member(name="break", verbnet_key="break#1"),
                Member(name="shatter", verbnet_key="shatter#1"),
            ],
            themroles=[
                ThematicRole(
                    type="Agent",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
                    ),
                ),
                ThematicRole(
                    type="Patient",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None, restrictions=[SelectionalRestriction(value="+", type="solid")]
                    ),
                ),
                ThematicRole(
                    type="Instrument",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None,
                        restrictions=[SelectionalRestriction(value="+", type="concrete")],
                    ),
                ),
            ],
            frames=[
                VNFrame(
                    description=FrameDescription(
                        description_number="0.1", primary="NP V NP", secondary="Transitive"
                    ),
                    examples=[Example(text="John broke the window")],
                    syntax=Syntax(
                        elements=[
                            SyntaxElement(pos="NP", value="Agent"),
                            SyntaxElement(pos="VERB"),
                            SyntaxElement(pos="NP", value="Patient"),
                        ]
                    ),
                    semantics=Semantics(
                        predicates=[
                            Predicate(
                                value="cause",
                                args=[
                                    PredicateArgument(type="Event", value="e1"),
                                    PredicateArgument(type="ThemRole", value="Agent"),
                                ],
                            ),
                            Predicate(
                                value="change",
                                args=[
                                    PredicateArgument(type="Event", value="e2"),
                                    PredicateArgument(type="ThemRole", value="Patient"),
                                ],
                            ),
                        ]
                    ),
                )
            ],
            subclasses=[],
        )

        return [give_class, run_class, break_class]

    def test_init_empty(self):
        """Test initialization with empty search."""
        search = VerbNetSearch()
        assert search.get_statistics()["class_count"] == 0
        assert search.get_all_predicates() == []
        assert search.get_all_roles() == []
        assert search.get_all_members() == []

    def test_init_with_classes(self, sample_classes):
        """Test initialization with classes."""
        search = VerbNetSearch(sample_classes)
        stats = search.get_statistics()
        assert stats["class_count"] == 3
        assert (
            stats["unique_predicates"] == 6
        )  # transfer, has_possession, motion, path, cause, change
        assert (
            stats["unique_roles"] == 7
        )  # Agent, Theme, Recipient, Path, Location, Patient, Instrument
        assert stats["unique_members"] == 8  # give, hand, pass, run, walk, jog, break, shatter

    def test_add_class(self, sample_classes):
        """Test adding classes to search."""
        search = VerbNetSearch()
        search.add_class(sample_classes[0])

        assert search.get_statistics()["class_count"] == 1
        assert "give" in search.get_all_members()

    def test_add_duplicate_class(self, sample_classes):
        """Test adding duplicate class raises error."""
        search = VerbNetSearch()
        search.add_class(sample_classes[0])

        with pytest.raises(ValueError, match="already exists"):
            search.add_class(sample_classes[0])

    def test_by_themroles(self, sample_classes):
        """Test finding classes by thematic roles."""
        search = VerbNetSearch(sample_classes)

        # Find classes with Agent and Theme
        results = search.by_themroles(["Agent", "Theme"])
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Find classes with Agent only
        results = search.by_themroles(["Agent"])
        assert len(results) == 3  # All have Agent

        # Find classes with exactly Agent, Path, Location
        results = search.by_themroles(["Agent", "Path", "Location"], only=True)
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

        # Find classes with non-existent role
        results = search.by_themroles(["NonExistent"])
        assert len(results) == 0

    def test_by_syntax(self, sample_classes):
        """Test finding classes by syntactic patterns."""
        search = VerbNetSearch(sample_classes)

        # Find ditransitive pattern
        results = search.by_syntax("NP VERB NP NP")
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Find transitive pattern
        results = search.by_syntax("NP VERB NP")
        assert len(results) == 1
        assert results[0].id == "break-45.1"

        # Find PP pattern
        results = search.by_syntax("NP VERB PREP NP")
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

        # Non-existent pattern
        results = search.by_syntax("NP NP NP")
        assert len(results) == 0

    def test_by_predicate(self, sample_classes):
        """Test finding classes by semantic predicate."""
        search = VerbNetSearch(sample_classes)

        # Find classes with "transfer" predicate
        results = search.by_predicate("transfer")
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Find classes with "motion" predicate
        results = search.by_predicate("motion")
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

        # Find classes with "cause" predicate
        results = search.by_predicate("cause")
        assert len(results) == 1
        assert results[0].id == "break-45.1"

        # Non-existent predicate
        results = search.by_predicate("nonexistent")
        assert len(results) == 0

    def test_by_predicates(self, sample_classes):
        """Test finding classes by multiple predicates."""
        search = VerbNetSearch(sample_classes)

        # Find classes with both "transfer" and "has_possession"
        results = search.by_predicates(["transfer", "has_possession"], require_all=True)
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Find classes with either "motion" or "path"
        results = search.by_predicates(["motion", "path"], require_all=False)
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

        # Find classes with either "cause" or "transfer"
        results = search.by_predicates(["cause", "transfer"], require_all=False)
        assert len(results) == 2
        class_ids = [c.id for c in results]
        assert "break-45.1" in class_ids
        assert "give-13.1" in class_ids

    def test_by_restriction(self, sample_classes):
        """Test finding classes by selectional restrictions."""
        search = VerbNetSearch(sample_classes)

        # Find classes with animate Agent
        results = search.by_restriction("Agent", "animate", "+")
        assert len(results) == 3  # All have animate Agent

        # Find classes with concrete Theme
        results = search.by_restriction("Theme", "concrete", "+")
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Find classes with solid Patient
        results = search.by_restriction("Patient", "solid", "+")
        assert len(results) == 1
        assert results[0].id == "break-45.1"

        # Find classes with location Location
        results = search.by_restriction("Location", "location", "+")
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

    def test_by_members(self, sample_classes):
        """Test finding classes by member verbs."""
        search = VerbNetSearch(sample_classes)

        # Find classes with "give"
        results = search.by_members(["give"])
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Find classes with "run" or "walk"
        results = search.by_members(["run", "walk"])
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

        # Find classes with "break"
        results = search.by_members(["break"])
        assert len(results) == 1
        assert results[0].id == "break-45.1"

        # Find classes with multiple members
        results = search.by_members(["give", "break"])
        assert len(results) == 2

        # Non-existent member
        results = search.by_members(["nonexistent"])
        assert len(results) == 0

    def test_complex_search(self, sample_classes):
        """Test multi-criteria search."""
        search = VerbNetSearch(sample_classes)

        # Search for transfer classes with Agent, Theme, Recipient
        results = search.complex_search(
            predicates=["transfer"], themroles=["Agent", "Theme", "Recipient"]
        )
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Search for motion classes with Agent
        results = search.complex_search(predicates=["motion"], themroles=["Agent"])
        assert len(results) == 1
        assert results[0].id == "run-51.3.2"

        # Search with restrictions
        results = search.complex_search(
            themroles=["Agent"], restrictions={"Agent": [("+", "animate")]}
        )
        assert len(results) == 3  # All have animate Agent

        # Search with syntax
        results = search.complex_search(syntax="NP VERB NP NP")
        assert len(results) == 1
        assert results[0].id == "give-13.1"

        # Complex search with multiple criteria
        results = search.complex_search(
            predicates=["cause", "change"], themroles=["Agent", "Patient"], syntax="NP VERB NP"
        )
        assert len(results) == 1
        assert results[0].id == "break-45.1"

    def test_get_all_predicates(self, sample_classes):
        """Test getting all predicates."""
        search = VerbNetSearch(sample_classes)

        predicates = search.get_all_predicates()
        assert len(predicates) == 6
        assert "cause" in predicates
        assert "change" in predicates
        assert "has_possession" in predicates
        assert "motion" in predicates
        assert "path" in predicates
        assert "transfer" in predicates

        # Check sorted
        assert predicates == sorted(predicates)

    def test_get_all_roles(self, sample_classes):
        """Test getting all thematic roles."""
        search = VerbNetSearch(sample_classes)

        roles = search.get_all_roles()
        assert len(roles) == 7
        assert "Agent" in roles
        assert "Instrument" in roles
        assert "Location" in roles
        assert "Path" in roles
        assert "Patient" in roles
        assert "Recipient" in roles
        assert "Theme" in roles

        # Check sorted
        assert roles == sorted(roles)

    def test_get_all_members(self, sample_classes):
        """Test getting all member lemmas."""
        search = VerbNetSearch(sample_classes)

        members = search.get_all_members()
        assert len(members) == 8
        assert "break" in members
        assert "give" in members
        assert "hand" in members
        assert "jog" in members
        assert "pass" in members
        assert "run" in members
        assert "shatter" in members
        assert "walk" in members

        # Check sorted
        assert members == sorted(members)

    def test_get_statistics(self, sample_classes):
        """Test getting search statistics."""
        search = VerbNetSearch(sample_classes)

        stats = search.get_statistics()
        assert stats["class_count"] == 3
        assert stats["unique_predicates"] == 6
        assert stats["unique_roles"] == 7
        assert stats["unique_members"] == 8
        assert stats["total_members"] == 8
        assert stats["total_frames"] == 3
