"""Pytest configuration and shared fixtures for the frames test suite.

This module provides common fixtures and configuration for testing
the frames package components.
"""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory.

    Returns
    -------
    Path
        Path to the fixtures directory containing test data.
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_framenet_data() -> dict:
    """Provide sample FrameNet data for testing.

    Returns
    -------
    dict
        Sample FrameNet frame data.
    """
    return {
        "id": 7,
        "name": "Abandonment",
        "definition": "An Agent leaves behind a Theme.",
        "frame_elements": [
            {
                "id": 1,
                "name": "Agent",
                "abbrev": "Agt",
                "definition": "The conscious entity that leaves the Theme behind.",
                "core_type": "Core",
                "bg_color": "FF0000",
                "fg_color": "FFFFFF",
            },
            {
                "id": 2,
                "name": "Theme",
                "abbrev": "Thm",
                "definition": "The entity that is left behind by the Agent.",
                "core_type": "Core",
                "bg_color": "0000FF",
                "fg_color": "FFFFFF",
            },
        ],
    }


@pytest.fixture
def sample_propbank_data() -> dict:
    """Provide sample PropBank data for testing.

    Returns
    -------
    dict
        Sample PropBank roleset data.
    """
    return {
        "id": "abandon.01",
        "name": "leave behind",
        "roles": [
            {"n": "0", "f": "PAG", "descr": "abandoner"},
            {"n": "1", "f": "PPT", "descr": "thing abandoned"},
        ],
    }


@pytest.fixture
def sample_verbnet_data() -> dict:
    """Provide sample VerbNet data for testing.

    Returns
    -------
    dict
        Sample VerbNet class data.
    """
    return {
        "id": "leave-51.2",
        "members": [
            {
                "name": "abandon",
                "verbnet_key": "abandon#1",
                "wn": "abandon%2:40:00",
                "grouping": "abandon.01",
                "fn_mapping": "Abandonment",
            }
        ],
        "themroles": [
            {"type": "Agent", "sel_restrictions": {"value": "+", "type": "animate"}},
            {"type": "Theme", "sel_restrictions": None},
        ],
    }


@pytest.fixture
def sample_wordnet_data() -> dict:
    """Provide sample WordNet data for testing.

    Returns
    -------
    dict
        Sample WordNet synset data.
    """
    return {
        "offset": "02228111",
        "lex_filenum": 40,
        "ss_type": "v",
        "words": [
            {"lemma": "abandon", "lex_id": 0},
            {"lemma": "forsake", "lex_id": 0},
            {"lemma": "desolate", "lex_id": 0},
            {"lemma": "desert", "lex_id": 3},
        ],
        "gloss": "leave someone who needs or counts on you; leave in the lurch",
    }
