"""Tests for VerbNet Generative Lexicon models.

Tests the GLVerbClass, GLFrame, EventStructure, Qualia, and related models
for proper validation, serialization, and functionality.
"""

from __future__ import annotations

from glazing.verbnet.gl_models import (
    Event,
    EventStructure,
    GLFrame,
    GLVerbClass,
    Opposition,
    Qualia,
    State,
    Subcategorization,
    SubcatMember,
    Subevent,
)
from glazing.verbnet.models import (
    Example,
    FrameDescription,
    Predicate,
    PredicateArgument,
    Semantics,
    Syntax,
    SyntaxElement,
    VerbClass,
    VNFrame,
)


class TestState:
    """Test the State model."""

    def test_basic_state(self) -> None:
        """Test creating a basic state."""
        state = State(predicate="at_location", args=["x", "y"])
        assert state.predicate == "at_location"
        assert state.args == ["x", "y"]
        assert not state.negated

    def test_negated_state(self) -> None:
        """Test creating a negated state."""
        state = State(predicate="has_possession", args=["agent", "theme"], negated=True)
        assert state.negated

    def test_empty_args(self) -> None:
        """Test state with no arguments."""
        state = State(predicate="exists", args=[])
        assert state.args == []


class TestOpposition:
    """Test the Opposition model."""

    def test_motion_opposition(self) -> None:
        """Test creating a motion opposition."""
        opposition = Opposition(
            type="motion",
            initial_state=State(predicate="at_location", args=["x", "source"]),
            final_state=State(predicate="at_location", args=["x", "goal"]),
        )
        assert opposition.type == "motion"
        assert opposition.initial_state.args[1] == "source"
        assert opposition.final_state.args[1] == "goal"

    def test_state_change_opposition(self) -> None:
        """Test state change opposition."""
        opposition = Opposition(
            type="state_change",
            initial_state=State(predicate="closed", args=["door"], negated=True),
            final_state=State(predicate="closed", args=["door"], negated=False),
        )
        assert opposition.type == "state_change"
        assert opposition.initial_state.negated
        assert not opposition.final_state.negated


class TestEvent:
    """Test the Event model."""

    def test_process_event(self) -> None:
        """Test creating a process event."""
        event = Event(id="e1", type="process", participants={"Agent": "x", "Theme": "y"})
        assert event.id == "e1"
        assert event.type == "process"
        assert event.participants["Agent"] == "x"

    def test_state_event(self) -> None:
        """Test creating a state event."""
        event = Event(id="e2", type="state", participants={"Theme": "x"})
        assert event.type == "state"

    def test_transition_event(self) -> None:
        """Test creating a transition event."""
        event = Event(id="e3", type="transition", participants={"Patient": "x", "Result": "state"})
        assert event.type == "transition"

    def test_empty_participants(self) -> None:
        """Test event with no participants."""
        event = Event(id="e1", type="process", participants={})
        assert event.participants == {}


class TestSubevent:
    """Test the Subevent model."""

    def test_basic_subevent(self) -> None:
        """Test creating a basic subevent."""
        subevent = Subevent(
            id="e1.1",
            parent_event="e1",
            relation="starts",
            predicate="motion",
            args=["x", "source", "goal"],
        )
        assert subevent.id == "e1.1"
        assert subevent.parent_event == "e1"
        assert subevent.relation == "starts"
        assert len(subevent.args) == 3

    def test_culmination_subevent(self) -> None:
        """Test culmination relation."""
        subevent = Subevent(
            id="e2.2",
            parent_event="e2",
            relation="culminates",
            predicate="arrive",
            args=["x", "goal"],
        )
        assert subevent.relation == "culminates"

    def test_result_subevent(self) -> None:
        """Test result relation."""
        subevent = Subevent(
            id="e3.3", parent_event="e3", relation="results", predicate="broken", args=["y"]
        )
        assert subevent.relation == "results"


class TestEventStructure:
    """Test the EventStructure model."""

    def test_simple_event_structure(self) -> None:
        """Test simple event structure with single event."""
        structure = EventStructure(
            events=[Event(id="e1", type="process", participants={"Agent": "x"})]
        )
        assert len(structure.events) == 1
        assert structure.subevents == []

    def test_complex_event_structure(self) -> None:
        """Test complex event structure with subevents."""
        structure = EventStructure(
            events=[
                Event(id="e1", type="process", participants={"Agent": "x", "Theme": "y"}),
                Event(id="e2", type="state", participants={"Theme": "y"}),
            ],
            subevents=[
                Subevent(
                    id="e1.1",
                    parent_event="e1",
                    relation="starts",
                    predicate="grasp",
                    args=["x", "y"],
                ),
                Subevent(
                    id="e1.2",
                    parent_event="e1",
                    relation="culminates",
                    predicate="hold",
                    args=["x", "y"],
                ),
            ],
        )
        assert len(structure.events) == 2
        assert len(structure.subevents) == 2


class TestQualia:
    """Test the Qualia model."""

    def test_full_qualia(self) -> None:
        """Test qualia with all fields."""
        qualia = Qualia(
            formal="object", constitutive="material", telic="transport", agentive="manufacture"
        )
        assert qualia.formal == "object"
        assert qualia.constitutive == "material"
        assert qualia.telic == "transport"
        assert qualia.agentive == "manufacture"

    def test_partial_qualia(self) -> None:
        """Test qualia with some fields."""
        qualia = Qualia(formal="event", telic="communicate")
        assert qualia.formal == "event"
        assert qualia.telic == "communicate"
        assert qualia.constitutive is None
        assert qualia.agentive is None

    def test_empty_qualia(self) -> None:
        """Test qualia with no fields set."""
        qualia = Qualia()
        assert qualia.formal is None
        assert qualia.constitutive is None
        assert qualia.telic is None
        assert qualia.agentive is None


class TestSubcatMember:
    """Test the SubcatMember model."""

    def test_np_member(self) -> None:
        """Test NP subcategorization member."""
        member = SubcatMember(role="Agent", variable="x", pos="NP")
        assert member.role == "Agent"
        assert member.variable == "x"
        assert member.pos == "NP"
        assert member.prep is None

    def test_pp_member(self) -> None:
        """Test PP subcategorization member."""
        member = SubcatMember(role="Goal", variable="z", pos="PP", prep="to")
        assert member.pos == "PP"
        assert member.prep == "to"


class TestSubcategorization:
    """Test the Subcategorization model."""

    def test_transitive_subcat(self) -> None:
        """Test transitive subcategorization."""
        subcat = Subcategorization(
            members=[
                SubcatMember(role="Agent", variable="x", pos="NP"),
                SubcatMember(role="Theme", variable="y", pos="NP"),
            ]
        )
        assert len(subcat.members) == 2
        assert subcat.members[0].role == "Agent"
        assert subcat.members[1].role == "Theme"

    def test_ditransitive_subcat(self) -> None:
        """Test ditransitive subcategorization."""
        subcat = Subcategorization(
            members=[
                SubcatMember(role="Agent", variable="x", pos="NP"),
                SubcatMember(role="Theme", variable="y", pos="NP"),
                SubcatMember(role="Recipient", variable="z", pos="PP", prep="to"),
            ]
        )
        assert len(subcat.members) == 3
        assert subcat.members[2].prep == "to"

    def test_empty_subcat(self) -> None:
        """Test empty subcategorization."""
        subcat = Subcategorization(members=[])
        assert subcat.members == []


class TestGLFrame:
    """Test the GLFrame model."""

    def test_basic_gl_frame(self) -> None:
        """Test creating a basic GL frame."""
        vn_frame = VNFrame(
            description=FrameDescription(
                description_number="0.1", primary="NP V NP", secondary="Transitive"
            ),
            examples=[Example(text="John hit the ball")],
            syntax=Syntax(
                elements=[
                    SyntaxElement(pos="NP", value="Agent"),
                    SyntaxElement(pos="VERB"),
                    SyntaxElement(pos="NP", value="Theme"),
                ]
            ),
            semantics=Semantics(
                predicates=[
                    Predicate(value="cause", args=[PredicateArgument(type="Event", value="e1")])
                ]
            ),
        )

        gl_frame = GLFrame(
            vn_frame=vn_frame,
            subcat=Subcategorization(
                members=[
                    SubcatMember(role="Agent", variable="x", pos="NP"),
                    SubcatMember(role="Theme", variable="y", pos="NP"),
                ]
            ),
            event_structure=EventStructure(
                events=[Event(id="e1", type="process", participants={"Agent": "x"})]
            ),
        )

        assert gl_frame.vn_frame == vn_frame
        assert len(gl_frame.subcat.members) == 2
        assert gl_frame.qualia is None
        assert gl_frame.opposition is None

    def test_gl_frame_with_all_features(self) -> None:
        """Test GL frame with all features."""
        vn_frame = VNFrame(
            description=FrameDescription(
                description_number="1.0", primary="NP V PP", secondary="Motion"
            ),
            examples=[],
            syntax=Syntax(elements=[]),
            semantics=Semantics(predicates=[]),
        )

        gl_frame = GLFrame(
            vn_frame=vn_frame,
            subcat=Subcategorization(
                members=[
                    SubcatMember(role="Theme", variable="x", pos="NP"),
                    SubcatMember(role="Goal", variable="y", pos="PP", prep="to"),
                ]
            ),
            qualia=Qualia(formal="event", telic="motion"),
            event_structure=EventStructure(
                events=[Event(id="e1", type="transition", participants={"Theme": "x"})],
                subevents=[
                    Subevent(
                        id="e1.1",
                        parent_event="e1",
                        relation="starts",
                        predicate="move",
                        args=["x"],
                    )
                ],
            ),
            opposition=Opposition(
                type="motion",
                initial_state=State(predicate="at", args=["x", "source"]),
                final_state=State(predicate="at", args=["x", "y"]),
            ),
        )

        assert gl_frame.qualia is not None
        assert gl_frame.opposition is not None
        assert gl_frame.opposition.type == "motion"


class TestGLVerbClass:
    """Test the GLVerbClass model."""

    def test_basic_gl_class(self) -> None:
        """Test creating a basic GL verb class."""
        verb_class = VerbClass(id="move-51.3", members=[], themroles=[], frames=[], subclasses=[])

        gl_class = GLVerbClass(verb_class=verb_class, gl_frames=[])

        assert gl_class.verb_class == verb_class
        assert gl_class.gl_frames == []

    def test_is_motion_class(self) -> None:
        """Test motion class detection."""
        verb_class = VerbClass(id="move-51.3", members=[], themroles=[], frames=[], subclasses=[])

        # Create frame with motion opposition
        vn_frame = VNFrame(
            description=FrameDescription(
                description_number="0.1", primary="NP V PP", secondary="Motion"
            ),
            examples=[],
            syntax=Syntax(elements=[]),
            semantics=Semantics(predicates=[]),
        )

        gl_frame = GLFrame(
            vn_frame=vn_frame,
            subcat=Subcategorization(members=[]),
            event_structure=EventStructure(events=[]),
            opposition=Opposition(
                type="motion",
                initial_state=State(predicate="at", args=["x", "source"]),
                final_state=State(predicate="at", args=["x", "goal"]),
            ),
        )

        gl_class = GLVerbClass(verb_class=verb_class, gl_frames=[gl_frame])

        assert gl_class.is_motion_class()

    def test_is_change_of_possession_class(self) -> None:
        """Test possession transfer class detection."""
        verb_class = VerbClass(id="give-13.1", members=[], themroles=[], frames=[], subclasses=[])

        vn_frame = VNFrame(
            description=FrameDescription(
                description_number="0.1", primary="NP V NP NP", secondary="Ditransitive"
            ),
            examples=[],
            syntax=Syntax(elements=[]),
            semantics=Semantics(predicates=[]),
        )

        gl_frame = GLFrame(
            vn_frame=vn_frame,
            subcat=Subcategorization(
                members=[
                    SubcatMember(role="Agent", variable="x", pos="NP"),
                    SubcatMember(role="Theme", variable="y", pos="NP"),
                    SubcatMember(role="Recipient", variable="z", pos="NP"),
                ]
            ),
            event_structure=EventStructure(events=[]),
            opposition=Opposition(
                type="possession_transfer",
                initial_state=State(predicate="has", args=["x", "y"]),
                final_state=State(predicate="has", args=["z", "y"]),
            ),
        )

        gl_class = GLVerbClass(verb_class=verb_class, gl_frames=[gl_frame])

        assert gl_class.is_change_of_possession_class()

    def test_is_change_of_info_class(self) -> None:
        """Test information transfer class detection."""
        verb_class = VerbClass(id="tell-37.2", members=[], themroles=[], frames=[], subclasses=[])

        vn_frame = VNFrame(
            description=FrameDescription(
                description_number="0.1", primary="NP V NP S", secondary="Communication"
            ),
            examples=[],
            syntax=Syntax(elements=[]),
            semantics=Semantics(predicates=[]),
        )

        gl_frame = GLFrame(
            vn_frame=vn_frame,
            subcat=Subcategorization(members=[]),
            qualia=Qualia(telic="communicate information"),
            event_structure=EventStructure(events=[]),
        )

        gl_class = GLVerbClass(verb_class=verb_class, gl_frames=[gl_frame])

        assert gl_class.is_change_of_info_class()

    def test_multiple_detection_methods(self) -> None:
        """Test that multiple detection methods work correctly."""
        verb_class = VerbClass(id="run-51.3", members=[], themroles=[], frames=[], subclasses=[])

        vn_frame = VNFrame(
            description=FrameDescription(
                description_number="0.1", primary="NP V", secondary="Intransitive"
            ),
            examples=[],
            syntax=Syntax(elements=[]),
            semantics=Semantics(predicates=[]),
        )

        # Motion frame with Source/Goal participants
        gl_frame = GLFrame(
            vn_frame=vn_frame,
            subcat=Subcategorization(members=[]),
            event_structure=EventStructure(
                events=[
                    Event(
                        id="e1",
                        type="process",
                        participants={"Agent": "x", "Source": "y", "Goal": "z"},
                    )
                ]
            ),
        )

        gl_class = GLVerbClass(verb_class=verb_class, gl_frames=[gl_frame])

        assert gl_class.is_motion_class()
        assert not gl_class.is_change_of_possession_class()
        assert not gl_class.is_change_of_info_class()
