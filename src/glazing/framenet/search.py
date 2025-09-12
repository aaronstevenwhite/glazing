"""FrameNet search functionality.

This module provides search capabilities for FrameNet data,
including frame searches by name and definition, frame element searches
across frames, and lexical unit pattern matching.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from glazing.framenet.models import Frame, FrameElement, LexicalUnit
from glazing.framenet.types import CoreType, FrameID, FrameNetPOS


class FrameNetSearch:
    """Search interface for FrameNet frame lookups.

    Provides search methods for frames, frame elements,
    and lexical units with pattern matching and cross-frame queries.

    Parameters
    ----------
    frames : list[Frame] | None
        Initial frames to index. If None, creates empty index.

    Attributes
    ----------
    _frames_by_id : dict[FrameID, Frame]
        Mapping from frame ID to frame object.
    _frames_by_name : dict[str, Frame]
        Mapping from frame name to frame object.
    _frames_by_lemma : dict[str, set[Frame]]
        Mapping from lemma to frames evoked by that lemma.
    _fe_index : dict[str, set[Frame]]
        Mapping from FE name to frames containing that FE.
    _lu_index : dict[str, set[LexicalUnit]]
        Mapping from lemma to lexical units.

    Methods
    -------
    add_frame(frame)
        Add a frame to the index.
    get_frame_by_id(frame_id)
        Get frame by ID.
    get_frame_by_name(name)
        Get frame by name.
    search_frames_by_name(pattern, case_sensitive)
        Search frames by name pattern.
    search_frames_by_definition(pattern, case_sensitive)
        Search frames by definition pattern.
    find_frames_with_fe(fe_name, core_type)
        Find frames containing a specific FE.
    find_frames_by_lemma(lemma, pos)
        Find frames evoked by a lemma.
    search_lexical_units(pattern, pos, case_sensitive)
        Search lexical units by pattern.
    get_fe_across_frames(fe_name)
        Get FE definitions across all frames.

    Examples
    --------
    >>> search = FrameNetSearch()
    >>> search.add_frame(abandonment_frame)
    >>> frame = search.get_frame_by_name("Abandonment")
    >>> frames = search.search_frames_by_definition("leave.*behind")
    """

    def __init__(self, frames: list[Frame] | None = None) -> None:
        """Initialize frame index with optional initial frames."""
        self._frames_by_id: dict[FrameID, Frame] = {}
        self._frames_by_name: dict[str, Frame] = {}
        self._frames_by_lemma: dict[str, set[FrameID]] = defaultdict(set)
        self._fe_index: dict[str, set[FrameID]] = defaultdict(set)
        self._lu_index: dict[str, set[tuple[FrameID, int]]] = defaultdict(set)

        if frames:
            for frame in frames:
                self.add_frame(frame)

    def add_frame(self, frame: Frame) -> None:
        """Add a frame to the index.

        Parameters
        ----------
        frame : Frame
            Frame to add to index.

        Raises
        ------
        ValueError
            If frame with same ID already exists.
        """
        if frame.id in self._frames_by_id:
            msg = f"Frame with ID {frame.id} already exists in index"
            raise ValueError(msg)

        self._frames_by_id[frame.id] = frame
        self._frames_by_name[frame.name] = frame

        # Index frame elements
        for fe in frame.frame_elements:
            self._fe_index[fe.name].add(frame.id)

        # Index lexical units
        for lu in frame.lexical_units:
            # Extract lemma from LU name (format: lemma.pos)
            if "." in lu.name:
                lemma = lu.name.rsplit(".", 1)[0]
                self._frames_by_lemma[lemma].add(frame.id)
                self._lu_index[lemma].add((frame.id, lu.id))

    def get_frame_by_id(self, frame_id: FrameID) -> Frame | None:
        """Get frame by ID.

        Parameters
        ----------
        frame_id : FrameID
            Frame ID to look up.

        Returns
        -------
        Frame | None
            Frame if found, None otherwise.
        """
        return self._frames_by_id.get(frame_id)

    def get_frame_by_name(self, name: str) -> Frame | None:
        """Get frame by name.

        Parameters
        ----------
        name : str
            Frame name to look up.

        Returns
        -------
        Frame | None
            Frame if found, None otherwise.
        """
        return self._frames_by_name.get(name)

    def search_frames_by_name(self, pattern: str, case_sensitive: bool = False) -> list[Frame]:
        """Search frames by name pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against frame names.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[Frame]
            Frames with names matching pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_frames = []
        for name, frame in self._frames_by_name.items():
            if regex.search(name):
                matching_frames.append(frame)

        return sorted(matching_frames, key=lambda f: f.name)

    def search_frames_by_definition(
        self, pattern: str, case_sensitive: bool = False
    ) -> list[Frame]:
        """Search frames by definition pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against frame definitions.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[Frame]
            Frames with definitions matching pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_frames = []
        for frame in self._frames_by_id.values():
            # Search in plain text of definition
            if regex.search(frame.definition.plain_text):
                matching_frames.append(frame)

        return sorted(matching_frames, key=lambda f: f.name)

    def find_frames_with_fe(self, fe_name: str, core_type: CoreType | None = None) -> list[Frame]:
        """Find frames containing a specific frame element.

        Parameters
        ----------
        fe_name : str
            Name of frame element to search for.
        core_type : CoreType | None
            If specified, only return frames where FE has this core type.

        Returns
        -------
        list[Frame]
            Frames containing the specified FE.
        """
        frame_ids = self._fe_index.get(fe_name, set())
        frames = [self._frames_by_id[fid] for fid in frame_ids]

        if core_type is not None:
            filtered_frames = []
            for frame in frames:
                fe = frame.get_fe_by_name(fe_name)
                if fe and fe.core_type == core_type:
                    filtered_frames.append(frame)
            frames = filtered_frames

        return sorted(frames, key=lambda f: f.name)

    def find_frames_by_lemma(self, lemma: str, pos: FrameNetPOS | None = None) -> list[Frame]:
        """Find frames evoked by a lemma.

        Parameters
        ----------
        lemma : str
            Lemma to search for.
        pos : FrameNetPOS | None
            If specified, only return frames with LUs of this POS.

        Returns
        -------
        list[Frame]
            Frames evoked by the lemma.
        """
        frame_ids = self._frames_by_lemma.get(lemma, set())
        frames = [self._frames_by_id[fid] for fid in frame_ids]

        if pos is not None:
            filtered_frames = []
            for frame in frames:
                # Check if any LU for this lemma has the specified POS
                for lu in frame.lexical_units:
                    if "." in lu.name:
                        lu_lemma = lu.name.rsplit(".", 1)[0]
                        if lu_lemma == lemma and lu.pos == pos:
                            filtered_frames.append(frame)
                            break
            frames = filtered_frames

        return sorted(frames, key=lambda f: f.name)

    def search_lexical_units(
        self, pattern: str, pos: FrameNetPOS | None = None, case_sensitive: bool = False
    ) -> list[LexicalUnit]:
        """Search lexical units by pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern to match against LU names.
        pos : FrameNetPOS | None
            If specified, only return LUs with this POS.
        case_sensitive : bool
            Whether search should be case-sensitive.

        Returns
        -------
        list[LexicalUnit]
            Lexical units matching the pattern.

        Raises
        ------
        re.error
            If pattern is invalid regular expression.
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        matching_lus = []
        seen_lu_ids = set()
        for lu_refs in self._lu_index.values():
            for frame_id, lu_id in lu_refs:
                if lu_id not in seen_lu_ids:
                    frame = self._frames_by_id[frame_id]
                    for lu in frame.lexical_units:
                        if (
                            lu.id == lu_id
                            and regex.search(lu.name)
                            and (pos is None or lu.pos == pos)
                        ):
                            matching_lus.append(lu)
                            seen_lu_ids.add(lu_id)
                            break

        return sorted(matching_lus, key=lambda lu: lu.name)

    def get_fe_across_frames(self, fe_name: str) -> dict[str, FrameElement]:
        """Get frame element definitions across all frames.

        Parameters
        ----------
        fe_name : str
            Name of frame element to retrieve.

        Returns
        -------
        dict[str, FrameElement]
            Mapping from frame name to FE definition in that frame.
        """
        fe_definitions = {}
        frame_ids = self._fe_index.get(fe_name, set())
        for frame_id in frame_ids:
            frame = self._frames_by_id[frame_id]
            fe = frame.get_fe_by_name(fe_name)
            if fe:
                fe_definitions[frame.name] = fe

        return dict(sorted(fe_definitions.items()))

    def get_all_fe_names(self) -> list[str]:
        """Get all unique frame element names across all frames.

        Returns
        -------
        list[str]
            Sorted list of unique FE names.
        """
        return sorted(self._fe_index.keys())

    def get_all_lemmas(self) -> list[str]:
        """Get all unique lemmas across all lexical units.

        Returns
        -------
        list[str]
            Sorted list of unique lemmas.
        """
        return sorted(self._frames_by_lemma.keys())

    def get_statistics(self) -> dict[str, int]:
        """Get index statistics.

        Returns
        -------
        dict[str, int]
            Statistics about indexed data.
        """
        total_lus = sum(len(frame.lexical_units) for frame in self._frames_by_id.values())

        total_fes = sum(len(frame.frame_elements) for frame in self._frames_by_id.values())

        return {
            "frame_count": len(self._frames_by_id),
            "unique_fe_names": len(self._fe_index),
            "total_fes": total_fes,
            "unique_lemmas": len(self._frames_by_lemma),
            "total_lus": total_lus,
        }

    @classmethod
    def from_jsonl_file(cls, path: Path | str) -> FrameNetSearch:
        """Load index from JSON Lines file.

        Parameters
        ----------
        path : Path | str
            Path to JSON Lines file containing frames.

        Returns
        -------
        FrameIndex
            Index populated with frames from file.

        Raises
        ------
        FileNotFoundError
            If file does not exist.
        ValueError
            If file contains invalid data.
        """
        path = Path(path)
        if not path.exists():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        frames = []
        with path.open(encoding="utf-8") as f:
            for line_raw in f:
                line = line_raw.strip()
                if line:
                    frame = Frame.model_validate_json(line)
                    frames.append(frame)

        return cls(frames)

    def merge(self, other: FrameNetSearch) -> None:
        """Merge another index into this one.

        Parameters
        ----------
        other : FrameIndex
            Index to merge into this one.

        Raises
        ------
        ValueError
            If there are conflicting frame IDs.
        """
        for frame_id, frame in other._frames_by_id.items():
            if frame_id in self._frames_by_id:
                msg = f"Cannot merge: frame ID {frame_id} exists in both indices"
                raise ValueError(msg)
            self.add_frame(frame)
