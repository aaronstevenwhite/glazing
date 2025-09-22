"""WordNet search functionality.

This module provides search capabilities for WordNet data,
including synset searches by lemma, offset, sense key, and pattern-based
searches with domain-specific filtering.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from glazing.wordnet.models import Sense, Synset
from glazing.wordnet.types import (
    LexFileName,
    SenseKey,
    SynsetOffset,
    WordNetPOS,
)


class WordNetSearch:
    """Search interface for WordNet data.

    Provides methods for finding synsets by various criteria
    including lemma, offset, sense key, pattern matching, and
    domain-specific searches.

    Parameters
    ----------
    synsets : list[Synset] | None
        Initial synsets to index. If None, creates empty search.
    senses : list[Sense] | None
        Initial senses to index. If None, creates empty search.

    Attributes
    ----------
    _synsets : dict[SynsetOffset, Synset]
        Mapping from synset offset to synset object.
    _synsets_by_lemma : dict[str, dict[WordNetPOS, set[SynsetOffset]]]
        Mapping from lemma and POS to synset offsets.
    _senses : dict[SenseKey, Sense]
        Mapping from sense key to sense object.
    _synsets_by_domain : dict[LexFileName, set[SynsetOffset]]
        Mapping from lexical file name to synset offsets.

    Methods
    -------
    add_synset(synset)
        Add a synset to the search index.
    add_sense(sense)
        Add a sense to the search index.
    by_offset(offset, pos)
        Find synset by offset and POS.
    by_lemma(lemma, pos)
        Find synsets containing a lemma.
    by_sense_key(sense_key)
        Find synset by sense key.
    by_pattern(pattern, pos, case_sensitive)
        Find synsets matching a pattern.
    by_domain(domain)
        Find synsets in a specific domain.
    by_gloss_pattern(pattern, pos, case_sensitive)
        Find synsets with glosses matching a pattern.
    get_lemma_senses(lemma, pos)
        Get all senses for a lemma.

    Examples
    --------
    >>> search = WordNetSearch()
    >>> search.add_synset(dog_synset)
    >>> synsets = search.by_lemma("dog", "n")
    >>> synset = search.by_offset("02084442", "n")
    """

    def __init__(
        self, synsets: list[Synset] | None = None, senses: list[Sense] | None = None
    ) -> None:
        """Initialize WordNet search with optional initial data."""
        self._synsets: dict[SynsetOffset, Synset] = {}
        self._synsets_by_lemma: dict[str, dict[WordNetPOS, set[SynsetOffset]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._senses: dict[SenseKey, Sense] = {}
        self._synsets_by_domain: dict[LexFileName, set[SynsetOffset]] = defaultdict(set)
        self._synsets_by_pos: dict[WordNetPOS, set[SynsetOffset]] = defaultdict(set)

        if synsets:
            for synset in synsets:
                self.add_synset(synset)

        if senses:
            for sense in senses:
                self.add_sense(sense)

    def add_synset(self, synset: Synset) -> None:
        """Add a synset to the search index.

        Parameters
        ----------
        synset : Synset
            Synset to add to index.

        Raises
        ------
        ValueError
            If synset with same offset already exists.
        """
        if synset.offset in self._synsets:
            msg = f"Synset with offset {synset.offset} already exists"
            raise ValueError(msg)

        self._synsets[synset.offset] = synset
        self._synsets_by_pos[synset.ss_type].add(synset.offset)

        # Index by lemma
        for word in synset.words:
            self._synsets_by_lemma[word.lemma][synset.ss_type].add(synset.offset)

        # Index by domain (lexical file)
        self._synsets_by_domain[synset.lex_filename].add(synset.offset)

    def add_sense(self, sense: Sense) -> None:
        """Add a sense to the search index.

        Parameters
        ----------
        sense : Sense
            Sense to add to index.

        Raises
        ------
        ValueError
            If sense with same key already exists.
        """
        if sense.sense_key in self._senses:
            msg = f"Sense with key {sense.sense_key} already exists"
            raise ValueError(msg)

        self._senses[sense.sense_key] = sense

    def by_offset(self, offset: SynsetOffset, pos: WordNetPOS | None = None) -> Synset | None:
        """Find synset by offset and optionally POS.

        Parameters
        ----------
        offset : SynsetOffset
            Synset offset (8-digit string).
        pos : WordNetPOS | None
            Part of speech to filter by.

        Returns
        -------
        Synset | None
            Synset if found, None otherwise.
        """
        synset = self._synsets.get(offset)
        if synset and pos is not None and synset.ss_type != pos:
            return None
        return synset

    def by_lemma(self, lemma: str, pos: WordNetPOS | None = None) -> list[Synset]:
        """Find synsets containing a lemma.

        Parameters
        ----------
        lemma : str
            Lemma to search for (lowercase, underscores for spaces).
        pos : WordNetPOS | None
            Part of speech to filter by.

        Returns
        -------
        list[Synset]
            Synsets containing the lemma.
        """
        # Normalize lemma
        lemma = lemma.lower().replace(" ", "_")

        synsets = []
        if pos is not None:
            # Search specific POS
            offsets = self._synsets_by_lemma.get(lemma, {}).get(pos, set())
            synsets = [self._synsets[offset] for offset in offsets]
        else:
            # Search all POS
            for pos_offsets in self._synsets_by_lemma.get(lemma, {}).values():
                synsets.extend([self._synsets[offset] for offset in pos_offsets])

        return sorted(synsets, key=lambda s: s.offset)

    def by_sense_key(self, sense_key: SenseKey) -> Synset | None:
        """Find synset by sense key.

        Parameters
        ----------
        sense_key : SenseKey
            Sense key to look up.

        Returns
        -------
        Synset | None
            Synset containing the sense, None if not found.
        """
        sense = self._senses.get(sense_key)
        if sense:
            return self._synsets.get(sense.synset_offset)
        return None

    def by_pattern(
        self, pattern: str, pos: WordNetPOS | None = None, case_sensitive: bool = False
    ) -> list[Synset]:
        """Find synsets matching a pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against lemmas.
        pos : WordNetPOS | None
            Part of speech to filter by.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[Synset]
            Synsets with lemmas matching the pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_offsets = set()

        # Determine which synsets to search
        if pos is not None:
            synsets_to_search = [self._synsets[offset] for offset in self._synsets_by_pos[pos]]
        else:
            synsets_to_search = list(self._synsets.values())

        for synset in synsets_to_search:
            for word in synset.words:
                if regex.search(word.lemma):
                    matching_offsets.add(synset.offset)
                    break

        synsets = [self._synsets[offset] for offset in matching_offsets]
        return sorted(synsets, key=lambda s: s.offset)

    def by_domain(self, domain: LexFileName) -> list[Synset]:
        """Find synsets in a specific domain.

        Parameters
        ----------
        domain : LexFileName
            Lexical file name (domain).

        Returns
        -------
        list[Synset]
            Synsets in the specified domain.
        """
        offsets = self._synsets_by_domain.get(domain, set())
        synsets = [self._synsets[offset] for offset in offsets]
        return sorted(synsets, key=lambda s: s.offset)

    def by_gloss_pattern(
        self, pattern: str, pos: WordNetPOS | None = None, case_sensitive: bool = False
    ) -> list[Synset]:
        """Find synsets with glosses matching a pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against glosses.
        pos : WordNetPOS | None
            Part of speech to filter by.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[Synset]
            Synsets with glosses matching the pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_synsets = []

        # Determine which synsets to search
        if pos is not None:
            synsets_to_search = [self._synsets[offset] for offset in self._synsets_by_pos[pos]]
        else:
            synsets_to_search = list(self._synsets.values())

        for synset in synsets_to_search:
            if regex.search(synset.gloss):
                matching_synsets.append(synset)

        return sorted(matching_synsets, key=lambda s: s.offset)

    def get_lemma_senses(self, lemma: str, pos: WordNetPOS | None = None) -> list[Sense]:
        """Get all senses for a lemma.

        Parameters
        ----------
        lemma : str
            Lemma to get senses for.
        pos : WordNetPOS | None
            Part of speech to filter by.

        Returns
        -------
        list[Sense]
            Senses for the lemma, ordered by sense number.
        """
        # Normalize lemma
        lemma = lemma.lower().replace(" ", "_")

        matching_senses = []
        for sense in self._senses.values():
            if sense.lemma == lemma and (pos is None or sense.ss_type == pos):
                matching_senses.append(sense)

        return sorted(matching_senses, key=lambda s: s.sense_number)

    def get_all_lemmas(self, pos: WordNetPOS | None = None) -> list[str]:
        """Get all unique lemmas.

        Parameters
        ----------
        pos : WordNetPOS | None
            Part of speech to filter by.

        Returns
        -------
        list[str]
            Sorted list of unique lemmas.
        """
        if pos is not None:
            lemmas = set()
            for lemma, pos_dict in self._synsets_by_lemma.items():
                if pos in pos_dict:
                    lemmas.add(lemma)
            return sorted(lemmas)
        return sorted(self._synsets_by_lemma.keys())

    def get_all_domains(self) -> list[LexFileName]:
        """Get all lexical file names (domains).

        Returns
        -------
        list[LexFileName]
            Sorted list of domains.
        """
        return sorted(self._synsets_by_domain.keys())

    def get_all_synsets(self) -> list[Synset]:
        """Get all synsets in the search index.

        Returns
        -------
        list[Synset]
            All synsets sorted by offset.
        """
        return sorted(self._synsets.values(), key=lambda s: s.offset)

    def get_synset_by_id(self, synset_id: str) -> Synset | None:
        """Get a synset by its ID string.

        Parameters
        ----------
        synset_id : str
            Synset ID in format "offsetpos" (e.g., "01234567n").

        Returns
        -------
        Synset | None
            The synset if found, None otherwise.
        """
        if len(synset_id) == 9 and synset_id[:-1].isdigit() and synset_id[-1] in "nvasr":
            offset = synset_id[:-1]
            pos = synset_id[-1]
            return self.by_offset(offset, pos)  # type: ignore[arg-type]
        return None

    def get_statistics(self) -> dict[str, int]:
        """Get search index statistics.

        Returns
        -------
        dict[str, int]
            Statistics about indexed data.
        """
        total_words = sum(len(s.words) for s in self._synsets.values())

        total_lemmas = len(self._synsets_by_lemma)

        # Count synsets by POS
        pos_counts = {pos: len(offsets) for pos, offsets in self._synsets_by_pos.items()}

        return {
            "synset_count": len(self._synsets),
            "sense_count": len(self._senses),
            "unique_lemmas": total_lemmas,
            "total_words": total_words,
            "domain_count": len(self._synsets_by_domain),
            **{f"{pos}_synsets": count for pos, count in pos_counts.items()},
        }

    @classmethod
    def from_jsonl_files(
        cls, synsets_path: Path | str | None = None, senses_path: Path | str | None = None
    ) -> WordNetSearch:
        """Load search index from JSON Lines files.

        Parameters
        ----------
        synsets_path : Path | str | None
            Path to JSON Lines file containing synsets.
        senses_path : Path | str | None
            Path to JSON Lines file containing senses.

        Returns
        -------
        WordNetSearch
            Search index populated with data from files.

        Raises
        ------
        FileNotFoundError
            If specified file does not exist.
        ValueError
            If file contains invalid data.
        """
        synsets = []
        senses = []

        if synsets_path:
            synsets_path = Path(synsets_path)
            if not synsets_path.exists():
                msg = f"Synsets file not found: {synsets_path}"
                raise FileNotFoundError(msg)

            with synsets_path.open(encoding="utf-8") as f:
                for line_raw in f:
                    line = line_raw.strip()
                    if line:
                        synset = Synset.model_validate_json(line)
                        synsets.append(synset)

        if senses_path:
            senses_path = Path(senses_path)
            if not senses_path.exists():
                msg = f"Senses file not found: {senses_path}"
                raise FileNotFoundError(msg)

            with senses_path.open(encoding="utf-8") as f:
                for line_raw in f:
                    line = line_raw.strip()
                    if line:
                        sense = Sense.model_validate_json(line)
                        senses.append(sense)

        return cls(synsets=synsets, senses=senses)
