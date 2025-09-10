"""Shared utilities and helper functions.

This module provides common utilities used across the package including
XML parsing, validation, caching, and data conversion helpers.

Functions
---------
parse_xml
    Parse XML with namespace handling.
validate_schema
    Validate data against XSD or DTD schemas.
create_cache
    Create an LRU cache for query results.

Classes
-------
LazyLoader
    Lazy loading for large datasets.
DataCache
    Caching layer for frequently accessed data.

Examples
--------
>>> from frames.utils import LazyLoader
>>> loader = LazyLoader("data/large_dataset.json")
>>> item = loader.get_item(123)  # Loads on demand
"""

__all__: list[str] = []
