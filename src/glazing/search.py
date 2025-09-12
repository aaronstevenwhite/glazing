"""Unified search interface for all linguistic datasets.

This module provides a unified interface for searching across
FrameNet, VerbNet, WordNet, and PropBank data simultaneously.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from glazing.framenet.models import Frame
from glazing.framenet.search import FrameNetSearch
from glazing.propbank.models import Frameset, Roleset
from glazing.propbank.search import PropBankSearch
from glazing.types import ResourceType
from glazing.verbnet.models import VerbClass
from glazing.verbnet.search import VerbNetSearch
from glazing.verbnet.types import PredicateType
from glazing.wordnet.models import Synset
from glazing.wordnet.search import WordNetSearch


@dataclass
class UnifiedSearchResult:
    """Container for search results across all datasets.

    Parameters
    ----------
    frames : list[Frame]
        FrameNet frames found.
    verb_classes : list[VerbClass]
        VerbNet verb classes found.
    synsets : list[Synset]
        WordNet synsets found.
    framesets : list[Frameset]
        PropBank framesets found.
    rolesets : list[Roleset]
        PropBank rolesets found.

    Examples
    --------
    >>> result = UnifiedSearchResult(
    ...     frames=[giving_frame],
    ...     verb_classes=[give_class],
    ...     synsets=[give_synset],
    ...     framesets=[give_frameset],
    ...     rolesets=[]
    ... )
    """

    frames: list[Frame]
    verb_classes: list[VerbClass]
    synsets: list[Synset]
    framesets: list[Frameset]
    rolesets: list[Roleset]

    def is_empty(self) -> bool:
        """Check if all result lists are empty.

        Returns
        -------
        bool
            True if no results found in any dataset.
        """
        return not any(
            [
                self.frames,
                self.verb_classes,
                self.synsets,
                self.framesets,
                self.rolesets,
            ]
        )

    def count(self) -> int:
        """Get total count of all results.

        Returns
        -------
        int
            Total number of results across all datasets.
        """
        return (
            len(self.frames)
            + len(self.verb_classes)
            + len(self.synsets)
            + len(self.framesets)
            + len(self.rolesets)
        )


class UnifiedSearch:
    """Unified search interface across all linguistic datasets.

    Provides methods for searching FrameNet, VerbNet, WordNet,
    and PropBank simultaneously or individually.

    Parameters
    ----------
    framenet : FrameNetSearch | None
        FrameNet search index.
    verbnet : VerbNetSearch | None
        VerbNet search index.
    wordnet : WordNetSearch | None
        WordNet search index.
    propbank : PropBankSearch | None
        PropBank search index.

    Attributes
    ----------
    framenet : FrameNetSearch | None
        FrameNet search interface.
    verbnet : VerbNetSearch | None
        VerbNet search interface.
    wordnet : WordNetSearch | None
        WordNet search interface.
    propbank : PropBankSearch | None
        PropBank search interface.

    Methods
    -------
    by_lemma(lemma, pos)
        Search all datasets by lemma.
    by_semantic_role(role_name)
        Search for frames/classes with a semantic role.
    by_semantic_predicate(predicate)
        Search for verb classes with a semantic predicate.
    by_domain(domain)
        Search within a specific domain.
    get_statistics()
        Get statistics across all datasets.

    Examples
    --------
    >>> search = UnifiedSearch(
    ...     framenet=FrameNetSearch(frames),
    ...     verbnet=VerbNetSearch(classes),
    ...     wordnet=WordNetSearch(synsets),
    ...     propbank=PropBankSearch(framesets)
    ... )
    >>> results = search.by_lemma("give")
    """

    def __init__(
        self,
        framenet: FrameNetSearch | None = None,
        verbnet: VerbNetSearch | None = None,
        wordnet: WordNetSearch | None = None,
        propbank: PropBankSearch | None = None,
    ) -> None:
        """Initialize unified search with optional dataset indices."""
        self.framenet = framenet
        self.verbnet = verbnet
        self.wordnet = wordnet
        self.propbank = propbank

    def by_lemma(self, lemma: str, pos: str | None = None) -> UnifiedSearchResult:  # noqa: C901, PLR0912
        """Search all datasets by lemma.

        Parameters
        ----------
        lemma : str
            Lemma to search for.
        pos : str | None
            Part of speech constraint (format varies by dataset).

        Returns
        -------
        UnifiedSearchResult
            Results from all datasets.
        """
        frames = []
        verb_classes = []
        synsets = []
        framesets = []
        rolesets = []

        # Search FrameNet
        if self.framenet:
            # Convert POS if provided
            fn_pos = None
            if pos:
                pos_lower = pos.lower()
                if pos_lower in ["v", "verb"]:
                    fn_pos = "V"
                elif pos_lower in ["n", "noun"]:
                    fn_pos = "N"
                elif pos_lower in ["a", "adj", "adjective"]:
                    fn_pos = "A"
            frames = self.framenet.find_frames_by_lemma(lemma, fn_pos)  # type: ignore[arg-type]

        # Search VerbNet
        if self.verbnet:
            verb_classes = self.verbnet.by_members([lemma])

        # Search WordNet
        if self.wordnet:
            # Convert POS if provided
            wn_pos = None
            if pos:
                pos_lower = pos.lower()
                if pos_lower in ["v", "verb"]:
                    wn_pos = "v"
                elif pos_lower in ["n", "noun"]:
                    wn_pos = "n"
                elif pos_lower in ["a", "adj", "adjective", "s"]:
                    wn_pos = "a"
                elif pos_lower in ["r", "adv", "adverb"]:
                    wn_pos = "r"
            synsets = self.wordnet.by_lemma(lemma, wn_pos)  # type: ignore[arg-type]

        # Search PropBank
        if self.propbank:
            frameset = self.propbank.by_lemma(lemma)
            if frameset:
                framesets = [frameset]
                rolesets = frameset.rolesets

        return UnifiedSearchResult(
            frames=frames,
            verb_classes=verb_classes,
            synsets=synsets,
            framesets=framesets,
            rolesets=rolesets,
        )

    def by_semantic_role(self, role_name: str) -> UnifiedSearchResult:
        """Search for frames/classes with a semantic role.

        Parameters
        ----------
        role_name : str
            Name of semantic role (e.g., "Agent", "Theme").

        Returns
        -------
        UnifiedSearchResult
            Results from datasets that have this role.
        """
        frames = []
        verb_classes = []

        # Search FrameNet for frames with this FE
        if self.framenet:
            frames = self.framenet.find_frames_with_fe(role_name)

        # Search VerbNet for classes with this thematic role
        if self.verbnet:
            verb_classes = self.verbnet.by_themroles([role_name])  # type: ignore[list-item]

        # PropBank uses numbered arguments, not named roles
        # WordNet doesn't have semantic roles

        return UnifiedSearchResult(
            frames=frames,
            verb_classes=verb_classes,
            synsets=[],
            framesets=[],
            rolesets=[],
        )

    def by_semantic_predicate(self, predicate: PredicateType) -> UnifiedSearchResult:
        """Search for verb classes with a semantic predicate.

        Parameters
        ----------
        predicate : PredicateType
            Semantic predicate to search for.

        Returns
        -------
        UnifiedSearchResult
            Results from VerbNet.
        """
        verb_classes = []

        # Only VerbNet has semantic predicates
        if self.verbnet:
            verb_classes = self.verbnet.by_predicate(predicate)

        return UnifiedSearchResult(
            frames=[],
            verb_classes=verb_classes,
            synsets=[],
            framesets=[],
            rolesets=[],
        )

    def by_domain(self, domain: str) -> UnifiedSearchResult:
        """Search within a specific domain.

        Parameters
        ----------
        domain : str
            Domain name (WordNet lexical file name).

        Returns
        -------
        UnifiedSearchResult
            Results from datasets that support domain search.
        """
        synsets = []

        # Only WordNet has explicit domains (lexical files)
        if self.wordnet:
            synsets = self.wordnet.by_domain(domain)  # type: ignore[arg-type]

        return UnifiedSearchResult(
            frames=[],
            verb_classes=[],
            synsets=synsets,
            framesets=[],
            rolesets=[],
        )

    def by_external_resource(
        self, resource_type: ResourceType, class_name: str | None = None
    ) -> UnifiedSearchResult:
        """Search for entries linked to external resources.

        Parameters
        ----------
        resource_type : ResourceType
            Type of resource (e.g., "VerbNet", "FrameNet").
        class_name : str | None
            Specific class/frame name to match.

        Returns
        -------
        UnifiedSearchResult
            Results from datasets with links to the resource.
        """
        rolesets = []

        # PropBank has external resource links
        if self.propbank:
            rolesets = self.propbank.by_resource(resource_type, class_name)

        return UnifiedSearchResult(
            frames=[],
            verb_classes=[],
            synsets=[],
            framesets=[],
            rolesets=rolesets,
        )

    def get_statistics(self) -> dict[str, dict[str, int]]:
        """Get statistics across all datasets.

        Returns
        -------
        dict[str, dict[str, int]]
            Statistics for each available dataset.
        """
        stats = {}

        if self.framenet:
            stats["framenet"] = self.framenet.get_statistics()

        if self.verbnet:
            stats["verbnet"] = self.verbnet.get_statistics()

        if self.wordnet:
            stats["wordnet"] = self.wordnet.get_statistics()

        if self.propbank:
            stats["propbank"] = self.propbank.get_statistics()

        return stats

    @classmethod
    def from_paths(
        cls,
        framenet_path: Path | str | None = None,
        verbnet_path: Path | str | None = None,
        wordnet_synsets_path: Path | str | None = None,
        wordnet_senses_path: Path | str | None = None,
        propbank_path: Path | str | None = None,
    ) -> UnifiedSearch:
        """Load unified search from JSON Lines files.

        Parameters
        ----------
        framenet_path : Path | str | None
            Path to FrameNet JSONL file.
        verbnet_path : Path | str | None
            Path to VerbNet JSONL file.
        wordnet_synsets_path : Path | str | None
            Path to WordNet synsets JSONL file.
        wordnet_senses_path : Path | str | None
            Path to WordNet senses JSONL file.
        propbank_path : Path | str | None
            Path to PropBank JSONL file.

        Returns
        -------
        UnifiedSearch
            Unified search with loaded datasets.
        """
        framenet = None
        if framenet_path:
            framenet = FrameNetSearch.from_jsonl_file(framenet_path)

        verbnet = None
        if verbnet_path:
            verbnet = VerbNetSearch.from_jsonl_file(verbnet_path)

        wordnet = None
        if wordnet_synsets_path or wordnet_senses_path:
            wordnet = WordNetSearch.from_jsonl_files(
                synsets_path=wordnet_synsets_path,
                senses_path=wordnet_senses_path,
            )

        propbank = None
        if propbank_path:
            propbank = PropBankSearch.from_jsonl_file(propbank_path)

        return cls(
            framenet=framenet,
            verbnet=verbnet,
            wordnet=wordnet,
            propbank=propbank,
        )
