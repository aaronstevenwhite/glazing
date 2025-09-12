"""VerbNet thematic role inheritance logic.

This module implements VerbNet's thematic role inheritance system, handling
role resolution through class hierarchies, override detection, and complex
inheritance chains.

Classes
-------
RoleInheritanceResolver
    Resolve thematic role inheritance in VerbNet classes.
InheritanceChain
    Track inheritance path through class hierarchy.

Functions
---------
get_effective_roles
    Calculate effective roles for a class considering inheritance.
resolve_inheritance_chain
    Resolve complete inheritance chain for a class.
detect_role_overrides
    Find roles that override parent class roles.

Examples
--------
>>> from glazing.verbnet.inheritance import RoleInheritanceResolver
>>> from glazing.verbnet.models import VerbClass, ThematicRole
>>> resolver = RoleInheritanceResolver()
>>> parent_class = VerbClass(
...     id="give-13.1",
...     themroles=[ThematicRole(type="Agent"), ThematicRole(type="Theme")],
...     ...
... )
>>> subclass = VerbClass(
...     id="give-13.1-1",
...     themroles=[],  # Empty = inherit all
...     parent_class="give-13.1",
...     ...
... )
>>> effective = resolver.get_effective_roles(subclass, parent_class.themroles)
>>> print(len(effective))  # Should be 2 (inherited Agent and Theme)
2
"""

from __future__ import annotations

from typing import Literal

from glazing.verbnet.models import (
    SelectionalRestriction,
    SelectionalRestrictions,
    ThematicRole,
    VerbClass,
)
from glazing.verbnet.types import ThematicRoleType, VerbClassID


class InheritanceChain:
    """Track inheritance path through VerbNet class hierarchy.

    Parameters
    ----------
    child_class_id : VerbClassID
        The subclass ID.
    parent_chain : list[VerbClassID]
        Chain of parent class IDs from child to root.
    role_resolutions : dict[ThematicRoleType, tuple[VerbClassID, ThematicRole]]
        Maps role types to their source class and definition.

    Methods
    -------
    get_depth()
        Get inheritance chain depth.
    get_role_source(role_type)
        Get which class defines a specific role.
    has_role_override(role_type)
        Check if role is overridden in subclass.
    """

    def __init__(
        self,
        child_class_id: VerbClassID,
        parent_chain: list[VerbClassID] | None = None,
        role_resolutions: dict[ThematicRoleType, tuple[VerbClassID, ThematicRole]] | None = None,
    ) -> None:
        """Initialize inheritance chain.

        Parameters
        ----------
        child_class_id : VerbClassID
            The subclass identifier.
        parent_chain : list[VerbClassID] | None, default=None
            Chain of parent class IDs.
        role_resolutions : dict | None, default=None
            Role resolution mappings.
        """
        self.child_class_id = child_class_id
        self.parent_chain = parent_chain or []
        self.role_resolutions = role_resolutions or {}

    def get_depth(self) -> int:
        """Get inheritance chain depth.

        Returns
        -------
        int
            Number of levels in inheritance chain.
        """
        return len(self.parent_chain)

    def get_role_source(
        self, role_type: ThematicRoleType
    ) -> tuple[VerbClassID, ThematicRole] | None:
        """Get which class defines a specific role.

        Parameters
        ----------
        role_type : ThematicRoleType
            Role type to look up.

        Returns
        -------
        tuple[VerbClassID, ThematicRole] | None
            Source class and role definition, or None if not found.
        """
        return self.role_resolutions.get(role_type)

    def has_role_override(self, role_type: ThematicRoleType) -> bool:
        """Check if role is overridden in subclass.

        Parameters
        ----------
        role_type : ThematicRoleType
            Role type to check.

        Returns
        -------
        bool
            True if role is defined in child class, overriding parent.
        """
        source_info = self.get_role_source(role_type)
        if not source_info:
            return False

        source_class_id, _ = source_info
        return source_class_id == self.child_class_id

    def get_inherited_roles(self) -> list[tuple[ThematicRoleType, VerbClassID]]:
        """Get roles inherited from parent classes.

        Returns
        -------
        list[tuple[ThematicRoleType, VerbClassID]]
            List of (role_type, source_class_id) for inherited roles.
        """
        inherited = []
        for role_type, (source_class, _) in self.role_resolutions.items():
            if source_class != self.child_class_id:
                inherited.append((role_type, source_class))
        return inherited

    def get_overridden_roles(self) -> list[tuple[ThematicRoleType, VerbClassID]]:
        """Get roles overridden by child class.

        Returns
        -------
        list[tuple[ThematicRoleType, VerbClassID]]
            List of (role_type, child_class_id) for overridden roles.
        """
        overridden = []
        for role_type, (source_class, _) in self.role_resolutions.items():
            if source_class == self.child_class_id:
                # Check if this role type exists in any parent
                # by looking for it in parent classes
                for _parent_id in self.parent_chain:
                    # If we had a parent with this role, it's an override
                    # For now, we consider any role defined in child as potential override
                    # Full implementation would need parent role data
                    pass
                # Add to overridden if defined in child
                overridden.append((role_type, self.child_class_id))
        return overridden

    def _get_parent_role_sets(self) -> list[set[ThematicRoleType]]:
        """Get role sets for each parent class.

        Returns
        -------
        list[set[ThematicRoleType]]
            Role sets for each parent in the chain.
        """
        parent_role_sets = []

        # Build role sets for each parent based on role_resolutions
        for parent_id in self.parent_chain:
            role_set = set()
            for role_type, (source_class, _) in self.role_resolutions.items():
                # Include roles that originate from this parent
                if source_class == parent_id:
                    role_set.add(role_type)
            if role_set:
                parent_role_sets.append(role_set)

        return parent_role_sets


class RoleInheritanceResolver:
    """Resolve thematic role inheritance in VerbNet classes.

    Handles VerbNet's inheritance system where empty THEMROLES elements
    indicate full inheritance from parent classes, and non-empty elements
    can override or extend parent roles.

    Methods
    -------
    get_effective_roles(verb_class, parent_roles)
        Calculate effective roles considering inheritance.
    resolve_inheritance_chain(class_hierarchy, class_id)
        Build complete inheritance chain for a class.
    detect_role_overrides(child_roles, parent_roles)
        Find roles that override parent definitions.
    merge_role_restrictions(child_role, parent_role)
        Merge selectional restrictions between child and parent roles.
    """

    def get_effective_roles(
        self,
        verb_class: VerbClass,
        parent_roles: list[ThematicRole] | None = None,
    ) -> list[ThematicRole]:
        """Calculate effective roles for a class considering inheritance.

        Implements VerbNet's inheritance rules:
        - Empty themroles list = inherit all parent roles
        - Non-empty themroles = child roles + non-overridden parent roles
        - Child roles with same type override parent roles completely

        Parameters
        ----------
        verb_class : VerbClass
            The verb class to calculate roles for.
        parent_roles : list[ThematicRole] | None, default=None
            Roles from parent class(es).

        Returns
        -------
        list[ThematicRole]
            Effective roles after applying inheritance rules.

        Examples
        --------
        >>> resolver = RoleInheritanceResolver()
        >>> parent_roles = [ThematicRole(type="Agent"), ThematicRole(type="Theme")]
        >>> # Empty themroles = full inheritance
        >>> child_empty = VerbClass(id="test-1", themroles=[], ...)
        >>> effective = resolver.get_effective_roles(child_empty, parent_roles)
        >>> len(effective)  # 2 (inherited both)
        2

        >>> # Override one role
        >>> child_override = VerbClass(
        ...     id="test-2",
        ...     themroles=[ThematicRole(type="Agent")],  # Override Agent only
        ...     ...
        ... )
        >>> effective = resolver.get_effective_roles(child_override, parent_roles)
        >>> len(effective)  # 2 (overridden Agent + inherited Theme)
        2
        """
        # Case 1: Empty themroles means full inheritance
        if not verb_class.themroles and parent_roles:
            return parent_roles.copy()

        # Case 2: No parent roles, return child roles only
        if not parent_roles:
            return verb_class.themroles.copy()

        # Case 3: Merge child and parent roles with child taking precedence
        final_roles = verb_class.themroles.copy()
        child_role_types = {role.type for role in verb_class.themroles}

        # Add non-overridden parent roles
        for parent_role in parent_roles:
            if parent_role.type not in child_role_types:
                final_roles.append(parent_role)

        return final_roles

    def resolve_inheritance_chain(
        self,
        class_hierarchy: dict[VerbClassID, VerbClass],
        class_id: VerbClassID,
    ) -> InheritanceChain:
        """Build complete inheritance chain for a VerbNet class.

        Parameters
        ----------
        class_hierarchy : dict[VerbClassID, VerbClass]
            Complete class hierarchy mapping.
        class_id : VerbClassID
            Class to build chain for.

        Returns
        -------
        InheritanceChain
            Complete inheritance chain with role resolutions.

        Raises
        ------
        ValueError
            If class_id is not found in hierarchy.
        """
        if class_id not in class_hierarchy:
            msg = f"Class {class_id} not found in hierarchy"
            raise ValueError(msg)

        # Build parent chain by following parent_class references
        parent_chain = []
        current_id = class_id
        visited = set()  # Prevent infinite loops

        while current_id in class_hierarchy:
            if current_id in visited:
                break  # Circular reference, stop

            visited.add(current_id)
            current_class = class_hierarchy[current_id]

            if current_class.parent_class:
                parent_chain.append(current_class.parent_class)
                current_id = current_class.parent_class
            else:
                break

        # Resolve roles through the chain
        role_resolutions = self._resolve_roles_through_chain(
            class_hierarchy, class_id, parent_chain
        )

        return InheritanceChain(
            child_class_id=class_id,
            parent_chain=parent_chain,
            role_resolutions=role_resolutions,
        )

    def detect_role_overrides(
        self,
        child_roles: list[ThematicRole],
        parent_roles: list[ThematicRole],
    ) -> dict[ThematicRoleType, tuple[ThematicRole, ThematicRole]]:
        """Find roles that override parent definitions.

        Parameters
        ----------
        child_roles : list[ThematicRole]
            Roles defined in child class.
        parent_roles : list[ThematicRole]
            Roles defined in parent class.

        Returns
        -------
        dict[ThematicRoleType, tuple[ThematicRole, ThematicRole]]
            Maps role type to (child_role, parent_role) for overrides.
        """
        overrides = {}

        parent_role_map = {role.type: role for role in parent_roles}

        for child_role in child_roles:
            if child_role.type in parent_role_map:
                parent_role = parent_role_map[child_role.type]
                overrides[child_role.type] = (child_role, parent_role)

        return overrides

    def merge_role_restrictions(
        self,
        child_role: ThematicRole,
        parent_role: ThematicRole,
    ) -> ThematicRole:
        """Merge selectional restrictions between child and parent roles.

        Parameters
        ----------
        child_role : ThematicRole
            Child role definition.
        parent_role : ThematicRole
            Parent role definition.

        Returns
        -------
        ThematicRole
            Merged role with combined restrictions.
        """
        # If child has no restrictions, inherit parent's
        if not child_role.sel_restrictions:
            return ThematicRole(type=child_role.type, sel_restrictions=parent_role.sel_restrictions)

        # If parent has no restrictions, use child's
        if not parent_role.sel_restrictions:
            return child_role

        # Both have restrictions - combine them with AND logic
        # Child restrictions take precedence but we preserve parent restrictions
        # that don't conflict
        merged_restrictions = []

        # Add child restrictions first (they have priority)
        if child_role.sel_restrictions and hasattr(child_role.sel_restrictions, "restrictions"):
            merged_restrictions.extend(child_role.sel_restrictions.restrictions)

        # Add parent restrictions that don't conflict
        if parent_role.sel_restrictions and hasattr(parent_role.sel_restrictions, "restrictions"):
            child_types = set()
            if child_role.sel_restrictions and hasattr(child_role.sel_restrictions, "restrictions"):
                for r in child_role.sel_restrictions.restrictions:
                    if isinstance(r, SelectionalRestriction):
                        child_types.add(r.type)

            for parent_r in parent_role.sel_restrictions.restrictions:
                if (
                    isinstance(parent_r, SelectionalRestriction)
                    and parent_r.type not in child_types
                ):
                    merged_restrictions.append(parent_r)

        # Create merged role
        logic: Literal["and", "or"] = "and"  # Default to AND for combined restrictions
        return ThematicRole(
            type=child_role.type,
            sel_restrictions=SelectionalRestrictions(logic=logic, restrictions=merged_restrictions)
            if merged_restrictions
            else None,
        )

    def get_inheritance_statistics(
        self,
        class_hierarchy: dict[VerbClassID, VerbClass],
        class_id: VerbClassID,
    ) -> dict[str, str | int | float | bool | list[str] | dict[str, int]]:
        """Get inheritance statistics for a class.

        Parameters
        ----------
        class_hierarchy : dict[VerbClassID, VerbClass]
            Complete class hierarchy.
        class_id : VerbClassID
            Class to analyze.

        Returns
        -------
        dict[str, str | int | float | bool | list[str] | dict[str, int]]
            Statistics about inheritance patterns.
        """
        if class_id not in class_hierarchy:
            return {}

        chain = self.resolve_inheritance_chain(class_hierarchy, class_id)
        current_class = class_hierarchy[class_id]

        # Calculate statistics
        stats: dict[str, str | int | float | bool | list[str] | dict[str, int]] = {
            "class_id": class_id,
            "inheritance_depth": chain.get_depth(),
            "parent_chain": chain.parent_chain,
            "total_roles": len(chain.role_resolutions),
            "inherited_roles": len(chain.get_inherited_roles()),
            "overridden_roles": len(chain.get_overridden_roles()),
            "local_roles": len(current_class.themroles),
            "has_empty_themroles": len(current_class.themroles) == 0,
        }

        # Role distribution by source
        source_distribution: dict[VerbClassID, int] = {}
        for _, (source_class, _) in chain.role_resolutions.items():
            source_distribution[source_class] = source_distribution.get(source_class, 0) + 1

        stats["role_sources"] = source_distribution

        return stats

    def _resolve_roles_through_chain(
        self,
        class_hierarchy: dict[VerbClassID, VerbClass],
        class_id: VerbClassID,
        parent_chain: list[VerbClassID],
    ) -> dict[ThematicRoleType, tuple[VerbClassID, ThematicRole]]:
        """Resolve roles through inheritance chain.

        Parameters
        ----------
        class_hierarchy : dict[VerbClassID, VerbClass]
            Class hierarchy mapping.
        class_id : VerbClassID
            Current class ID.
        parent_chain : list[VerbClassID]
            Chain of parent classes.

        Returns
        -------
        dict[ThematicRoleType, tuple[VerbClassID, ThematicRole]]
            Role resolutions with source classes.
        """
        role_resolutions = {}

        # Start with current class roles
        if class_id in class_hierarchy:
            current_class = class_hierarchy[class_id]

            # If current class has roles, they take precedence
            if current_class.themroles:
                for role in current_class.themroles:
                    role_resolutions[role.type] = (class_id, role)
            else:
                # Empty themroles = inherit from first parent with roles
                for parent_id in parent_chain:
                    if parent_id in class_hierarchy:
                        parent_class = class_hierarchy[parent_id]
                        if parent_class.themroles:
                            for role in parent_class.themroles:
                                if role.type not in role_resolutions:
                                    role_resolutions[role.type] = (parent_id, role)
                            break  # Stop at first parent with roles

        return role_resolutions


# Convenience functions for direct use


def get_effective_roles(
    verb_class: VerbClass,
    parent_roles: list[ThematicRole] | None = None,
) -> list[ThematicRole]:
    """Calculate effective roles for a VerbNet class considering inheritance.

    Parameters
    ----------
    verb_class : VerbClass
        The verb class to calculate roles for.
    parent_roles : list[ThematicRole] | None, default=None
        Roles from parent class.

    Returns
    -------
    list[ThematicRole]
        Effective roles after inheritance.
    """
    resolver = RoleInheritanceResolver()
    return resolver.get_effective_roles(verb_class, parent_roles)


def resolve_inheritance_chain(
    class_hierarchy: dict[VerbClassID, VerbClass],
    class_id: VerbClassID,
) -> InheritanceChain:
    """Resolve complete inheritance chain for a VerbNet class.

    Parameters
    ----------
    class_hierarchy : dict[VerbClassID, VerbClass]
        Complete class hierarchy mapping.
    class_id : VerbClassID
        Class to build chain for.

    Returns
    -------
    InheritanceChain
        Complete inheritance chain.
    """
    resolver = RoleInheritanceResolver()
    return resolver.resolve_inheritance_chain(class_hierarchy, class_id)


def detect_role_overrides(
    child_roles: list[ThematicRole],
    parent_roles: list[ThematicRole],
) -> dict[ThematicRoleType, tuple[ThematicRole, ThematicRole]]:
    """Find thematic roles that override parent definitions.

    Parameters
    ----------
    child_roles : list[ThematicRole]
        Roles from child class.
    parent_roles : list[ThematicRole]
        Roles from parent class.

    Returns
    -------
    dict[ThematicRoleType, tuple[ThematicRole, ThematicRole]]
        Override mappings.
    """
    resolver = RoleInheritanceResolver()
    return resolver.detect_role_overrides(child_roles, parent_roles)


def analyze_inheritance_patterns(
    class_hierarchy: dict[VerbClassID, VerbClass],
) -> dict[str, int | float | dict[str, int | float]]:
    """Analyze inheritance patterns across VerbNet classes.

    Parameters
    ----------
    class_hierarchy : dict[VerbClassID, VerbClass]
        Complete VerbNet class hierarchy.

    Returns
    -------
    dict[str, int | float | dict[str, int | float]]
        Analysis results including statistics and patterns.
    """
    resolver = RoleInheritanceResolver()

    # Overall statistics
    total_classes = len(class_hierarchy)
    classes_with_roles = sum(1 for cls in class_hierarchy.values() if cls.themroles)
    classes_with_empty_roles = total_classes - classes_with_roles

    # Inheritance depth analysis
    inheritance_depths = []
    for class_id in class_hierarchy:
        chain = resolver.resolve_inheritance_chain(class_hierarchy, class_id)
        inheritance_depths.append(chain.get_depth())

    max_depth = max(inheritance_depths) if inheritance_depths else 0
    avg_depth = sum(inheritance_depths) / len(inheritance_depths) if inheritance_depths else 0

    # Role override analysis
    total_overrides = 0
    for _class_id, verb_class in class_hierarchy.items():
        if verb_class.parent_class and verb_class.parent_class in class_hierarchy:
            parent_class = class_hierarchy[verb_class.parent_class]
            overrides = resolver.detect_role_overrides(verb_class.themroles, parent_class.themroles)
            total_overrides += len(overrides)

    return {
        "total_classes": total_classes,
        "classes_with_roles": classes_with_roles,
        "classes_with_empty_roles": classes_with_empty_roles,
        "inheritance_statistics": {
            "max_depth": max_depth,
            "average_depth": avg_depth,
            "total_overrides": total_overrides,
        },
        "empty_role_percentage": (
            (classes_with_empty_roles / total_classes) * 100 if total_classes > 0 else 0
        ),
    }
