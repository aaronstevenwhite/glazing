"""FrameNet XML to JSON Lines converter.

This module provides conversion from FrameNet XML format to JSON Lines format
using the glazing FrameNet models. Supports both full frame files and lu files.

Classes
-------
FrameNetConverter
    Convert FrameNet XML files to JSON Lines format.

Functions
---------
convert_frame_file
    Convert a single frame XML file to Frame model.
convert_lu_file
    Convert a single lexical unit XML file to LexicalUnit model.
convert_frames_directory
    Convert all frame files in a directory to JSON Lines.

Examples
--------
>>> from pathlib import Path
>>> from glazing.framenet.converter import FrameNetConverter
>>> converter = FrameNetConverter()
>>> frame = converter.convert_frame_file("frame/Abandonment.xml")
>>> print(frame.name)
'Abandonment'

>>> # Convert entire directory
>>> converter.convert_frames_directory(
...     input_dir="framenet_v17/frame",
...     output_file="frames.jsonl"
... )
"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from pathlib import Path

from lxml import etree

from glazing.framenet.models import (
    AnnotatedText,
    Frame,
    FrameElement,
)
from glazing.utils.xml_parser import (
    parse_attributes,
    parse_with_schema,
)


class FrameNetConverter:
    """Convert FrameNet XML files to JSON Lines format.

    Parameters
    ----------
    namespace : str, default="http://framenet.icsi.berkeley.edu"
        FrameNet XML namespace URI.
    validate_schema : bool, default=False
        Whether to validate against DTD/XSD.

    Attributes
    ----------
    namespace : str
        FrameNet XML namespace.
    ns : dict[str, str]
        Namespace mapping for XPath.

    Methods
    -------
    convert_frame_file(filepath)
        Convert a frame XML file to Frame model.
    convert_lu_file(filepath)
        Convert a lexical unit XML file to LexicalUnit model.
    convert_frames_directory(input_dir, output_file)
        Convert all frames in a directory to JSON Lines.
    """

    def __init__(
        self,
        namespace: str = "http://framenet.icsi.berkeley.edu",
        validate_schema: bool = False,
    ) -> None:
        """Initialize the converter.

        Parameters
        ----------
        namespace : str
            FrameNet XML namespace URI.
        validate_schema : bool
            Whether to validate XML against schema.
        """
        self.namespace = namespace
        self.ns = {"fn": namespace} if namespace else {}
        self.validate_schema = validate_schema

    def _parse_definition(self, element: etree._Element | None) -> AnnotatedText:
        """Parse a definition element with embedded markup.

        Parameters
        ----------
        element : etree._Element | None
            The definition element.

        Returns
        -------
        AnnotatedText
            Parsed definition with annotations.
        """
        if element is None or element.text is None:
            return AnnotatedText(raw_text="", plain_text="", annotations=[])

        # FrameNet definitions have HTML entities that need decoding
        raw_text = element.text
        decoded_text = html.unescape(raw_text)

        # Parse the decoded text as AnnotatedText
        return AnnotatedText.parse(decoded_text)

    def _parse_datetime(self, date_str: str | None) -> datetime | None:
        """Parse FrameNet datetime string.

        Parameters
        ----------
        date_str : str | None
            Date string like "03/05/2008 03:50:35 PST Wed".

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if not date_str:
            return None

        # FrameNet uses multiple datetime formats
        # Primary format: "MM/DD/YYYY HH:MM:SS TZ Day"
        # Secondary formats for variations in the data
        formats = [
            "%m/%d/%Y %H:%M:%S",  # Without timezone/day
            "%d/%m/%Y %H:%M:%S",  # European date format
            "%Y-%m-%d %H:%M:%S",  # ISO-like format
            "%m/%d/%Y",  # Date only
            "%d/%m/%Y",  # European date only
            "%Y-%m-%d",  # ISO date only
        ]

        # Try to parse with timezone and day suffix first
        parts = date_str.split()

        # Try primary format (first two parts: date and time)
        if len(parts) >= 2:
            date_time = " ".join(parts[:2])
            for fmt in formats[:3]:  # Try datetime formats first
                try:
                    return datetime.strptime(date_time, fmt).replace(tzinfo=UTC)
                except ValueError:
                    continue

        # Try with just the first part (date only)
        if len(parts) >= 1:
            for fmt in formats[3:]:  # Try date-only formats
                try:
                    return datetime.strptime(parts[0], fmt).replace(tzinfo=UTC)
                except ValueError:
                    continue

        # Try the full string with all formats
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=UTC)
            except ValueError:
                continue

        # If all parsing attempts fail, raise an error with details
        error_msg = (
            f"Unable to parse datetime string '{date_str}'. "
            f"Expected format like 'MM/DD/YYYY HH:MM:SS TZ Day' or similar. "
            f"Tried formats: {', '.join(formats)}"
        )
        raise ValueError(error_msg)

    def _validate_fe_attributes(self, attrs: dict[str, str | int | float | bool]) -> None:
        """Validate required frame element attributes.

        Parameters
        ----------
        attrs : dict[str, str | int]
            Attributes to validate.

        Raises
        ------
        ValueError
            If required attributes are missing.
        """
        required = ["ID", "name", "coreType", "bgColor", "fgColor"]
        for attr in required:
            if attr not in attrs:
                msg = f"Missing required '{attr}' attribute in FrameElement"
                raise ValueError(msg)

    def _parse_fe_constraints(self, fe_elem: etree._Element) -> tuple[list[str], list[str]]:
        """Parse frame element constraints.

        Parameters
        ----------
        fe_elem : etree._Element
            The FE element.

        Returns
        -------
        tuple[list[str], list[str]]
            Requires and excludes lists.
        """
        requires_fe = []
        excludes_fe = []

        requires_elem = fe_elem.find(
            f"{{{self.namespace}}}requiresFE" if self.namespace else "requiresFE"
        )
        if requires_elem is not None:
            requires_fe = [req.get("name", "") for req in requires_elem]

        excludes_elem = fe_elem.find(
            f"{{{self.namespace}}}excludesFE" if self.namespace else "excludesFE"
        )
        if excludes_elem is not None:
            excludes_fe = [exc.get("name", "") for exc in excludes_elem]

        return requires_fe, excludes_fe

    def _parse_fe_semtypes(self, fe_elem: etree._Element) -> list[int]:
        """Parse frame element semantic types.

        Parameters
        ----------
        fe_elem : etree._Element
            The FE element.

        Returns
        -------
        list[int]
            Semantic type IDs.
        """
        semtype_refs = []
        semtypes_elem = fe_elem.find(
            f"{{{self.namespace}}}semTypes" if self.namespace else "semTypes"
        )
        if semtypes_elem is not None:
            for semtype in semtypes_elem:
                sem_id = semtype.get("ID")
                if sem_id:
                    semtype_refs.append(int(sem_id))
        return semtype_refs

    def _parse_frame_element(self, fe_elem: etree._Element) -> FrameElement:
        """Parse a frame element from XML.

        Parameters
        ----------
        fe_elem : etree._Element
            The FE element.

        Returns
        -------
        FrameElement
            Parsed frame element.
        """
        attrs = parse_attributes(fe_elem, {"ID": int})
        self._validate_fe_attributes(attrs)

        # Parse definition
        def_elem = fe_elem.find(
            f"{{{self.namespace}}}definition" if self.namespace else "definition"
        )
        definition = self._parse_definition(def_elem)

        # Parse constraints and semantic types
        requires_fe, excludes_fe = self._parse_fe_constraints(fe_elem)
        semtype_refs = self._parse_fe_semtypes(fe_elem)

        # Get abbreviation - no fallback generation
        abbrev = str(attrs.get("abbrev", ""))

        return FrameElement(
            id=int(attrs["ID"]),
            name=str(attrs["name"]),
            abbrev=abbrev if abbrev else str(attrs["name"]),  # Use name if abbrev empty
            definition=definition,
            core_type=str(attrs["coreType"]),  # type: ignore[arg-type]
            bg_color=str(attrs["bgColor"]),
            fg_color=str(attrs["fgColor"]),
            requires_fe=requires_fe,
            excludes_fe=excludes_fe,
            semtype_refs=semtype_refs,
            created_by=str(attrs.get("cBy")) if attrs.get("cBy") else None,
            created_date=self._parse_datetime(
                str(attrs.get("cDate")) if attrs.get("cDate") else None
            ),
        )

    def convert_frame_file(self, filepath: Path | str) -> Frame:
        """Convert a frame XML file to Frame model.

        Parameters
        ----------
        filepath : Path | str
            Path to frame XML file.

        Returns
        -------
        Frame
            Parsed Frame model instance.

        Examples
        --------
        >>> converter = FrameNetConverter()
        >>> frame = converter.convert_frame_file("frame/Abandonment.xml")
        >>> print(f"Frame: {frame.name} (ID: {frame.id})")
        'Frame: Abandonment (ID: 2031)'
        """
        filepath = Path(filepath)

        # Parse XML
        if self.validate_schema:
            root = parse_with_schema(filepath)
        else:
            tree = etree.parse(str(filepath))
            root = tree.getroot()

        # Extract frame attributes
        attrs = parse_attributes(root, {"ID": int})

        # Parse definition
        def_elem = root.find(f"{{{self.namespace}}}definition" if self.namespace else "definition")
        definition = self._parse_definition(def_elem)

        # Parse frame elements
        frame_elements = []
        fe_tag = f"{{{self.namespace}}}FE" if self.namespace else "FE"
        for fe_elem in root.findall(fe_tag):
            frame_elements.append(self._parse_frame_element(fe_elem))

        return Frame(
            id=int(attrs.get("ID", 0)),
            name=str(attrs.get("name", "")),
            definition=definition,
            frame_elements=frame_elements,
            created_by=str(attrs.get("cBy")) if attrs.get("cBy") else None,
            created_date=self._parse_datetime(
                str(attrs.get("cDate")) if attrs.get("cDate") else None
            ),
            modified_date=self._parse_datetime(
                str(attrs.get("mDate")) if attrs.get("mDate") else None
            ),
        )

    def convert_frames_directory(
        self,
        input_dir: Path | str,
        output_file: Path | str,
        pattern: str = "*.xml",
    ) -> int:
        """Convert all frame files in a directory to JSON Lines.

        Parameters
        ----------
        input_dir : Path | str
            Directory containing frame XML files.
        output_file : Path | str
            Output JSON Lines file path.
        pattern : str, default="*.xml"
            File pattern to match.

        Returns
        -------
        int
            Number of frames converted.

        Examples
        --------
        >>> converter = FrameNetConverter()
        >>> count = converter.convert_frames_directory(
        ...     "framenet_v17/frame",
        ...     "frames.jsonl"
        ... )
        >>> print(f"Converted {count} frames")
        'Converted 1221 frames'
        """
        input_dir = Path(input_dir)
        output_file = Path(output_file)

        count = 0
        errors: list[tuple[Path, Exception]] = []

        with output_file.open("w", encoding="utf-8") as f:
            for xml_file in sorted(input_dir.glob(pattern)):
                try:
                    frame = self.convert_frame_file(xml_file)
                    # Write as JSON Lines
                    json_line = frame.model_dump_json(exclude_none=True)
                    f.write(json_line + "\n")
                    count += 1
                except (etree.XMLSyntaxError, ValueError, TypeError) as e:
                    errors.append((xml_file, e))

        # If there were any errors, raise an exception with details
        if errors:
            error_details = "\n".join(f"  - {file}: {error}" for file, error in errors)
            total_files = count + len(errors)
            error_msg = (
                f"Failed to convert {len(errors)} out of {total_files} files:\n{error_details}"
            )
            raise RuntimeError(error_msg)

        return count


# Convenience functions
def convert_frame_file(filepath: Path | str) -> Frame:
    """Convert a single frame XML file to Frame model.

    Parameters
    ----------
    filepath : Path | str
        Path to frame XML file.

    Returns
    -------
    Frame
        Parsed Frame model.
    """
    converter = FrameNetConverter()
    return converter.convert_frame_file(filepath)


def convert_frames_directory(
    input_dir: Path | str,
    output_file: Path | str,
    pattern: str = "*.xml",
) -> int:
    """Convert all frames in a directory to JSON Lines.

    Parameters
    ----------
    input_dir : Path | str
        Directory with frame XML files.
    output_file : Path | str
        Output JSON Lines file.
    pattern : str
        File pattern to match.

    Returns
    -------
    int
        Number of frames converted.
    """
    converter = FrameNetConverter()
    return converter.convert_frames_directory(input_dir, output_file, pattern)
