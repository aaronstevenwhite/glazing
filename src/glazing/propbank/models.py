"""PropBank data models.

Defines Pydantic models for PropBank framesets, rolesets, and annotations.

Classes
-------
Frameset
    Container for all senses of a predicate.
Alias
    Alias for a predicate with part of speech.
ArgAlias
    Argument-specific alias.
Aliases
    Container for all alias types.
Usage
    Usage information for a resource.
UsageNotes
    Container for usage information.
Roleset
    A single sense of a predicate with its semantic roles.
Role
    Semantic role definition.
RoleLink
    Link from a role to VerbNet/FrameNet.
LexLink
    Confidence-scored link to external resource.
PropBankAnnotation
    PropBank annotation structure for examples.
Arg
    Argument annotation in an example.
Rel
    Relation/predicate marker in example.
AMRAnnotation
    AMR annotation for an example.
Example
    Annotated example sentence.
"""

import re

from pydantic import Field, field_validator

from glazing.base import GlazingBaseModel
from glazing.propbank.types import (
    PREDICATE_LEMMA_PATTERN,
    ROLESET_ID_PATTERN,
    AliasPOS,
    ArgumentNumber,
    ArgumentTypePB,
    FunctionTag,
    IntOrQuestionMark,
    PredicateLemma,
    RolesetID,
    UsageInUse,
)
from glazing.types import MappingSource, ResourceType
from glazing.utils.special_cases import SpecialCaseRegistry


class Alias(GlazingBaseModel):
    """Alias for a predicate with part of speech.

    Attributes
    ----------
    text : str
        The alias text (e.g., "abandon", "abandonment").
    pos : AliasPOS
        Part of speech marker.

    Examples
    --------
    >>> alias = Alias(text="abandon", pos="v")
    >>> alias = Alias(text="abandonment", pos="n")
    """

    text: str
    pos: AliasPOS

    @field_validator("text")
    @classmethod
    def validate_alias_text(cls, v: str) -> str:
        """Validate alias text format.

        Parameters
        ----------
        v : str
            Alias text to validate.

        Returns
        -------
        str
            Validated alias text.

        Raises
        ------
        ValueError
            If alias text format is invalid.
        """
        # Allow: alphabetic start OR numeric start, plus spaces, hyphens, apostrophes, underscores
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_\-\'\s]*$", v):
            msg = f"Invalid alias text: {v}"
            raise ValueError(msg)
        return v


class ArgAlias(GlazingBaseModel):
    """Argument-specific alias.

    Attributes
    ----------
    text : str
        The alias text (e.g., "actress" for arg0 of "act").
    pos : AliasPOS
        Part of speech marker.
    arg : str
        Argument number it refers to (e.g., "0", "1").

    Examples
    --------
    >>> arg_alias = ArgAlias(text="giver", pos="n", arg="0")
    >>> arg_alias = ArgAlias(text="gift", pos="n", arg="1")
    """

    text: str
    pos: AliasPOS
    arg: str

    @field_validator("arg")
    @classmethod
    def validate_arg(cls, v: str) -> str:
        """Validate argument reference.

        Parameters
        ----------
        v : str
            Argument reference to validate.

        Returns
        -------
        str
            Validated argument reference.

        Raises
        ------
        ValueError
            If argument reference is invalid.
        """
        # Check standard argument references
        if v in ["0", "1", "2", "3", "4", "5", "6", "7", "M"]:
            return v

        # Check if it's a known special case
        if SpecialCaseRegistry.is_valid_arg_exception(v):
            return v

        msg = f"Invalid argument reference: {v}"
        raise ValueError(msg)


class Aliases(GlazingBaseModel):
    """Container for all alias types.

    Attributes
    ----------
    alias : list[Alias], default=[]
        Regular aliases for the predicate.
    argalias : list[ArgAlias], default=[]
        Argument-specific aliases.

    Examples
    --------
    >>> aliases = Aliases(
    ...     alias=[Alias(text="give", pos="v")],
    ...     argalias=[ArgAlias(text="giver", pos="n", arg="0")]
    ... )
    """

    alias: list[Alias] = Field(default_factory=list)
    argalias: list[ArgAlias] = Field(default_factory=list)


class Usage(GlazingBaseModel):
    """Usage information for a resource.

    Attributes
    ----------
    resource : ResourceType
        The resource type (e.g., "VerbNet", "FrameNet").
    version : str
        Version of the resource.
    inuse : UsageInUse
        Usage status indicator (+ or -).

    Examples
    --------
    >>> usage = Usage(resource="verbnet", version="3.4", inuse="+")
    """

    resource: ResourceType
    version: str
    inuse: UsageInUse


class UsageNotes(GlazingBaseModel):
    """Container for usage information.

    Attributes
    ----------
    usage : list[Usage]
        List of usage information.

    Examples
    --------
    >>> usage_notes = UsageNotes(
    ...     usage=[Usage(resource="VerbNet", version="3.4", inuse="+")]
    ... )
    """

    usage: list[Usage]


class RoleLink(GlazingBaseModel):
    """Link from a role to VerbNet/FrameNet.

    Attributes
    ----------
    class_name : str
        VerbNet class or FrameNet frame.
    resource : ResourceType
        Target resource type.
    version : str
        Version of the target resource.
    role : str | None, default=None
        Role name in target resource.

    Examples
    --------
    >>> link = RoleLink(
    ...     class_name="give-13.1",
    ...     resource="VerbNet",
    ...     version="3.4",
    ...     role="Agent"
    ... )
    """

    class_name: str
    resource: ResourceType
    version: str
    role: str | None = None

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        """Validate VerbNet class or FrameNet frame name.

        Parameters
        ----------
        v : str
            Class name to validate.

        Returns
        -------
        str
            Validated class name.
        """
        vn_pattern = r"^[a-z_]+-[\d.]+([-\d.]+)?$"
        fn_pattern = r"^[A-Z][A-Za-z0-9_]*$"
        special_pattern = r"^[a-z_]+$"

        if not (re.match(vn_pattern, v) or re.match(fn_pattern, v) or re.match(special_pattern, v)):
            pass
        return v


class Role(GlazingBaseModel):
    """Semantic role definition.

    Attributes
    ----------
    n : ArgumentNumber
        Argument number (0-7, m, or M).
    f : FunctionTag
        Function tag.
    descr : str
        Description of the role.
    rolelinks : list[RoleLink], default=[]
        Links to external resources.

    Examples
    --------
    >>> role = Role(
    ...     n="0",
    ...     f="PAG",
    ...     descr="The giver"
    ... )
    """

    n: ArgumentNumber
    f: FunctionTag
    descr: str
    rolelinks: list[RoleLink] = Field(default_factory=list)


class LexLink(GlazingBaseModel):
    """Confidence-scored link to external resource.

    Attributes
    ----------
    class_name : str
        Name of the external class/frame.
    confidence : float
        Confidence score (0.0-1.0).
    resource : ResourceType
        Target resource type.
    version : str
        Version of the target resource.
    src : MappingSource
        Source of the mapping.

    Examples
    --------
    >>> link = LexLink(
    ...     class_name="give-13.1",
    ...     confidence=0.95,
    ...     resource="VerbNet",
    ...     version="3.4",
    ...     src="manual"
    ... )
    """

    class_name: str
    confidence: float
    resource: ResourceType
    version: str
    src: MappingSource

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence score.

        Parameters
        ----------
        v : float
            Confidence score to validate.

        Returns
        -------
        float
            Validated confidence score.

        Raises
        ------
        ValueError
            If confidence is not between 0 and 1.
        """
        if not 0.0 <= v <= 1.0:
            msg = f"Confidence must be between 0 and 1: {v}"
            raise ValueError(msg)
        return v


class Roleset(GlazingBaseModel):
    """A single sense of a predicate with its semantic roles.

    Attributes
    ----------
    id : RolesetID
        Roleset identifier (e.g., "give.01").
    name : str | None, default=None
        Optional descriptive name.
    aliases : Aliases | None, default=None
        Predicate aliases.
    roles : list[Role]
        Semantic roles for this sense.
    usagenotes : UsageNotes | None, default=None
        Usage information.
    lexlinks : list[LexLink], default=[]
        Confidence-scored external links.
    examples : list[Example], default=[]
        Annotated example sentences.
    notes : list[str], default=[]
        Additional notes.

    Examples
    --------
    >>> roleset = Roleset(
    ...     id="give.01",
    ...     name="transfer",
    ...     roles=[
    ...         Role(n="0", f="PAG", descr="giver"),
    ...         Role(n="1", f="PPT", descr="thing given"),
    ...         Role(n="2", f="GOL", descr="entity given to")
    ...     ]
    ... )
    """

    id: RolesetID
    name: str | None = None
    aliases: Aliases | None = None
    roles: list[Role]
    usagenotes: UsageNotes | None = None
    lexlinks: list[LexLink] = Field(default_factory=list)
    examples: list["Example"] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_roleset_id(cls, v: str) -> str:
        """Validate roleset ID format.

        Parameters
        ----------
        v : str
            Roleset ID to validate.

        Returns
        -------
        str
            Validated roleset ID.

        Raises
        ------
        ValueError
            If roleset ID format is invalid.
        """
        # First check against the standard pattern (includes .LV for light verbs)
        if re.match(ROLESET_ID_PATTERN, v):
            return v

        # Check if it's a known special case
        if SpecialCaseRegistry.is_valid_roleset_exception(v):
            return v

        msg = f"Invalid roleset ID: {v}"
        raise ValueError(msg)


class Frameset(GlazingBaseModel):
    """Container for all senses of a predicate.

    Attributes
    ----------
    predicate_lemma : PredicateLemma
        The predicate lemma (e.g., "give", "abandon").
    rolesets : list[Roleset]
        All senses of this predicate.
    notes : list[str], default=[]
        Additional notes about the frameset.

    Examples
    --------
    >>> frameset = Frameset(
    ...     predicate_lemma="give",
    ...     rolesets=[
    ...         Roleset(id="give.01", name="transfer", roles=[...]),
    ...         Roleset(id="give.02", name="emit", roles=[...])
    ...     ]
    ... )
    """

    predicate_lemma: PredicateLemma
    rolesets: list[Roleset]
    notes: list[str] = Field(default_factory=list)

    @field_validator("predicate_lemma")
    @classmethod
    def validate_predicate_lemma(cls, v: str) -> str:
        """Validate predicate lemma format.

        Parameters
        ----------
        v : str
            Predicate lemma to validate.

        Returns
        -------
        str
            Validated predicate lemma.

        Raises
        ------
        ValueError
            If predicate lemma format is invalid.
        """
        # Allow alphabetic predicates OR pure numeric OR predicates with dots
        lemma_pattern = r"^[a-zA-Z][a-zA-Z0-9_\-\.]*$"
        if not (re.match(PREDICATE_LEMMA_PATTERN, v) or v.isdigit() or re.match(lemma_pattern, v)):
            msg = f"Invalid predicate lemma format: {v}"
            raise ValueError(msg)
        return v


class Arg(GlazingBaseModel):
    """Argument annotation in an example.

    Attributes
    ----------
    type : ArgumentTypePB
        Argument type (e.g., "ARG0", "ARGM-TMP").
    start : IntOrQuestionMark
        Start token index or "?" for unknown.
    end : IntOrQuestionMark
        End token index or "?" for unknown.
    text : str | None, default=None
        Extracted text (optional).

    Examples
    --------
    >>> arg = Arg(type="ARG0", start=0, end=1, text="John")
    >>> arg = Arg(type="ARGM-TMP", start=5, end=6, text="yesterday")
    >>> arg = Arg(type="ARG0", start="?", end="?")  # Unknown position
    """

    type: ArgumentTypePB
    start: IntOrQuestionMark
    end: IntOrQuestionMark
    text: str | None = None

    @field_validator("start", "end")
    @classmethod
    def validate_indices(cls, v: int | str) -> int | str:
        """Validate token indices.

        Parameters
        ----------
        v : int | str
            Token index or "?" to validate.

        Returns
        -------
        int | str
            Validated token index or "?".

        Raises
        ------
        ValueError
            If token index is invalid.
        """
        if v == "?":
            return v
        if isinstance(v, int) and v < 0:
            msg = f"Token index cannot be negative: {v}"
            raise ValueError(msg)
        return v


class Rel(GlazingBaseModel):
    """Relation/predicate marker in example.

    Attributes
    ----------
    relloc : str
        Location indices (can be space-separated).
    text : str | None, default=None
        The predicate text.

    Examples
    --------
    >>> rel = Rel(relloc="2", text="gave")
    >>> rel = Rel(relloc="2 3", text="gave up")
    """

    relloc: str
    text: str | None = None

    @field_validator("relloc")
    @classmethod
    def validate_relloc(cls, v: str) -> str:
        """Validate relation location format.

        Parameters
        ----------
        v : str
            Relation location to validate.

        Returns
        -------
        str
            Validated relation location.

        Raises
        ------
        ValueError
            If location format is invalid.
        """
        if not re.match(r"^\d+(\s+\d+)*$", v) and v != "?":
            msg = f"Invalid relloc format: {v}"
            raise ValueError(msg)
        return v


class PropBankAnnotation(GlazingBaseModel):
    """PropBank annotation structure for examples.

    Attributes
    ----------
    args : list[Arg], default=[]
        Argument annotations.
    rel : Rel | None, default=None
        Predicate/relation marker (optional, some annotations lack rel).
    notes : list[str], default=[]
        Additional annotation notes.

    Examples
    --------
    >>> annotation = PropBankAnnotation(
    ...     args=[
    ...         Arg(type="ARG0", start=0, end=1, text="John"),
    ...         Arg(type="ARG1", start=3, end=4, text="gift")
    ...     ],
    ...     rel=Rel(relloc="2", text="gave")
    ... )
    """

    args: list[Arg] = Field(default_factory=list)
    rel: Rel | None = None
    notes: list[str] = Field(default_factory=list)


class AMRAnnotation(GlazingBaseModel):
    """AMR annotation for an example.

    Attributes
    ----------
    version : str
        AMR version.
    graph : str
        AMR graph representation.

    Examples
    --------
    >>> amr = AMRAnnotation(
    ...     version="1.0",
    ...     graph="(g / give-01 :ARG0 (p / person :name John) :ARG1 (g2 / gift))"
    ... )
    """

    version: str
    graph: str


class Example(GlazingBaseModel):
    """Annotated example sentence.

    Attributes
    ----------
    name : str | None, default=None
        Optional example name.
    src : str | None, default=None
        Source of the example.
    text : str
        The sentence text.
    propbank : PropBankAnnotation | None, default=None
        PropBank annotation.
    amr : AMRAnnotation | None, default=None
        AMR annotation.
    notes : list[str], default=[]
        Additional notes.

    Examples
    --------
    >>> example = Example(
    ...     text="John gave Mary a book",
    ...     propbank=PropBankAnnotation(
    ...         args=[
    ...             Arg(type="ARG0", start=0, end=1),
    ...             Arg(type="ARG2", start=2, end=3),
    ...             Arg(type="ARG1", start=4, end=6)
    ...         ],
    ...         rel=Rel(relloc="1")
    ...     )
    ... )
    """

    name: str | None = None
    src: str | None = None
    text: str
    propbank: PropBankAnnotation | None = None
    amr: AMRAnnotation | None = None
    notes: list[str] = Field(default_factory=list)
