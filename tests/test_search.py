"""Tests for unified search functionality."""

import pytest

from glazing.framenet.models import (
    AnnotatedText,
    Frame,
    FrameElement,
    Lexeme,
    LexicalUnit,
    SentenceCount,
)
from glazing.framenet.search import FrameNetSearch
from glazing.propbank.models import (
    Alias,
    Aliases,
    Frameset,
    LexLink,
    Role,
    Roleset,
)
from glazing.propbank.search import PropBankSearch
from glazing.search import UnifiedSearch, UnifiedSearchResult
from glazing.verbnet.models import (
    Example as VNExample,
)
from glazing.verbnet.models import (
    FrameDescription,
    Member,
    Predicate,
    Semantics,
    Syntax,
    SyntaxElement,
    ThematicRole,
    VerbClass,
    VNFrame,
)
from glazing.verbnet.search import VerbNetSearch
from glazing.wordnet.models import Synset, Word
from glazing.wordnet.search import WordNetSearch


class TestUnifiedSearchResult:
    """Tests for UnifiedSearchResult class."""

    def test_is_empty(self):
        """Test is_empty method."""
        # Empty result
        result = UnifiedSearchResult(
            frames=[],
            verb_classes=[],
            synsets=[],
            framesets=[],
            rolesets=[],
        )
        assert result.is_empty()

        # Non-empty result
        result = UnifiedSearchResult(
            frames=[
                Frame(
                    id=1,
                    name="Test",
                    definition=AnnotatedText(raw_text="test", plain_text="test", annotations=[]),
                    frame_elements=[],
                    lexical_units=[],
                )
            ],
            verb_classes=[],
            synsets=[],
            framesets=[],
            rolesets=[],
        )
        assert not result.is_empty()

    def test_count(self):
        """Test count method."""
        result = UnifiedSearchResult(
            frames=[
                Frame(
                    id=1,
                    name="Test1",
                    definition=AnnotatedText(raw_text="test", plain_text="test", annotations=[]),
                    frame_elements=[],
                    lexical_units=[],
                )
            ],
            verb_classes=[],  # Skip VerbClass for now due to complex validation
            synsets=[
                Synset(
                    offset="00000001",
                    ss_type="n",
                    lex_filename="noun.cognition",
                    lex_filenum=9,
                    words=[Word(lemma="test", lex_id=0)],
                    gloss="A test",
                )
            ],
            framesets=[],
            rolesets=[],
        )
        assert result.count() == 2


class TestUnifiedSearch:
    """Tests for UnifiedSearch class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for all datasets."""
        # FrameNet frame
        giving_frame = Frame(
            id=139,
            name="Giving",
            definition=AnnotatedText(
                raw_text="A Donor transfers a Theme to a Recipient.",
                plain_text="A Donor transfers a Theme to a Recipient.",
                annotations=[],
            ),
            frame_elements=[
                FrameElement(
                    id=2001,
                    name="Donor",
                    abbrev="Don",
                    definition=AnnotatedText(
                        raw_text="The person who gives.",
                        plain_text="The person who gives.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="FF0000",
                    fg_color="FFFFFF",
                ),
                FrameElement(
                    id=2002,
                    name="Theme",
                    abbrev="Thm",
                    definition=AnnotatedText(
                        raw_text="The object given.",
                        plain_text="The object given.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="0000FF",
                    fg_color="FFFFFF",
                ),
            ],
            lexical_units=[
                LexicalUnit(
                    id=20001,
                    name="give.v",
                    pos="V",
                    definition="To transfer possession",
                    frame_id=139,
                    frame_name="Giving",
                    sentence_count=SentenceCount(annotated=20, total=50),
                    lexemes=[Lexeme(name="give", pos="V", headword=True)],
                ),
            ],
        )

        # VerbNet class
        give_class = VerbClass(
            id="give-13.1",
            members=[Member(name="give", verbnet_key="give#1")],
            themroles=[
                ThematicRole(type="Agent"),
                ThematicRole(type="Theme"),
                ThematicRole(type="Recipient"),
            ],
            frames=[
                VNFrame(
                    description=FrameDescription(
                        description_number="0.1",
                        primary="NP V NP NP",
                        secondary="Basic Ditransitive",
                    ),
                    examples=[VNExample(text="John gave Mary a book")],
                    syntax=Syntax(
                        elements=[
                            SyntaxElement(pos="NP", value="Agent"),
                            SyntaxElement(pos="VERB"),
                            SyntaxElement(pos="NP", value="Theme"),
                            SyntaxElement(pos="NP", value="Recipient"),
                        ]
                    ),
                    semantics=Semantics(
                        predicates=[
                            Predicate(
                                value="transfer",
                                args=[
                                    {"type": "Event", "value": "e1"},
                                    {"type": "ThemRole", "value": "Agent"},
                                    {"type": "ThemRole", "value": "Theme"},
                                    {"type": "ThemRole", "value": "Recipient"},
                                ],
                            ),
                        ]
                    ),
                )
            ],
        )

        # WordNet synset
        give_synset = Synset(
            offset="02200686",
            ss_type="v",
            lex_filename="verb.possession",
            lex_filenum=40,
            words=[
                Word(lemma="give", lex_id=0),
                Word(lemma="present", lex_id=0),
            ],
            gloss="transfer possession of something concrete or abstract",
        )

        # PropBank frameset
        give_frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(
                    id="give.01",
                    name="transfer",
                    aliases=Aliases(alias=[Alias(text="give", pos="v")]),
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
                    ],
                ),
            ],
        )

        return {
            "framenet": [giving_frame],
            "verbnet": [give_class],
            "wordnet": [give_synset],
            "propbank": [give_frameset],
        }

    def test_init_empty(self):
        """Test initialization with no datasets."""
        search = UnifiedSearch(auto_load=False)
        assert search.framenet is None
        assert search.verbnet is None
        assert search.wordnet is None
        assert search.propbank is None

    def test_init_with_datasets(self, sample_data):
        """Test initialization with all datasets."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )
        assert search.framenet is not None
        assert search.verbnet is not None
        assert search.wordnet is not None
        assert search.propbank is not None

    def test_by_lemma(self, sample_data):
        """Test searching by lemma across all datasets."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        results = search.by_lemma("give")
        assert len(results.frames) == 1
        assert results.frames[0].name == "Giving"
        assert len(results.verb_classes) == 1
        assert results.verb_classes[0].id == "give-13.1"
        assert len(results.synsets) == 1
        assert results.synsets[0].offset == "02200686"
        assert len(results.framesets) == 1
        assert results.framesets[0].predicate_lemma == "give"
        assert len(results.rolesets) == 1
        assert results.rolesets[0].id == "give.01"

    def test_by_lemma_with_pos(self, sample_data):
        """Test searching by lemma with POS constraint."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        # Search for verb
        results = search.by_lemma("give", pos="v")
        assert len(results.frames) == 1
        assert len(results.synsets) == 1

        # Search for noun (should find nothing in our sample)
        results = search.by_lemma("give", pos="n")
        assert len(results.frames) == 0
        assert len(results.synsets) == 0

    def test_by_semantic_role(self, sample_data):
        """Test searching by semantic role."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        # Search for "Theme"
        results = search.by_semantic_role("Theme")
        assert len(results.frames) == 1  # FrameNet has Theme FE
        assert len(results.verb_classes) == 1  # VerbNet has Theme role
        assert len(results.synsets) == 0  # WordNet doesn't have roles
        assert len(results.framesets) == 0  # PropBank uses numbers

        # Search for "Donor"
        results = search.by_semantic_role("Donor")
        assert len(results.frames) == 1  # FrameNet has Donor FE
        assert len(results.verb_classes) == 0  # VerbNet doesn't have Donor

    def test_by_semantic_predicate(self, sample_data):
        """Test searching by semantic predicate."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        # Only VerbNet has semantic predicates
        results = search.by_semantic_predicate("transfer")
        assert len(results.frames) == 0
        assert len(results.verb_classes) == 1
        assert len(results.synsets) == 0
        assert len(results.framesets) == 0

    def test_by_domain(self, sample_data):
        """Test searching by domain."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        # Only WordNet has domains
        results = search.by_domain("verb.possession")
        assert len(results.frames) == 0
        assert len(results.verb_classes) == 0
        assert len(results.synsets) == 1
        assert len(results.framesets) == 0

    def test_by_external_resource(self, sample_data):
        """Test searching by external resource."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        # PropBank has links to VerbNet
        results = search.by_external_resource("VerbNet", "give-13.1")
        assert len(results.frames) == 0
        assert len(results.verb_classes) == 0
        assert len(results.synsets) == 0
        assert len(results.rolesets) == 1
        assert results.rolesets[0].id == "give.01"

    def test_get_statistics(self, sample_data):
        """Test getting statistics."""
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
            wordnet=WordNetSearch(sample_data["wordnet"]),
            propbank=PropBankSearch(sample_data["propbank"]),
        )

        stats = search.get_statistics()
        assert "framenet" in stats
        assert "verbnet" in stats
        assert "wordnet" in stats
        assert "propbank" in stats

        assert stats["framenet"]["frame_count"] == 1
        assert stats["verbnet"]["class_count"] == 1
        assert stats["wordnet"]["synset_count"] == 1
        assert stats["propbank"]["frameset_count"] == 1

    def test_partial_search(self, sample_data):
        """Test search with only some datasets available."""
        # Only FrameNet and VerbNet
        search = UnifiedSearch(
            framenet=FrameNetSearch(sample_data["framenet"]),
            verbnet=VerbNetSearch(sample_data["verbnet"]),
        )

        results = search.by_lemma("give")
        assert len(results.frames) == 1
        assert len(results.verb_classes) == 1
        assert len(results.synsets) == 0  # WordNet not available
        assert len(results.framesets) == 0  # PropBank not available

        stats = search.get_statistics()
        assert "framenet" in stats
        assert "verbnet" in stats
        assert "wordnet" not in stats
        assert "propbank" not in stats
