"""VerbNet Generative Lexicon (GL) models.

This module implements VerbNet-GL extensions that enhance VerbNet with
Generative Lexicon features including event structure, qualia, and
opposition structures for deeper semantic representations.

Classes
-------
GLVerbClass
    VerbNet class with Generative Lexicon features.
GLFrame
    Frame with GL event structure and qualia.
Subcategorization
    GL subcategorization with variable assignments.
SubcatMember
    Subcategorization member with variable.
EventStructure
    Temporal event decomposition.
Event
    Single event in event structure.
Subevent
    Subevent with temporal relations.
Qualia
    Qualia structure for frame semantics.
Opposition
    Semantic opposition structure.
State
    State in opposition structure.

Examples
--------
>>> from glazing.verbnet.gl_models import GLVerbClass, GLFrame
>>> gl_class = GLVerbClass(
...     verb_class=verb_class,
...     gl_frames=[]
... )
"""

from __future__ import annotations

from pydantic import Field

from glazing.base import GlazingBaseModel
from glazing.verbnet.models import VerbClass, VNFrame
from glazing.verbnet.types import (
    EventType,
    GLSubcatPOS,
    GLTemporalRelation,
    GLVariable,
    OppositionType,
    PrepositionValue,
    ThematicRoleType,
)


class State(GlazingBaseModel):
    """State in opposition structure.

    Attributes
    ----------
    predicate : str
        The state predicate.
    args : list[str]
        Arguments to the state predicate.
    negated : bool, default=False
        Whether the state is negated.

    Examples
    --------
    >>> state = State(
    ...     predicate="at_location",
    ...     args=["x", "y"],
    ...     negated=False
    ... )
    """

    predicate: str
    args: list[str]
    negated: bool = False


class Opposition(GlazingBaseModel):
    """Semantic opposition structure.

    Attributes
    ----------
    type : OppositionType
        Type of opposition (e.g., "motion", "state_change").
    initial_state : State
        The initial state.
    final_state : State
        The final state.

    Examples
    --------
    >>> opposition = Opposition(
    ...     type="motion",
    ...     initial_state=State(predicate="at_location", args=["x", "source"]),
    ...     final_state=State(predicate="at_location", args=["x", "goal"])
    ... )
    """

    type: OppositionType
    initial_state: State
    final_state: State


class Event(GlazingBaseModel):
    """Single event in event structure.

    Attributes
    ----------
    id : str
        Event identifier (e.g., "e1", "e2").
    type : EventType
        Event type (e.g., "process", "state", "transition").
    participants : dict[str, str]
        Mapping from roles to variables.

    Examples
    --------
    >>> event = Event(
    ...     id="e1",
    ...     type="process",
    ...     participants={"Agent": "x", "Theme": "y"}
    ... )
    """

    id: str
    type: EventType
    participants: dict[str, str]


class Subevent(GlazingBaseModel):
    """Subevent with temporal relations.

    Attributes
    ----------
    id : str
        Subevent identifier.
    parent_event : str
        Parent event identifier.
    relation : GLTemporalRelation
        Temporal relation (e.g., "starts", "culminates", "results").
    predicate : str
        Subevent predicate.
    args : list[str]
        Arguments to the subevent.

    Examples
    --------
    >>> subevent = Subevent(
    ...     id="e1.1",
    ...     parent_event="e1",
    ...     relation="starts",
    ...     predicate="motion",
    ...     args=["x", "source", "goal"]
    ... )
    """

    id: str
    parent_event: str
    relation: GLTemporalRelation
    predicate: str
    args: list[str]


class EventStructure(GlazingBaseModel):
    """Temporal event decomposition.

    Attributes
    ----------
    events : list[Event]
        List of events.
    subevents : list[Subevent], default=[]
        List of subevents with temporal relations.

    Examples
    --------
    >>> event_structure = EventStructure(
    ...     events=[Event(id="e1", type="process", participants={})],
    ...     subevents=[]
    ... )
    """

    events: list[Event]
    subevents: list[Subevent] = Field(default_factory=list)


class Qualia(GlazingBaseModel):
    """Qualia structure for frame semantics.

    Attributes
    ----------
    formal : str | None, default=None
        What type of thing it is.
    constitutive : str | None, default=None
        What it's made of.
    telic : str | None, default=None
        Purpose or function.
    agentive : str | None, default=None
        How it comes about.

    Examples
    --------
    >>> qualia = Qualia(
    ...     formal="object",
    ...     constitutive="material",
    ...     telic="transport",
    ...     agentive="manufacture"
    ... )
    """

    formal: str | None = None
    constitutive: str | None = None
    telic: str | None = None
    agentive: str | None = None


class SubcatMember(GlazingBaseModel):
    """Subcategorization member with variable.

    Attributes
    ----------
    role : ThematicRoleType
        Thematic role name.
    variable : GLVariable
        Variable assignment (e.g., "x", "y", "z").
    pos : GLSubcatPOS
        Part of speech.
    prep : PrepositionValue | None, default=None
        Preposition for PP roles.

    Examples
    --------
    >>> member = SubcatMember(
    ...     role="Agent",
    ...     variable="x",
    ...     pos="NP"
    ... )
    """

    role: ThematicRoleType
    variable: GLVariable
    pos: GLSubcatPOS
    prep: PrepositionValue | None = None


class Subcategorization(GlazingBaseModel):
    """GL subcategorization with variable assignments.

    Attributes
    ----------
    members : list[SubcatMember]
        List of subcategorization members.

    Examples
    --------
    >>> subcat = Subcategorization(members=[
    ...     SubcatMember(role="Agent", variable="x", pos="NP"),
    ...     SubcatMember(role="Theme", variable="y", pos="NP")
    ... ])
    """

    members: list[SubcatMember]


class GLFrame(GlazingBaseModel):
    """Frame with GL event structure and qualia.

    Attributes
    ----------
    vn_frame : VNFrame
        Base VerbNet frame.
    subcat : Subcategorization
        Subcategorization with variable assignments.
    qualia : Qualia | None, default=None
        Qualia structure.
    event_structure : EventStructure
        Event structure decomposition.
    opposition : Opposition | None, default=None
        Opposition structure.

    Examples
    --------
    >>> gl_frame = GLFrame(
    ...     vn_frame=vn_frame,
    ...     subcat=Subcategorization(members=[]),
    ...     event_structure=EventStructure(events=[]),
    ...     qualia=None,
    ...     opposition=None
    ... )
    """

    vn_frame: VNFrame
    subcat: Subcategorization
    qualia: Qualia | None = None
    event_structure: EventStructure
    opposition: Opposition | None = None


class GLVerbClass(GlazingBaseModel):
    """VerbNet class with Generative Lexicon features.

    Attributes
    ----------
    verb_class : VerbClass
        Base VerbNet class.
    gl_frames : list[GLFrame]
        List of GL frames.

    Methods
    -------
    is_motion_class()
        Check if this is a motion verb class.
    is_change_of_possession_class()
        Check if this involves possession transfer.
    is_change_of_info_class()
        Check if this involves information transfer.

    Examples
    --------
    >>> gl_class = GLVerbClass(
    ...     verb_class=verb_class,
    ...     gl_frames=[]
    ... )
    >>> is_motion = gl_class.is_motion_class()
    """

    verb_class: VerbClass
    gl_frames: list[GLFrame]

    def is_motion_class(self) -> bool:
        """Check if this is a motion verb class.

        Returns
        -------
        bool
            True if any frame has motion-related semantics or opposition.
        """
        for frame in self.gl_frames:
            # Check opposition type
            if frame.opposition and frame.opposition.type == "motion":
                return True
            # Check event types
            if frame.event_structure:
                for event in frame.event_structure.events:
                    if event.type in ["process", "transition"] and (
                        "Source" in event.participants or "Goal" in event.participants
                    ):
                        return True
        return False

    def is_change_of_possession_class(self) -> bool:
        """Check if this involves possession transfer.

        Returns
        -------
        bool
            True if frames involve possession transfer.
        """
        for frame in self.gl_frames:
            if frame.opposition and frame.opposition.type == "possession_transfer":
                return True
            # Check for possession-related roles
            if frame.subcat:
                roles = {m.role for m in frame.subcat.members}
                if "Recipient" in roles or "Beneficiary" in roles:
                    return True
        return False

    def is_change_of_info_class(self) -> bool:
        """Check if this involves information transfer.

        Returns
        -------
        bool
            True if frames involve information transfer.
        """
        for frame in self.gl_frames:
            if frame.opposition and frame.opposition.type == "info_transfer":
                return True
            # Check qualia for communication-related telic
            if (
                frame.qualia
                and frame.qualia.telic
                and (
                    "communicate" in frame.qualia.telic.lower()
                    or "inform" in frame.qualia.telic.lower()
                )
            ):
                return True
        return False
