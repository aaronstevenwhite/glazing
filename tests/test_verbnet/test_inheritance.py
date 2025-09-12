"""Tests for VerbNet inheritance logic.

Tests the VerbNet thematic role inheritance system including
role resolution, inheritance chains, and override detection.
"""

import pytest

from glazing.verbnet.inheritance import (
    InheritanceChain,
    RoleInheritanceResolver,
    analyze_inheritance_patterns,
    detect_role_overrides,
    get_effective_roles,
    resolve_inheritance_chain,
)
from glazing.verbnet.models import (
    SelectionalRestriction,
    SelectionalRestrictions,
    ThematicRole,
    VerbClass,
)


class TestInheritanceChain:
    """Test InheritanceChain functionality."""

    @pytest.fixture
    def sample_chain(self):
        """Create sample inheritance chain."""
        role_resolutions = {
            "Agent": ("give-13.1-1", ThematicRole(type="Agent", sel_restrictions=None)),
            "Theme": ("give-13.1", ThematicRole(type="Theme", sel_restrictions=None)),
            "Recipient": ("give-13.1", ThematicRole(type="Recipient", sel_restrictions=None)),
        }

        return InheritanceChain(
            child_class_id="give-13.1-1",
            parent_chain=["give-13.1", "give-13"],
            role_resolutions=role_resolutions,
        )

    def test_inheritance_chain_initialization(self):
        """Test inheritance chain initialization."""
        chain = InheritanceChain("test-1.0")

        assert chain.child_class_id == "test-1.0"
        assert chain.parent_chain == []
        assert chain.role_resolutions == {}

    def test_inheritance_chain_with_data(self, sample_chain):
        """Test inheritance chain with sample data."""
        assert sample_chain.child_class_id == "give-13.1-1"
        assert len(sample_chain.parent_chain) == 2
        assert len(sample_chain.role_resolutions) == 3

    def test_get_depth(self, sample_chain):
        """Test getting inheritance depth."""
        assert sample_chain.get_depth() == 2

    def test_get_role_source(self, sample_chain):
        """Test getting role source."""
        source = sample_chain.get_role_source("Agent")
        assert source is not None
        assert source[0] == "give-13.1-1"  # Defined in child class

        source = sample_chain.get_role_source("Theme")
        assert source is not None
        assert source[0] == "give-13.1"  # Inherited from parent

        source = sample_chain.get_role_source("NonExistent")
        assert source is None

    def test_has_role_override(self, sample_chain):
        """Test checking for role overrides."""
        # Agent is defined in child class
        assert sample_chain.has_role_override("Agent") is True

        # Theme is inherited from parent
        assert sample_chain.has_role_override("Theme") is False

        # Non-existent role
        assert sample_chain.has_role_override("NonExistent") is False

    def test_get_inherited_roles(self, sample_chain):
        """Test getting inherited roles."""
        inherited = sample_chain.get_inherited_roles()

        # Should include Theme and Recipient (both from give-13.1)
        assert len(inherited) == 2
        inherited_types = {role_type for role_type, _ in inherited}
        assert "Theme" in inherited_types
        assert "Recipient" in inherited_types
        assert "Agent" not in inherited_types  # This is overridden

    def test_get_overridden_roles(self, sample_chain):
        """Test getting overridden roles."""
        overridden = sample_chain.get_overridden_roles()

        # Agent is defined in child class, so it's overridden
        assert len(overridden) == 1
        assert overridden[0] == ("Agent", "give-13.1-1")


class TestRoleInheritanceResolver:
    """Test RoleInheritanceResolver functionality."""

    @pytest.fixture
    def resolver(self):
        """Create inheritance resolver instance."""
        return RoleInheritanceResolver()

    @pytest.fixture
    def parent_roles(self):
        """Create sample parent roles."""
        return [
            ThematicRole(
                type="Agent",
                sel_restrictions=SelectionalRestrictions(
                    logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
                ),
            ),
            ThematicRole(
                type="Theme",
                sel_restrictions=SelectionalRestrictions(
                    logic=None, restrictions=[SelectionalRestriction(value="-", type="animate")]
                ),
            ),
            ThematicRole(type="Recipient", sel_restrictions=None),
        ]

    @pytest.fixture
    def empty_child_class(self):
        """Create child class with empty thematic roles."""
        return VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[],  # Empty = inherit all
            frames=[],
            subclasses=[],
            parent_class="give-13.1",
        )

    @pytest.fixture
    def override_child_class(self):
        """Create child class that overrides some roles."""
        return VerbClass(
            id="give-13.1-2",
            members=[],
            themroles=[
                ThematicRole(
                    type="Agent",
                    sel_restrictions=SelectionalRestrictions(
                        logic=None,
                        restrictions=[SelectionalRestriction(value="+", type="organization")],
                    ),
                ),  # Override Agent with different restrictions
            ],
            frames=[],
            subclasses=[],
            parent_class="give-13.1",
        )

    def test_get_effective_roles_empty_child(self, resolver, empty_child_class, parent_roles):
        """Test effective roles with empty child class (full inheritance)."""
        effective = resolver.get_effective_roles(empty_child_class, parent_roles)

        # Should inherit all parent roles
        assert len(effective) == 3
        role_types = {role.type for role in effective}
        assert role_types == {"Agent", "Theme", "Recipient"}

        # Should be exact copies of parent roles
        for role in effective:
            if role.type == "Agent":
                assert role.sel_restrictions is not None
                assert len(role.sel_restrictions.restrictions) == 1

    def test_get_effective_roles_no_parent(self, resolver, override_child_class):
        """Test effective roles with no parent roles."""
        effective = resolver.get_effective_roles(override_child_class, None)

        # Should return only child roles
        assert len(effective) == 1
        assert effective[0].type == "Agent"

    def test_get_effective_roles_with_override(self, resolver, override_child_class, parent_roles):
        """Test effective roles with child overriding some parent roles."""
        effective = resolver.get_effective_roles(override_child_class, parent_roles)

        # Should have all 3 roles
        assert len(effective) == 3
        role_types = {role.type for role in effective}
        assert role_types == {"Agent", "Theme", "Recipient"}

        # Agent should be the child's version
        agent_role = next(role for role in effective if role.type == "Agent")
        assert agent_role.sel_restrictions is not None
        agent_restriction = agent_role.sel_restrictions.restrictions[0]
        assert agent_restriction.type == "organization"  # Child's restriction

        # Theme should be inherited from parent
        theme_role = next(role for role in effective if role.type == "Theme")
        assert theme_role.sel_restrictions is not None
        theme_restriction = theme_role.sel_restrictions.restrictions[0]
        assert theme_restriction.type == "animate"  # Parent's restriction

    def test_get_effective_roles_no_roles_no_parent(self, resolver):
        """Test effective roles with no child roles and no parent roles."""
        empty_class = VerbClass(
            id="empty-1.0",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        effective = resolver.get_effective_roles(empty_class, None)
        assert len(effective) == 0

    def test_resolve_inheritance_chain_basic(self, resolver):
        """Test resolving basic inheritance chain."""
        parent_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[
                ThematicRole(type="Agent", sel_restrictions=None),
                ThematicRole(type="Theme", sel_restrictions=None),
            ],
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        child_class = VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[],  # Inherit all
            frames=[],
            subclasses=[],
            parent_class="give-13.1",
        )

        hierarchy = {
            "give-13.1": parent_class,
            "give-13.1-1": child_class,
        }

        chain = resolver.resolve_inheritance_chain(hierarchy, "give-13.1-1")

        assert chain.child_class_id == "give-13.1-1"
        assert chain.parent_chain == ["give-13.1"]
        assert len(chain.role_resolutions) == 2  # Both roles from parent

    def test_resolve_inheritance_chain_missing_class(self, resolver):
        """Test resolving inheritance chain for non-existent class."""
        with pytest.raises(ValueError, match="Class nonexistent not found in hierarchy"):
            resolver.resolve_inheritance_chain({}, "nonexistent")

    def test_resolve_inheritance_chain_circular_reference(self, resolver):
        """Test resolving inheritance chain with circular reference."""
        # Create circular reference: A -> B -> A
        class_a = VerbClass(
            id="circular-13.1",
            members=[],
            themroles=[ThematicRole(type="Agent", sel_restrictions=None)],
            frames=[],
            subclasses=[],
            parent_class="circular-13.2",
        )

        class_b = VerbClass(
            id="circular-13.2",
            members=[],
            themroles=[ThematicRole(type="Theme", sel_restrictions=None)],
            frames=[],
            subclasses=[],
            parent_class="circular-13.1",  # Circular!
        )

        hierarchy = {
            "circular-13.1": class_a,
            "circular-13.2": class_b,
        }

        # Should handle circular reference gracefully
        chain = resolver.resolve_inheritance_chain(hierarchy, "circular-13.1")
        assert chain.child_class_id == "circular-13.1"
        # Should detect circular reference in the chain
        assert len(chain.parent_chain) >= 1
        assert "circular-13.2" in chain.parent_chain

    def test_detect_role_overrides(self, resolver, parent_roles):
        """Test detecting role overrides."""
        child_roles = [
            ThematicRole(type="Agent", sel_restrictions=None),  # Override
            ThematicRole(type="Location", sel_restrictions=None),  # New role
        ]

        overrides = resolver.detect_role_overrides(child_roles, parent_roles)

        # Should detect Agent override
        assert len(overrides) == 1
        assert "Agent" in overrides

        child_agent, parent_agent = overrides["Agent"]
        assert child_agent.type == "Agent"
        assert parent_agent.type == "Agent"

    def test_detect_role_overrides_no_overrides(self, resolver, parent_roles):
        """Test detecting overrides when there are none."""
        child_roles = [
            ThematicRole(type="Location", sel_restrictions=None),  # New role, not override
        ]

        overrides = resolver.detect_role_overrides(child_roles, parent_roles)
        assert len(overrides) == 0

    def test_merge_role_restrictions(self, resolver):
        """Test merging role restrictions."""
        # Test case 1: Child has no restrictions, inherit parent's
        child_role = ThematicRole(type="Agent", sel_restrictions=None)
        parent_role = ThematicRole(
            type="Agent",
            sel_restrictions=SelectionalRestrictions(
                logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
            ),
        )
        merged = resolver.merge_role_restrictions(child_role, parent_role)
        assert merged.sel_restrictions is not None
        assert len(merged.sel_restrictions.restrictions) == 1
        assert merged.sel_restrictions.restrictions[0].type == "animate"

        # Test case 2: Parent has no restrictions, use child's
        child_role = ThematicRole(
            type="Theme",
            sel_restrictions=SelectionalRestrictions(
                logic=None, restrictions=[SelectionalRestriction(value="+", type="concrete")]
            ),
        )
        parent_role = ThematicRole(type="Theme", sel_restrictions=None)
        merged = resolver.merge_role_restrictions(child_role, parent_role)
        assert merged.sel_restrictions is not None
        assert len(merged.sel_restrictions.restrictions) == 1
        assert merged.sel_restrictions.restrictions[0].type == "concrete"

        # Test case 3: Both have restrictions, combine them
        child_role = ThematicRole(
            type="Agent",
            sel_restrictions=SelectionalRestrictions(
                logic=None, restrictions=[SelectionalRestriction(value="+", type="human")]
            ),
        )
        parent_role = ThematicRole(
            type="Agent",
            sel_restrictions=SelectionalRestrictions(
                logic=None, restrictions=[SelectionalRestriction(value="+", type="animate")]
            ),
        )
        merged = resolver.merge_role_restrictions(child_role, parent_role)
        assert merged.sel_restrictions is not None
        # Child's restriction takes precedence, parent's non-conflicting added
        assert len(merged.sel_restrictions.restrictions) == 2
        restriction_types = {r.type for r in merged.sel_restrictions.restrictions}
        assert "human" in restriction_types
        assert "animate" in restriction_types

    def test_get_inheritance_statistics(self, resolver):
        """Test getting inheritance statistics."""
        parent_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[
                ThematicRole(type="Agent", sel_restrictions=None),
                ThematicRole(type="Theme", sel_restrictions=None),
            ],
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        child_class = VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[],  # Empty = inherit
            frames=[],
            subclasses=[],
            parent_class="give-13.1",
        )

        hierarchy = {
            "give-13.1": parent_class,
            "give-13.1-1": child_class,
        }

        stats = resolver.get_inheritance_statistics(hierarchy, "give-13.1-1")

        assert stats["class_id"] == "give-13.1-1"
        assert stats["inheritance_depth"] == 1
        assert stats["parent_chain"] == ["give-13.1"]
        assert stats["total_roles"] == 2  # Inherited Agent and Theme
        assert stats["inherited_roles"] == 2
        assert stats["overridden_roles"] == 0  # No overrides since themroles is empty
        assert stats["local_roles"] == 0
        assert stats["has_empty_themroles"] is True

    def test_get_inheritance_statistics_missing_class(self, resolver):
        """Test statistics for non-existent class returns empty dict."""
        stats = resolver.get_inheritance_statistics({}, "nonexistent")
        assert stats == {}


class TestInheritanceFunctions:
    """Test module-level inheritance functions."""

    @pytest.fixture
    def sample_roles(self):
        """Create sample roles for testing."""
        parent_roles = [
            ThematicRole(type="Agent", sel_restrictions=None),
            ThematicRole(type="Theme", sel_restrictions=None),
        ]
        child_roles = [ThematicRole(type="Agent", sel_restrictions=None)]  # Override Agent

        child_class = VerbClass(
            id="test-1.0",
            members=[],
            themroles=child_roles,
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        return parent_roles, child_roles, child_class

    def test_get_effective_roles_function(self, sample_roles):
        """Test get_effective_roles function."""
        parent_roles, _, child_class = sample_roles

        effective = get_effective_roles(child_class, parent_roles)

        assert len(effective) == 2  # Agent (overridden) + Theme (inherited)
        role_types = {role.type for role in effective}
        assert role_types == {"Agent", "Theme"}

    def test_resolve_inheritance_chain_function(self, sample_roles):
        """Test resolve_inheritance_chain function."""
        parent_roles, child_roles, child_class = sample_roles

        parent_class = VerbClass(
            id="test-13.1",
            members=[],
            themroles=parent_roles,
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        child_class.parent_class = "test-13.1"

        hierarchy = {
            "test-13.1": parent_class,
            "test-1.0": child_class,
        }

        chain = resolve_inheritance_chain(hierarchy, "test-1.0")

        assert isinstance(chain, InheritanceChain)
        assert chain.child_class_id == "test-1.0"

    def test_detect_role_overrides_function(self, sample_roles):
        """Test detect_role_overrides function."""
        parent_roles, child_roles, _ = sample_roles

        overrides = detect_role_overrides(child_roles, parent_roles)

        assert len(overrides) == 1
        assert "Agent" in overrides

    def test_analyze_inheritance_patterns(self):
        """Test inheritance pattern analysis."""
        # Create sample hierarchy
        parent_class = VerbClass(
            id="parent-1.0",
            members=[],
            themroles=[ThematicRole(type="Agent", sel_restrictions=None)],
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        child_with_roles = VerbClass(
            id="child-1.0",
            members=[],
            themroles=[ThematicRole(type="Theme", sel_restrictions=None)],
            frames=[],
            subclasses=[],
            parent_class="parent-1.0",
        )

        child_empty = VerbClass(
            id="child-2.0",
            members=[],
            themroles=[],  # Empty
            frames=[],
            subclasses=[],
            parent_class="parent-1.0",
        )

        hierarchy = {
            "parent-1.0": parent_class,
            "child-1.0": child_with_roles,
            "child-2.0": child_empty,
        }

        analysis = analyze_inheritance_patterns(hierarchy)

        assert analysis["total_classes"] == 3
        assert analysis["classes_with_roles"] == 2  # parent + child_with_roles
        assert analysis["classes_with_empty_roles"] == 1  # child_empty
        assert analysis["empty_role_percentage"] == pytest.approx(33.33, rel=1e-2)
        assert analysis["inheritance_statistics"]["max_depth"] == 1
        assert analysis["inheritance_statistics"]["average_depth"] > 0
