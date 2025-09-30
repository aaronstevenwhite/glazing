"""VerbNet core data models.

This module implements VerbNet verb classes, members, thematic roles,
selectional restrictions, and frame models with support for role inheritance
hierarchies.

Classes
-------
SelectionalRestriction
    Single selectional restriction on a thematic role.
SelectionalRestrictions
    Container for selectional restrictions with logical operators.
ThematicRole
    Thematic role with selectional restrictions.
WordNetCrossRef
    Cross-reference to WordNet from VerbNet.
VerbNetFrameNetRoleMapping
    Role-level mapping between VerbNet and FrameNet.
VerbNetFrameNetMapping
    VerbNet to FrameNet mapping with confidence.
MappingMetadata
    Metadata for cross-dataset mappings.
Member
    VerbNet member with cross-references.
VerbClass
    A VerbNet verb class with members and frames.
VNFrame
    Syntactic-semantic frame pattern.
FrameDescription
    Frame syntactic pattern description.
Example
    Frame example sentence.
Syntax
    Syntactic structure of a frame.
SyntaxElement
    Element in syntactic structure.
SyntacticRestriction
    Syntactic restriction on an element.
Semantics
    Semantic representation of a frame.
Predicate
    Semantic predicate in frame representation.
PredicateArgument
    Argument to a semantic predicate.

Examples
--------
>>> from glazing.verbnet.models import VerbClass, Member, ThematicRole
>>> verb_class = VerbClass(
...     id="give-13.1",
...     members=[],
...     themroles=[],
...     frames=[],
...     subclasses=[]
... )
>>> print(verb_class.id)
'give-13.1'
"""

from __future__ import annotations

import re
from typing import Self

from pydantic import Field, ValidationInfo, field_validator

from glazing.base import GlazingBaseModel
from glazing.references.models import (
    CrossReference,
    MappingMetadata,
    VerbNetFrameNetMapping,
)
from glazing.types import LogicType
from glazing.verbnet.types import (
    VERBNET_CLASS_PATTERN,
    VERBNET_KEY_PATTERN,
    ArgumentType,
    DescriptionNumber,
    PredicateType,
    RestrictionValue,
    SelectionalRestrictionType,
    SyntacticPOS,
    SyntacticRestrictionType,
    ThematicRoleType,
    VerbClassID,
    VerbNetKey,
    WordNetSense,
)


class SelectionalRestriction(GlazingBaseModel):
    """Single selectional restriction.

    Attributes
    ----------
    value : RestrictionValue
        Restriction polarity ("+" or "-").
    type : SelectionalRestrictionType
        Type of selectional restriction (e.g., "animate", "concrete").

    Examples
    --------
    >>> restriction = SelectionalRestriction(value="+", type="animate")
    >>> print(restriction.type)
    'animate'
    """

    value: RestrictionValue
    type: SelectionalRestrictionType


class SelectionalRestrictions(GlazingBaseModel):
    """Container for selectional restrictions with logic.

    Attributes
    ----------
    logic : LogicType | None, default=None
        Logical operator ("or", "and", or None for implicit AND).
    restrictions : list[SelectionalRestriction | SelectionalRestrictions]
        List of restrictions or nested restriction groups.

    Methods
    -------
    is_complex()
        Check if this contains nested restrictions.

    Examples
    --------
    >>> restrictions = SelectionalRestrictions(
    ...     logic="or",
    ...     restrictions=[
    ...         SelectionalRestriction(value="+", type="animate"),
    ...         SelectionalRestriction(value="+", type="human")
    ...     ]
    ... )
    >>> print(restrictions.is_complex())
    False
    """

    logic: LogicType | None = Field(None, description="Logical operator for combining restrictions")
    restrictions: list[SelectionalRestriction | SelectionalRestrictions] = Field(
        default_factory=list, description="List of restrictions or nested groups"
    )

    def is_complex(self) -> bool:
        """Check if this contains nested restrictions.

        Returns
        -------
        bool
            True if any restriction is a SelectionalRestrictions object.
        """
        return any(isinstance(r, SelectionalRestrictions) for r in self.restrictions)

    def validate_logic_consistency(self) -> bool:
        """Validate that logic operators are used consistently.

        Returns
        -------
        bool
            True if logic is consistent throughout the structure.
        """
        if not self.restrictions:
            return True

        # Check that nested restrictions don't conflict
        for restriction in self.restrictions:
            if (
                isinstance(restriction, SelectionalRestrictions)
                and not restriction.validate_logic_consistency()
            ):
                return False
        return True

    def flatten_restrictions(self) -> list[SelectionalRestriction]:
        """Flatten nested restrictions into a single list.

        Returns
        -------
        list[SelectionalRestriction]
            Flattened list of all restrictions.
        """
        result = []
        for restriction in self.restrictions:
            if isinstance(restriction, SelectionalRestriction):
                result.append(restriction)
            else:
                # Recursively flatten nested restrictions
                result.extend(restriction.flatten_restrictions())
        return result

    def check_contradiction(self) -> bool:
        """Check if restrictions contain contradictions.

        Returns
        -------
        bool
            True if contradictions are found (e.g., +animate and -animate).
        """
        if self.logic == "and" or self.logic is None:
            # For AND logic, check for direct contradictions
            flat = self.flatten_restrictions()
            type_values: dict[SelectionalRestrictionType, RestrictionValue] = {}
            for restriction in flat:
                if restriction.type in type_values:
                    if type_values[restriction.type] != restriction.value:
                        return True  # Found contradiction
                else:
                    type_values[restriction.type] = restriction.value
        return False


class ThematicRole(GlazingBaseModel):
    """Thematic role with selectional restrictions.

    Attributes
    ----------
    type : ThematicRoleType
        Type of thematic role (e.g., "Agent", "Theme", "Patient").
    sel_restrictions : SelectionalRestrictions | None, default=None
        Selectional restrictions on this role.

    Attributes
    ----------
    _class_id : str | None
        The class ID this role belongs to (set during parsing).

    Methods
    -------
    class_id()
        Get the class ID this role belongs to.

    Examples
    --------
    >>> role = ThematicRole(
    ...     type="Agent",
    ...     sel_restrictions=SelectionalRestrictions(
    ...         restrictions=[SelectionalRestriction(value="+", type="animate")]
    ...     )
    ... )
    >>> print(role.type)
    'Agent'
    """

    type: ThematicRoleType
    sel_restrictions: SelectionalRestrictions | None = Field(
        None, description="Selectional restrictions on this role"
    )

    def class_id(self) -> str | None:
        """Get the class ID this role belongs to (for inheritance).

        Returns
        -------
        str | None
            The class ID if set, None otherwise.
        """
        return getattr(self, "_class_id", None)


class WordNetCrossRef(GlazingBaseModel):
    """Cross-reference to WordNet from VerbNet.

    Attributes
    ----------
    sense_key : WordNetSense | None, default=None
        WordNet sense key (preferred, stable across versions).
    synset_offset : str | None, default=None
        WordNet synset offset (version-specific).
    lemma : str
        The lemma form.
    pos : str
        Part of speech ("n", "v", "a", "r", "s").
    sense_number : int | None, default=None
        Sense number in WordNet.

    Methods
    -------
    to_percentage_notation()
        Convert to VerbNet percentage notation.
    from_percentage_notation(notation)
        Parse VerbNet percentage notation.

    Examples
    --------
    >>> ref = WordNetCrossRef.from_percentage_notation("give%2:40:00")
    >>> print(ref.lemma)
    'give'
    """

    sense_key: WordNetSense | None = None
    synset_offset: str | None = None
    lemma: str
    pos: str
    sense_number: int | None = None

    def to_percentage_notation(self) -> str:
        """Convert to VerbNet percentage notation.

        Returns
        -------
        str
            Percentage notation string or empty string if incomplete.
        """
        if self.sense_key and "%" in self.sense_key:
            after_percent = self.sense_key.split("%")[1]
            parts = after_percent.split(":")
            if len(parts) >= 3:
                return f"{self.lemma}%{parts[0]}:{parts[1]}:{parts[2]}"
        return ""

    @classmethod
    def from_percentage_notation(cls, notation: str) -> Self:
        """Parse VerbNet percentage notation.

        Parameters
        ----------
        notation : str
            Percentage notation string (e.g., "word%2:40:00").

        Returns
        -------
        WordNetCrossRef
            Parsed cross-reference.

        Raises
        ------
        ValueError
            If notation format is invalid.
        """
        match = re.match(r"^([a-z_-]+)%([1-5]):([0-9]{2}):([0-9]{2})$", notation)
        if not match:
            msg = f"Invalid percentage notation: {notation}"
            raise ValueError(msg)

        lemma = match.group(1)
        ss_type = int(match.group(2))
        lex_filenum = match.group(3)
        lex_id = match.group(4)

        pos_map = {1: "n", 2: "v", 3: "a", 4: "r", 5: "s"}
        pos = pos_map[ss_type]

        sense_key = f"{lemma}%{ss_type}:{lex_filenum}:{lex_id}::"

        return cls(sense_key=sense_key, lemma=lemma, pos=pos)


class Member(GlazingBaseModel):
    """VerbNet member with cross-references.

    Attributes
    ----------
    name : str
        Lemma form (validated).
    verbnet_key : VerbNetKey
        Unique identifier with sense.
    framenet_mappings : list[VerbNetFrameNetMapping], default=[]
        FrameNet mappings with confidence.
    propbank_mappings : list[CrossReference], default=[]
        PropBank roleset mappings.
    wordnet_mappings : list[WordNetCrossRef], default=[]
        WordNet sense mappings.
    features : dict[str, str], default={}
        Semantic features.
    mapping_metadata : MappingMetadata | None, default=None
        Metadata about mappings.
    inherited_from_class : VerbClassID | None, default=None
        If inherited from parent class.

    Methods
    -------
    get_primary_framenet_frame()
        Get highest confidence FrameNet frame.
    get_all_framenet_frames()
        Get all FrameNet frames with confidence scores.
    get_wordnet_senses()
        Get WordNet senses in percentage notation.
    get_propbank_rolesets()
        Get PropBank roleset IDs.
    has_mapping_conflicts()
        Check if there are conflicting high-confidence mappings.

    Examples
    --------
    >>> member = Member(
    ...     name="give",
    ...     verbnet_key="give#2",
    ...     framenet_mappings=[],
    ...     propbank_mappings=[],
    ...     wordnet_mappings=[]
    ... )
    >>> print(member.verbnet_key)
    'give#2'
    """

    name: str = Field(description="Lemma form")
    verbnet_key: VerbNetKey = Field(description="Unique identifier with sense")
    framenet_mappings: list[VerbNetFrameNetMapping] = Field(
        default_factory=list, description="FrameNet mappings with confidence"
    )
    propbank_mappings: list[CrossReference] = Field(
        default_factory=list, description="PropBank roleset mappings"
    )
    wordnet_mappings: list[WordNetCrossRef] = Field(
        default_factory=list, description="WordNet sense mappings"
    )
    features: dict[str, str] = Field(default_factory=dict, description="Semantic features")
    mapping_metadata: MappingMetadata | None = None
    inherited_from_class: VerbClassID | None = None

    @field_validator("name")
    @classmethod
    def validate_member_name(cls, v: str) -> str:
        """Validate member name (verb lemma).

        Parameters
        ----------
        v : str
            Member name to validate.

        Returns
        -------
        str
            Validated member name.

        Raises
        ------
        ValueError
            If member name format is invalid.
        """
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_\-\.\s]*$", v):
            msg = f"Invalid member name format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("verbnet_key")
    @classmethod
    def validate_verbnet_key(cls, v: str) -> VerbNetKey:
        """Validate verbnet_key format.

        Parameters
        ----------
        v : str
            VerbNet key to validate.

        Returns
        -------
        str
            Validated VerbNet key.

        Raises
        ------
        ValueError
            If VerbNet key format is invalid.
        """
        if not re.match(VERBNET_KEY_PATTERN, v):
            msg = f"Invalid verbnet_key format: {v}"
            raise ValueError(msg)
        return v

    def get_primary_framenet_frame(self) -> str | None:
        """Get highest confidence FrameNet frame.

        Returns
        -------
        str | None
            Frame name or None if no mappings.
        """
        if not self.framenet_mappings:
            return None
        best = max(
            self.framenet_mappings,
            key=lambda m: m.confidence.score if m.confidence else 0.0,
            default=None,
        )
        return best.frame_name if best else None

    def get_all_framenet_frames(self) -> list[tuple[str, float | None]]:
        """Get all FrameNet frames with confidence scores.

        Returns
        -------
        list[tuple[str, float | None]]
            List of (frame_name, confidence_score) tuples.
        """
        frames = []
        for mapping in self.framenet_mappings:
            score = mapping.confidence.score if mapping.confidence else None
            frames.append((mapping.frame_name, score))
        return frames

    def get_wordnet_senses(self) -> list[str]:
        """Get WordNet senses in percentage notation.

        Returns
        -------
        list[str]
            List of percentage notation strings.
        """
        return [
            m.to_percentage_notation() for m in self.wordnet_mappings if m.to_percentage_notation()
        ]

    def get_propbank_rolesets(self) -> list[str]:
        """Get PropBank roleset IDs.

        Returns
        -------
        list[str]
            List of PropBank roleset IDs.
        """
        result: list[str] = []
        for m in self.propbank_mappings:
            if m.target_dataset == "propbank":
                if isinstance(m.target_id, list):
                    result.extend(m.target_id)
                else:
                    result.append(m.target_id)
        return result

    def has_mapping_conflicts(self) -> bool:
        """Check if there are conflicting high-confidence mappings.

        Returns
        -------
        bool
            True if multiple high-confidence FrameNet mappings exist.
        """
        high_conf_fn = [
            m for m in self.framenet_mappings if m.confidence and m.confidence.score > 0.7
        ]
        return len(high_conf_fn) > 1


class VerbClass(GlazingBaseModel):
    """A VerbNet verb class with members and frames.

    Attributes
    ----------
    id : VerbClassID
        Validated VerbNet class ID (e.g., "give-13.1").
    members : list[Member]
        Verb members in this class.
    themroles : list[ThematicRole]
        Thematic roles (may be empty for inheritance).
    frames : list[VNFrame]
        Frame specifications.
    subclasses : list[VerbClass]
        Recursive subclasses.
    parent_class : VerbClassID | None, default=None
        Parent class ID for subclasses.

    Methods
    -------
    get_effective_roles(parent_roles)
        Get effective roles considering inheritance from parent classes.
    get_all_members(include_subclasses)
        Get all members including those from subclasses.
    get_member_by_key(verbnet_key)
        Find a member by its VerbNet key.
    has_subclasses()
        Check if this class has subclasses.

    Examples
    --------
    >>> verb_class = VerbClass(
    ...     id="give-13.1",
    ...     members=[],
    ...     themroles=[
    ...         ThematicRole(type="Agent"),
    ...         ThematicRole(type="Theme"),
    ...         ThematicRole(type="Recipient")
    ...     ],
    ...     frames=[],
    ...     subclasses=[]
    ... )
    >>> roles = verb_class.get_effective_roles()
    >>> print(len(roles))
    3
    """

    id: VerbClassID = Field(description="VerbNet class ID")
    members: list[Member] = Field(default_factory=list, description="Verb members")
    themroles: list[ThematicRole] = Field(
        default_factory=list, description="Thematic roles (empty for inheritance)"
    )
    frames: list[VNFrame] = Field(default_factory=list, description="Frame specifications")
    subclasses: list[VerbClass] = Field(default_factory=list, description="Recursive subclasses")
    parent_class: VerbClassID | None = Field(None, description="Parent class ID for subclasses")

    @field_validator("id")
    @classmethod
    def validate_verbclass_id(cls, v: str) -> VerbClassID:
        """Validate VerbNet class ID format.

        Parameters
        ----------
        v : str
            Class ID to validate.

        Returns
        -------
        str
            Validated class ID.

        Raises
        ------
        ValueError
            If class ID format is invalid.
        """
        if not re.match(VERBNET_CLASS_PATTERN, v):
            msg = f"Invalid VerbNet class ID format: {v}"
            raise ValueError(msg)
        return v

    def get_effective_roles(
        self, parent_roles: list[ThematicRole] | None = None
    ) -> list[ThematicRole]:
        """Get effective roles considering inheritance from parent classes.

        Parameters
        ----------
        parent_roles : list[ThematicRole] | None, default=None
            Roles from parent class.

        Returns
        -------
        list[ThematicRole]
            Effective roles after applying inheritance rules.

        Notes
        -----
        If themroles is empty and parent_roles is provided, inherits all parent roles.
        Otherwise, subclass roles override parent roles of the same type.
        """
        if not self.themroles and parent_roles:
            return parent_roles
        if parent_roles:
            final_roles = self.themroles.copy()
            for parent_role in parent_roles:
                if not any(r.type == parent_role.type for r in self.themroles):
                    final_roles.append(parent_role)
            return final_roles
        return self.themroles

    def get_all_members(self, include_subclasses: bool = True) -> list[Member]:
        """Get all members including those from subclasses.

        Parameters
        ----------
        include_subclasses : bool, default=True
            Whether to include members from subclasses.

        Returns
        -------
        list[Member]
            All members in this class and optionally its subclasses.
        """
        members = self.members.copy()
        if include_subclasses:
            for subclass in self.subclasses:
                members.extend(subclass.get_all_members(include_subclasses=True))
        return members

    def get_member_by_key(self, verbnet_key: str) -> Member | None:
        """Find a member by its VerbNet key.

        Parameters
        ----------
        verbnet_key : str
            The VerbNet key to search for.

        Returns
        -------
        Member | None
            The member if found, None otherwise.
        """
        for member in self.get_all_members():
            if member.verbnet_key == verbnet_key:
                return member
        return None

    def has_subclasses(self) -> bool:
        """Check if this class has subclasses.

        Returns
        -------
        bool
            True if the class has subclasses.
        """
        return len(self.subclasses) > 0


# Frame Models


class Example(GlazingBaseModel):
    """Frame example sentence.

    Attributes
    ----------
    text : str
        The example sentence text.

    Examples
    --------
    >>> example = Example(text="John gave Mary a book")
    """

    text: str


class FrameDescription(GlazingBaseModel):
    """Frame syntactic pattern description.

    Attributes
    ----------
    description_number : DescriptionNumber
        The description number (e.g., "0.2", "2.5.1").
    primary : str
        Raw primary pattern string.
    secondary : str
        Raw secondary pattern string.
    xtag : str, default=""
        XTag reference (usually empty, sometimes "0.1", "0.2", or preposition patterns).
    primary_elements : list[str], default=[]
        Computed list of primary pattern elements.
    secondary_patterns : list[str], default=[]
        Computed list of secondary patterns.

    Examples
    --------
    >>> desc = FrameDescription(
    ...     description_number="0.2",
    ...     primary="NP V NP",
    ...     secondary="Basic Transitive"
    ... )
    """

    description_number: DescriptionNumber
    primary: str
    secondary: str
    xtag: str = ""
    primary_elements: list[str] = Field(default_factory=list)
    secondary_patterns: list[str] = Field(default_factory=list)

    @field_validator("description_number")
    @classmethod
    def validate_description_number(cls, v: str) -> DescriptionNumber:
        """Validate description number format.

        Parameters
        ----------
        v : str
            Description number to validate.

        Returns
        -------
        str
            Validated description number.

        Raises
        ------
        ValueError
            If description number format is invalid.
        """
        if v and not re.match(r"^[0-9]+(?:\.[0-9]+)*$", v):
            msg = f"Invalid description number format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("xtag")
    @classmethod
    def validate_xtag(cls, v: str) -> str:
        """Validate xtag format.

        Parameters
        ----------
        v : str
            XTag value to validate.

        Returns
        -------
        str
            Validated xtag value.
        """
        if v and not re.match(r"^([0-9]+(?:\.[0-9]+)?|[a-z/]+-PP)?$", v):
            # Don't fail validation, just log unusual values
            pass
        return v

    def model_post_init(self, _: dict[str, str | int | float | bool] | None) -> None:
        """Parse primary and secondary patterns after initialization."""
        # Parse primary pattern into elements
        if self.primary:
            self.primary_elements = self.primary.split()

        # Parse secondary pattern (can be semicolon-separated)
        if self.secondary:
            if ";" in self.secondary:
                self.secondary_patterns = [p.strip() for p in self.secondary.split(";")]
            else:
                self.secondary_patterns = [self.secondary.strip()] if self.secondary.strip() else []


class SyntacticRestriction(GlazingBaseModel):
    """Syntactic restriction on an element.

    Attributes
    ----------
    type : SyntacticRestrictionType
        The type of syntactic restriction.
    value : RestrictionValue
        The restriction value ("+" or "-").

    Examples
    --------
    >>> restriction = SyntacticRestriction(
    ...     type="be_sc_ing",
    ...     value="+"
    ... )
    """

    type: SyntacticRestrictionType
    value: RestrictionValue


class SyntaxElement(GlazingBaseModel):
    """Element in syntactic structure.

    Attributes
    ----------
    pos : SyntacticPOS
        Part of speech (NP, VERB, PREP, ADV, ADJ, LEX, ADVP, S, SBAR).
    value : str | None, default=None
        Role name or specific preposition values.
    synrestrs : list[SyntacticRestriction], default=[]
        Syntactic restrictions on this element.
    selrestrs : list[SelectionalRestriction], default=[]
        Selectional restrictions (for PREP).

    Examples
    --------
    >>> element = SyntaxElement(
    ...     pos="NP",
    ...     value="Agent"
    ... )
    >>> prep_element = SyntaxElement(
    ...     pos="PREP",
    ...     value="to for at"
    ... )
    """

    pos: SyntacticPOS
    value: str | None = None
    synrestrs: list[SyntacticRestriction] = Field(default_factory=list)
    selrestrs: list[SelectionalRestriction] = Field(default_factory=list)

    @field_validator("value")
    @classmethod
    def validate_prep_value(cls, v: str | None, info: ValidationInfo) -> str | None:
        """Validate preposition values.

        Parameters
        ----------
        v : str | None
            Value to validate.
        info : ValidationInfo
            Validation context.

        Returns
        -------
        str | None
            Validated value.

        Raises
        ------
        ValueError
            If preposition value format is invalid.
        """
        if (
            v
            and info.data.get("pos") == "PREP"
            and not re.match(r"^[a-zA-Z_?|\-]+(?:\s[a-zA-Z_?|\-]+)*$", v)
        ):
            msg = f"Invalid preposition value format: {v}"
            raise ValueError(msg)
        return v


class Syntax(GlazingBaseModel):
    """Syntactic structure of a frame.

    Attributes
    ----------
    elements : list[SyntaxElement]
        List of syntactic elements in order.

    Examples
    --------
    >>> syntax = Syntax(elements=[
    ...     SyntaxElement(pos="NP", value="Agent"),
    ...     SyntaxElement(pos="VERB"),
    ...     SyntaxElement(pos="NP", value="Theme")
    ... ])
    """

    elements: list[SyntaxElement]


class PredicateArgument(GlazingBaseModel):
    """Argument to a semantic predicate.

    Attributes
    ----------
    type : ArgumentType
        Type of argument (Event, ThemRole, etc.).
    value : str
        Argument value (e.g., "e1", "Agent", "?Theme").

    Examples
    --------
    >>> arg = PredicateArgument(type="ThemRole", value="Agent")
    >>> event_arg = PredicateArgument(type="Event", value="e1")
    """

    type: ArgumentType
    value: str

    @field_validator("value")
    @classmethod
    def validate_arg_value(cls, v: str, info: ValidationInfo) -> str:
        """Validate argument values based on type.

        Parameters
        ----------
        v : str
            Value to validate.
        info : ValidationInfo
            Validation context.

        Returns
        -------
        str
            Validated value.

        Raises
        ------
        ValueError
            If event variable format is invalid.
        """
        arg_type = info.data.get("type")
        if arg_type == "Event" and not re.match(r"^[eEë]\d*$", v):
            msg = f"Invalid event variable format: {v}"
            raise ValueError(msg)
        return v


class Predicate(GlazingBaseModel):
    """Semantic predicate in frame representation.

    Attributes
    ----------
    value : PredicateType
        The predicate type (e.g., "motion", "cause", "transfer").
    args : list[PredicateArgument]
        Arguments to the predicate.
    negated : bool, default=False
        Whether the predicate is negated (represents bool="!").

    Examples
    --------
    >>> pred = Predicate(
    ...     value="motion",
    ...     args=[
    ...         PredicateArgument(type="Event", value="e1"),
    ...         PredicateArgument(type="ThemRole", value="Agent")
    ...     ]
    ... )
    """

    value: PredicateType
    args: list[PredicateArgument]
    negated: bool = False

    @field_validator("negated", mode="before")
    @classmethod
    def parse_bool_attr(cls, v: str | bool | int | None) -> bool:
        """Parse XML bool attribute.

        Parameters
        ----------
        v : str | bool | int | None
            Value to parse.

        Returns
        -------
        bool
            True if value is "!", False otherwise.
        """
        if isinstance(v, str):
            return v == "!"
        return bool(v)


class Semantics(GlazingBaseModel):
    """Semantic representation of a frame.

    Attributes
    ----------
    predicates : list[Predicate]
        List of semantic predicates.

    Examples
    --------
    >>> semantics = Semantics(predicates=[
    ...     Predicate(
    ...         value="motion",
    ...         args=[PredicateArgument(type="Event", value="e1")]
    ...     )
    ... ])
    """

    predicates: list[Predicate]


class VNFrame(GlazingBaseModel):
    """Syntactic-semantic frame pattern.

    Attributes
    ----------
    description : FrameDescription
        Frame syntactic pattern description.
    examples : list[Example]
        Example sentences for this frame.
    syntax : Syntax
        Syntactic structure.
    semantics : Semantics
        Semantic representation.

    Examples
    --------
    >>> frame = VNFrame(
    ...     description=FrameDescription(
    ...         description_number="0.1",
    ...         primary="NP V NP",
    ...         secondary="Basic Transitive"
    ...     ),
    ...     examples=[Example(text="John hit the ball")],
    ...     syntax=Syntax(elements=[...]),
    ...     semantics=Semantics(predicates=[...])
    ... )
    """

    description: FrameDescription
    examples: list[Example]
    syntax: Syntax
    semantics: Semantics
