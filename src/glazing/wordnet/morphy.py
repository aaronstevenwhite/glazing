"""WordNet morphological processing (morphy).

This module implements WordNet's morphological processing algorithm for
finding base forms (lemmas) of inflected words. It handles both regular
inflections through suffix substitution rules and irregular forms through
exception lists. It also supports collocations and multi-word expressions.

Classes
-------
Morphy
    Morphological processor for finding word base forms.

Functions
---------
morphy
    Find base forms of a word given its POS.

Examples
--------
>>> from glazing.wordnet import Morphy
>>> morphy = Morphy(loader)
>>> lemmas = morphy.morphy("running", "v")
>>> print(lemmas)  # ['run']
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from glazing.wordnet.types import WordNetPOS

if TYPE_CHECKING:
    from glazing.wordnet.loader import WordNetLoader


class Morphy:
    """Morphological processor for finding word base forms.

    This class implements WordNet's morphological processing algorithm,
    which attempts to find the base form (lemma) of inflected words
    through a combination of exception list lookup and suffix substitution
    rules. It also handles collocations and multi-word expressions.

    Parameters
    ----------
    loader : WordNetLoader
        WordNet loader with exception lists and lemma index.

    Attributes
    ----------
    loader : WordNetLoader
        The WordNet loader instance.
    suffix_rules : dict[WordNetPOS, list[tuple[str, str]]]
        Suffix substitution rules by POS.

    Methods
    -------
    morphy(word, pos)
        Find base forms of a word for given POS.
    apply_rules(word, pos)
        Apply morphological rules to generate candidates.
    check_exceptions(word, pos)
        Check exception lists for irregular forms.

    Notes
    -----
    The algorithm follows WordNet's morphy implementation:
    1. Check if the word itself exists in WordNet
    2. Check exception lists for irregular forms
    3. Apply suffix substitution rules
    4. For each candidate, verify it exists in WordNet

    Special cases handled:
    - Multi-word expressions (collocations)
    - Nouns ending with "ful"
    - Verb-preposition collocations
    - Abbreviations with periods
    - Hyphenated words

    Examples
    --------
    >>> morphy = Morphy(loader)
    >>> morphy.morphy("children", "n")
    ['child']
    >>> morphy.morphy("ran", "v")
    ['run']
    >>> morphy.morphy("better", "a")
    ['good', 'well']
    >>> morphy.morphy("attorneys general", "n")
    ['attorney general']
    """

    # Suffix substitution rules by POS
    NOUN_RULES: ClassVar[list[tuple[str, str]]] = [
        ("s", ""),  # dogs -> dog
        ("ses", "s"),  # glasses -> glass
        ("xes", "x"),  # boxes -> box
        ("zes", "z"),  # buzzes -> buzz
        ("ches", "ch"),  # churches -> church
        ("shes", "sh"),  # bushes -> bush
        ("ves", "f"),  # knives -> knife
        ("ves", "fe"),  # wives -> wife
        ("men", "man"),  # men -> man
        ("ies", "y"),  # flies -> fly
    ]

    VERB_RULES: ClassVar[list[tuple[str, str]]] = [
        ("s", ""),  # runs -> run
        ("ies", "y"),  # flies -> fly
        ("es", "e"),  # hopes -> hope
        ("es", ""),  # watches -> watch
        ("ed", "e"),  # hoped -> hope
        ("ed", ""),  # watched -> watch
        ("ing", "e"),  # hoping -> hope
        ("ing", ""),  # watching -> watch
    ]

    ADJ_RULES: ClassVar[list[tuple[str, str]]] = [
        ("er", ""),  # bigger -> big
        ("est", ""),  # biggest -> big
        ("er", "e"),  # nicer -> nice
        ("est", "e"),  # nicest -> nice
    ]

    ADV_RULES: ClassVar[list[tuple[str, str]]] = []  # No morphology for adverbs

    def __init__(self, loader: WordNetLoader) -> None:
        """Initialize morphy with a WordNet loader.

        Parameters
        ----------
        loader : WordNetLoader
            WordNet loader with exception lists and lemma index.
        """
        self.loader = loader

        # Build suffix rules dictionary
        self.suffix_rules: dict[WordNetPOS, list[tuple[str, str]]] = {
            "n": self.NOUN_RULES,
            "v": self.VERB_RULES,
            "a": self.ADJ_RULES,
            "s": self.ADJ_RULES,  # Satellite adjectives use same rules
            "r": self.ADV_RULES,
        }

    def morphy(self, word: str, pos: WordNetPOS | None = None) -> list[str]:
        """Find base forms of a word for given POS.

        This is the main entry point for morphological processing.
        It returns all possible base forms found through exception
        lists and suffix rules. Handles collocations and special cases.

        Parameters
        ----------
        word : str
            The inflected word or collocation to process.
        pos : WordNetPOS | None, default=None
            Part of speech. If None, tries all POS.

        Returns
        -------
        list[str]
            List of base forms found. Empty if none found.

        Examples
        --------
        >>> lemmas = morphy.morphy("running", "v")
        >>> print(lemmas)
        ['run']

        >>> lemmas = morphy.morphy("geese", "n")
        >>> print(lemmas)
        ['goose']

        >>> lemmas = morphy.morphy("attorneys general", "n")
        >>> print(lemmas)
        ['attorney general']
        """
        # Normalize word to lowercase
        word = word.lower()

        # Remove periods from potential abbreviations
        word_no_period = word.rstrip(".")

        # Determine POS tags to try
        pos_tags: list[WordNetPOS]
        pos_tags = [pos] if pos is not None else ["n", "v", "a", "r"]

        base_forms: list[str] = []
        seen = set()

        # Check for collocations (multi-word expressions)
        if " " in word or "-" in word:
            # Process as collocation
            collocation_forms = self._morphy_collocation(word, pos_tags)
            for form in collocation_forms:
                if form not in seen:
                    base_forms.append(form)
                    seen.add(form)

        # Process as single word (also try without period)
        for test_word in [word, word_no_period]:
            if test_word != word and test_word == word_no_period and word != word_no_period:
                # Only test without period if it's different
                pass

            for pos_tag in pos_tags:
                # Get base forms for this POS
                forms = self._morphy_pos(test_word, pos_tag)

                # Add unique forms
                for form in forms:
                    if form not in seen:
                        base_forms.append(form)
                        seen.add(form)

        return base_forms

    def _morphy_collocation(self, collocation: str, pos_tags: list[WordNetPOS]) -> list[str]:
        """Process multi-word expressions and collocations.

        Parameters
        ----------
        collocation : str
            The multi-word expression to process.
        pos_tags : list[WordNetPOS]
            List of POS tags to try.

        Returns
        -------
        list[str]
            List of base forms for the collocation.
        """
        base_forms: list[str] = []

        # Split on both spaces and hyphens
        words = re.split(r"[\s-]+", collocation)

        # Check if it's a verb-preposition-noun pattern (for verbs)
        if "v" in pos_tags and len(words) >= 3:
            # Try morphing as verb collocation
            verb_forms = self._morphy_verb_collocation(words)
            base_forms.extend(verb_forms)

        # Try morphing individual words and recombining
        if "n" in pos_tags:
            # For nouns, morph each word individually
            morphed_words = []
            for word in words:
                word_forms = self._morphy_pos(word, "n")
                if word_forms:
                    morphed_words.append(word_forms[0])
                else:
                    morphed_words.append(word)

            # Recombine with original delimiters
            recombined = "-".join(morphed_words) if "-" in collocation else " ".join(morphed_words)

            # Check if recombined form exists in WordNet
            if self._is_collocation_in_wordnet(recombined, "n"):
                base_forms.append(recombined)

        return base_forms

    def _morphy_verb_collocation(self, words: list[str]) -> list[str]:
        """Process verb collocations with prepositions.

        Assumes first word is verb, last is noun, middle is preposition(s).

        Parameters
        ----------
        words : list[str]
            List of words in the collocation.

        Returns
        -------
        list[str]
            List of base forms for verb collocation.
        """
        base_forms: list[str] = []

        if len(words) < 3:
            return base_forms

        # Morph first word as verb
        verb_forms = self._morphy_pos(words[0], "v")
        base_verb = verb_forms[0] if verb_forms else words[0]

        # Morph last word as noun
        noun_forms = self._morphy_pos(words[-1], "n")
        base_noun = noun_forms[0] if noun_forms else words[-1]

        # Keep middle words (prepositions) as-is
        middle = " ".join(words[1:-1])

        # Build search string
        search_string = f"{base_verb} {middle} {base_noun}"

        # Check if it exists in WordNet
        if self._is_collocation_in_wordnet(search_string, "v"):
            base_forms.append(search_string)

        return base_forms

    def _morphy_pos(self, word: str, pos: WordNetPOS) -> list[str]:
        """Find base forms for a specific POS.

        Parameters
        ----------
        word : str
            The word to process (lowercase).
        pos : WordNetPOS
            The part of speech.

        Returns
        -------
        list[str]
            List of base forms for this POS.
        """
        base_forms: list[str] = []

        # Special handling for nouns ending with "ful"
        if pos == "n" and word.endswith("ful"):
            ful_form = self._handle_ful_suffix(word)
            if ful_form and self._is_in_wordnet(ful_form, pos):
                base_forms.append(ful_form)

        # Check if word itself is in WordNet
        if self._is_in_wordnet(word, pos):
            base_forms.append(word)

        # Check exception lists
        exceptions = self.check_exceptions(word, pos)
        for exc in exceptions:
            if exc not in base_forms and self._is_in_wordnet(exc, pos):
                base_forms.append(exc)

        # Apply morphological rules
        candidates = self.apply_rules(word, pos)
        for candidate in candidates:
            if candidate not in base_forms and self._is_in_wordnet(candidate, pos):
                base_forms.append(candidate)

        return base_forms

    def _handle_ful_suffix(self, word: str) -> str | None:
        """Handle special case of nouns ending with 'ful'.

        Transforms the substring preceding 'ful', then appends 'ful' back.
        For example: "boxesful" -> "boxful"

        Parameters
        ----------
        word : str
            Word ending with 'ful'.

        Returns
        -------
        str | None
            Transformed word or None if no transformation applies.
        """
        if not word.endswith("ful") or len(word) <= 3:
            return None

        # Get the part before "ful"
        prefix = word[:-3]

        # Apply noun morphology to the prefix
        prefix_forms = self._morphy_pos(prefix, "n")

        if prefix_forms:
            # Use the first base form found
            return prefix_forms[0] + "ful"

        return None

    def check_exceptions(self, word: str, pos: WordNetPOS) -> list[str]:
        """Check exception lists for irregular forms.

        Parameters
        ----------
        word : str
            The word to check (lowercase).
        pos : WordNetPOS
            The part of speech.

        Returns
        -------
        list[str]
            List of base forms from exception list.

        Examples
        --------
        >>> morphy.check_exceptions("children", "n")
        ['child']

        >>> morphy.check_exceptions("went", "v")
        ['go']
        """
        exceptions = self.loader.get_exceptions(pos)
        return exceptions.get(word, [])

    def apply_rules(self, word: str, pos: WordNetPOS) -> list[str]:
        """Apply morphological rules to generate candidates.

        Parameters
        ----------
        word : str
            The word to process (lowercase).
        pos : WordNetPOS
            The part of speech.

        Returns
        -------
        list[str]
            List of candidate base forms.

        Examples
        --------
        >>> morphy.apply_rules("running", "v")
        ['runn', 'run', 'runne', 'running']
        """
        candidates = []
        rules = self.suffix_rules.get(pos, [])

        for suffix, replacement in rules:
            if word.endswith(suffix):
                # Generate candidate by replacing suffix
                candidate = word[: -len(suffix)] + replacement if suffix else word + replacement

                if candidate and candidate not in candidates:
                    candidates.append(candidate)

                # Handle doubled consonants (e.g., running -> run)
                # Check if the word has a doubled consonant before the suffix
                if suffix and len(word) > len(suffix) + 2:
                    stem = word[: -len(suffix)]
                    if len(stem) >= 2 and stem[-1] == stem[-2] and stem[-1] in "bdfglmnprst":
                        # Remove the doubled consonant
                        undoubled = stem[:-1] + replacement
                        if undoubled not in candidates:
                            candidates.append(undoubled)

        return candidates

    def _is_in_wordnet(self, word: str, pos: WordNetPOS) -> bool:
        """Check if a word exists in WordNet for given POS.

        Parameters
        ----------
        word : str
            The word to check (lowercase).
        pos : WordNetPOS
            The part of speech.

        Returns
        -------
        bool
            True if word exists in WordNet.
        """
        # Check if word is in lemma index
        if word in self.loader.lemma_index:
            return pos in self.loader.lemma_index[word]
        return False

    def _is_collocation_in_wordnet(self, collocation: str, pos: WordNetPOS) -> bool:
        """Check if a collocation exists in WordNet for given POS.

        Parameters
        ----------
        collocation : str
            The multi-word expression to check.
        pos : WordNetPOS
            The part of speech.

        Returns
        -------
        bool
            True if collocation exists in WordNet.
        """
        # For collocations, we need to check with underscores
        # WordNet stores multi-word expressions with underscores
        wordnet_form = collocation.replace(" ", "_").replace("-", "_")
        return self._is_in_wordnet(wordnet_form, pos)

    def get_base_forms(self, word: str, pos: WordNetPOS | None = None) -> list[str]:
        """Get all possible base forms of a word.

        This method returns all candidates without checking if they
        exist in WordNet. Useful for debugging or when you want all
        morphological variants.

        Parameters
        ----------
        word : str
            The word to process.
        pos : WordNetPOS | None, default=None
            Part of speech. If None, tries all POS.

        Returns
        -------
        list[str]
            List of all candidate base forms.

        Examples
        --------
        >>> forms = morphy.get_base_forms("running", "v")
        >>> print(forms)
        ['running', 'run', 'runn', 'runne']
        """
        word = word.lower()

        # Determine POS tags
        pos_tags: list[WordNetPOS] = [pos] if pos is not None else ["n", "v", "a", "r"]

        all_forms = []
        seen = set()

        for pos_tag in pos_tags:
            # Add word itself
            if word not in seen:
                all_forms.append(word)
                seen.add(word)

            # Add exceptions
            for exc in self.check_exceptions(word, pos_tag):
                if exc not in seen:
                    all_forms.append(exc)
                    seen.add(exc)

            # Add rule-based candidates
            for candidate in self.apply_rules(word, pos_tag):
                if candidate not in seen:
                    all_forms.append(candidate)
                    seen.add(candidate)

        return all_forms


def morphy(
    word: str, pos: WordNetPOS | None = None, loader: WordNetLoader | None = None
) -> list[str]:
    """Find base forms of a word.

    Convenience function for morphological processing.

    Parameters
    ----------
    word : str
        The word to process.
    pos : WordNetPOS | None, default=None
        Part of speech. If None, tries all POS.
    loader : WordNetLoader | None, default=None
        WordNet loader. If None, uses default instance.

    Returns
    -------
    list[str]
        List of base forms.

    Raises
    ------
    ValueError
        If loader is None and no default is available.

    Examples
    --------
    >>> lemmas = morphy("running", "v", loader)
    >>> print(lemmas)
    ['run']
    """
    if loader is None:
        raise ValueError("WordNet loader required for morphy")

    processor = Morphy(loader)
    return processor.morphy(word, pos)
