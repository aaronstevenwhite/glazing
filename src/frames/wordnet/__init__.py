"""WordNet data models and utilities.

This module provides models for WordNet synsets, word senses, lexical and
semantic relations. It supports the complete WordNet 3.1 database structure
including morphological processing and relation traversal.

Classes
-------
Synset
    A set of cognitive synonyms representing a concept.
Word
    A lemma within a synset.
Sense
    A word-meaning pair with sense key.
Pointer
    A relation to another synset or word.

Functions
---------
load
    Load WordNet data from JSON Lines.

Examples
--------
>>> from frames.wordnet import load
>>> wn = load("data/wordnet.json")
>>> synset = wn.get_synset("02084442")  # dog.n.01
>>> print(synset.gloss)
"""

__all__: list[str] = []
