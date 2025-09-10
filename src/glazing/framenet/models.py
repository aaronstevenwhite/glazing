"""FrameNet core data models.

This module implements the core FrameNet data models including Frame, FrameElement,
and supporting models for annotated text processing. Models use Pydantic v2
for validation and support JSON Lines serialization.

Classes
-------
TextAnnotation
    Represents an annotation span within text.
AnnotatedText
    Text with embedded markup for frame elements and references.
Frame
    A FrameNet frame representing a schematic situation.
FrameElement
    A participant or prop in a frame.
FrameRelation
    Relationship between frames.
FERelation
    FE mapping between related frames.
SemanticType
    Semantic type in the FrameNet type system.
FrameIndexEntry
    Entry in the frame index file.

Examples
--------
>>> from glazing.framenet.models import Frame, FrameElement
>>> frame = Frame(
...     id=2031,
...     name="Abandonment",
...     definition=AnnotatedText.parse("An <fex>Agent</fex> leaves behind a <fex>Theme</fex>"),
...     frame_elements=[]
... )
>>> print(frame.definition.plain_text)
'An Agent leaves behind a Theme'
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Self

from pydantic import Field, field_validator, model_validator

from glazing.base import GlazingBaseModel, validate_hex_color, validate_pattern
from glazing.framenet.types import (
    FE_ABBREV_PATTERN,
    FE_NAME_PATTERN,
    FRAME_NAME_PATTERN,
    USERNAME_PATTERN,
    CoreType,
    FEAbbrev,
    FEName,
    FrameID,
    FrameName,
    FrameRelationSubType,
    FrameRelationType,
    MarkupType,
    SemTypeID,
    Username,
)
from glazing.types import MappingConfidenceScore


class TextAnnotation(GlazingBaseModel):
    """An annotation within text (FE reference, target, example, etc.).

    Parameters
    ----------
    start : int
        Start position in plain text (0-based).
    end : int
        End position in plain text (exclusive).
    type : MarkupType
        Type of annotation markup.
    name : str | None, default=None
        For FE references - validated as alphanumeric + underscore.
    ref_id : int | None, default=None
        ID of referenced element.
    text : str
        The annotated text span.

    Methods
    -------
    get_length()
        Get the length of the annotation span.
    overlaps_with(other)
        Check if this annotation overlaps with another.

    Examples
    --------
    >>> annotation = TextAnnotation(
    ...     start=3, end=8, type="fex", name="Agent", text="Agent"
    ... )
    >>> print(annotation.get_length())
    5
    """

    start: int = Field(ge=0, description="Start position in plain text")
    end: int = Field(ge=0, description="End position in plain text")
    type: MarkupType
    name: str | None = Field(None, description="FE name for fex/fen annotations")
    ref_id: int | None = Field(None, description="ID of referenced element")
    text: str = Field(min_length=1, description="The annotated text span")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate FE reference names."""
        if v is not None and not re.match(r"^[A-Z][A-Za-z0-9_]*$", v):
            msg = f"Invalid FE name format: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_positions(self) -> Self:
        """Validate that end position is after start position."""
        if self.end <= self.start:
            msg = f"End position ({self.end}) must be after start position ({self.start})"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_annotation_requirements(self) -> Self:
        """Validate annotation type-specific requirements."""
        if self.type in ("fex", "fen") and self.name is None:
            msg = f"Annotation type '{self.type}' requires a name"
            raise ValueError(msg)
        return self

    def get_length(self) -> int:
        """Get the length of the annotation span.

        Returns
        -------
        int
            Length of the text span.
        """
        return self.end - self.start

    def overlaps_with(self, other: TextAnnotation) -> bool:
        """Check if this annotation overlaps with another.

        Parameters
        ----------
        other : TextAnnotation
            The other annotation to check.

        Returns
        -------
        bool
            True if the annotations overlap.
        """
        return not (self.end <= other.start or other.end <= self.start)


class AnnotatedText(GlazingBaseModel):
    """Text with embedded markup for frame elements and other references.

    This model parses FrameNet's embedded markup in definitions, extracting
    annotations like <fex>Agent</fex>, <fen>Theme</fen>, etc.

    Parameters
    ----------
    raw_text : str
        Original text with markup.
    plain_text : str
        Text with markup removed.
    annotations : list[TextAnnotation]
        List of annotations found in the text.

    Methods
    -------
    parse(text)
        Parse text with markup and create AnnotatedText instance.
    get_annotations_by_type(markup_type)
        Get all annotations of a specific type.
    get_fe_references()
        Get all frame element references.
    get_targets()
        Get all target annotations.

    Examples
    --------
    >>> text = "An <fex>Agent</fex> leaves behind a <fex name='Theme'>thing</fex>"
    >>> annotated = AnnotatedText.parse(text)
    >>> print(annotated.plain_text)
    'An Agent leaves behind a thing'
    >>> print(len(annotated.annotations))
    2
    """

    raw_text: str = Field(description="Original text with markup")
    plain_text: str = Field(description="Text with markup removed")
    annotations: list[TextAnnotation] = Field(
        default_factory=list, description="Annotations found in text"
    )

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse text with embedded markup.

        Extracts FrameNet markup tags like:
        - <fex>Agent</fex> - Frame element example
        - <fen>Theme</fen> - Frame element name
        - <t>abandon</t> - Target word
        - <ex>example</ex> - Example text

        Parameters
        ----------
        text : str
            Text containing markup.

        Returns
        -------
        Self
            Parsed AnnotatedText instance.

        Examples
        --------
        >>> text = "The <fex>Agent</fex> leaves the <fex name='Theme'>car</fex>"
        >>> parsed = AnnotatedText.parse(text)
        >>> print(parsed.plain_text)
        'The Agent leaves the car'
        """
        if not text:
            return cls(raw_text=text, plain_text=text, annotations=[])

        annotations: list[TextAnnotation] = []
        plain_text = ""
        offset = 0

        # Pattern to match markup tags with optional attributes
        pattern = r"<(\w+)(?:\s+([^>]*))?>([^<]*?)</\1>"

        for match in re.finditer(pattern, text):
            tag_name = match.group(1)
            attributes = match.group(2) or ""
            content = match.group(3)

            # Add text before this tag to plain text
            before_tag = text[offset : match.start()]
            plain_text += before_tag
            start_pos = len(plain_text)

            # Add the content to plain text
            plain_text += content
            end_pos = len(plain_text)

            # Parse attributes for name and ref_id
            name = None
            ref_id = None

            if attributes:
                # Simple attribute parsing - look for name="value" or name=value
                name_match = re.search(r'name=["\']?([^"\'\s>]+)["\']?', attributes)
                if name_match:
                    name = name_match.group(1)

                ref_match = re.search(r'ref(?:_?id)?=["\']?(\d+)["\']?', attributes)
                if ref_match:
                    ref_id = int(ref_match.group(1))

            # For fex and fen tags, if no explicit name is provided, use the content as the name
            if tag_name in ("fex", "fen") and name is None:
                name = content

            # Create annotation
            if tag_name in ("fex", "fen", "t", "ex", "m", "gov", "x", "def-root"):
                annotation = TextAnnotation(
                    start=start_pos,
                    end=end_pos,
                    type=tag_name,  # type: ignore[arg-type]
                    name=name,
                    ref_id=ref_id,
                    text=content,
                )
                annotations.append(annotation)

            offset = match.end()

        # Add any remaining text
        if offset < len(text):
            plain_text += text[offset:]

        return cls(
            raw_text=text,
            plain_text=plain_text,
            annotations=annotations,
        )

    def get_annotations_by_type(self, markup_type: MarkupType) -> list[TextAnnotation]:
        """Get all annotations of a specific type.

        Parameters
        ----------
        markup_type : MarkupType
            The type of annotations to retrieve.

        Returns
        -------
        list[TextAnnotation]
            List of annotations of the specified type.
        """
        return [ann for ann in self.annotations if ann.type == markup_type]

    def get_fe_references(self) -> list[TextAnnotation]:
        """Get all frame element references.

        Returns
        -------
        list[TextAnnotation]
            List of fex and fen annotations.
        """
        return [ann for ann in self.annotations if ann.type in ("fex", "fen")]

    def get_targets(self) -> list[TextAnnotation]:
        """Get all target annotations.

        Returns
        -------
        list[TextAnnotation]
            List of target annotations.
        """
        return self.get_annotations_by_type("t")


class FrameElement(GlazingBaseModel):
    """A participant or prop in a frame.

    Parameters
    ----------
    id : int
        Unique FE identifier.
    name : FEName
        Frame element name (validated pattern).
    abbrev : FEAbbrev
        FE abbreviation (validated pattern).
    definition : AnnotatedText
        Definition with embedded markup.
    core_type : CoreType
        Core classification of this FE.
    bg_color : str
        Background color (6-digit hex).
    fg_color : str
        Foreground color (6-digit hex).
    requires_fe : list[FEName], default=[]
        FE names that this FE requires.
    excludes_fe : list[FEName], default=[]
        FE names that this FE excludes.
    semtype_refs : list[SemTypeID]
        Semantic type references.
    created_by : Username | None, default=None
        Username of creator.
    created_date : datetime | None, default=None
        Creation timestamp.

    Methods
    -------
    has_dependencies()
        Check if this FE has dependency constraints.
    is_core()
        Check if this is a core frame element.
    conflicts_with(other_fe_name)
        Check if this FE conflicts with another.

    Examples
    --------
    >>> fe = FrameElement(
    ...     id=123,
    ...     name="Agent",
    ...     abbrev="Agt",
    ...     definition=AnnotatedText.parse("The entity that performs an action"),
    ...     core_type="Core",
    ...     bg_color="FF0000",
    ...     fg_color="FFFFFF"
    ... )
    >>> print(fe.is_core())
    True
    """

    id: int = Field(ge=1, description="Unique FE identifier")
    name: FEName = Field(description="Frame element name")
    abbrev: FEAbbrev = Field(description="FE abbreviation")
    definition: AnnotatedText = Field(description="Definition with markup")
    core_type: CoreType = Field(description="Core classification")
    bg_color: str = Field(description="Background color (6-digit hex)")
    fg_color: str = Field(description="Foreground color (6-digit hex)")
    requires_fe: list[FEName] = Field(default_factory=list, description="FE names this FE requires")
    excludes_fe: list[FEName] = Field(default_factory=list, description="FE names this FE excludes")
    semtype_refs: list[SemTypeID] = Field(
        default_factory=list, description="Semantic type references"
    )
    created_by: Username | None = Field(None, description="Creator username")
    created_date: datetime | None = Field(None, description="Creation timestamp")

    @field_validator("name")
    @classmethod
    def validate_fe_name(cls, v: str) -> str:
        """Validate FE name format."""
        return validate_pattern(v, FE_NAME_PATTERN, "frame element name")

    @field_validator("abbrev")
    @classmethod
    def validate_abbrev(cls, v: str) -> str:
        """Validate FE abbreviation format."""
        return validate_pattern(v, FE_ABBREV_PATTERN, "FE abbreviation")

    @field_validator("bg_color", "fg_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        return validate_hex_color(v)

    @field_validator("created_by")
    @classmethod
    def validate_created_by(cls, v: str | None) -> str | None:
        """Validate creator username format."""
        if v is not None:
            return validate_pattern(v, USERNAME_PATTERN, "username")
        return v

    @field_validator("requires_fe", "excludes_fe")
    @classmethod
    def validate_fe_lists(cls, v: list[str]) -> list[str]:
        """Validate FE name lists."""
        for fe_name in v:
            if not re.match(FE_NAME_PATTERN, fe_name):
                msg = f"Invalid FE name in list: {fe_name}"
                raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_fe_constraints(self) -> Self:
        """Validate FE constraint consistency."""
        # Check for overlap between requires and excludes
        overlap = set(self.requires_fe) & set(self.excludes_fe)
        if overlap:
            msg = f"FE cannot both require and exclude: {overlap}"
            raise ValueError(msg)

        # Check that FE doesn't require or exclude itself
        if self.name in self.requires_fe:
            msg = f"FE cannot require itself: {self.name}"
            raise ValueError(msg)
        if self.name in self.excludes_fe:
            msg = f"FE cannot exclude itself: {self.name}"
            raise ValueError(msg)

        return self

    def has_dependencies(self) -> bool:
        """Check if this FE has dependency constraints.

        Returns
        -------
        bool
            True if the FE has requires or excludes constraints.
        """
        return len(self.requires_fe) > 0 or len(self.excludes_fe) > 0

    def is_core(self) -> bool:
        """Check if this is a core frame element.

        Returns
        -------
        bool
            True if core_type is "Core" or "Core-Unexpressed".
        """
        return self.core_type in ("Core", "Core-Unexpressed")

    def conflicts_with(self, other_fe_name: str) -> bool:
        """Check if this FE conflicts with another.

        Parameters
        ----------
        other_fe_name : str
            Name of the other FE to check.

        Returns
        -------
        bool
            True if this FE excludes the other FE.
        """
        return other_fe_name in self.excludes_fe


class Frame(GlazingBaseModel):
    """A FrameNet frame representing a schematic situation.

    Parameters
    ----------
    id : FrameID
        Unique frame identifier.
    name : FrameName
        Human-readable frame name.
    definition : AnnotatedText
        Frame definition with embedded markup.
    frame_elements : list[FrameElement]
        Core and non-core frame elements.
    created_by : Username | None, default=None
        Username of frame creator.
    created_date : datetime | None, default=None
        Frame creation timestamp.
    modified_date : datetime | None, default=None
        Last modification timestamp.

    Methods
    -------
    get_fe_by_name(name)
        Get frame element by name.
    get_core_elements()
        Get all core frame elements.
    get_peripheral_elements()
        Get all peripheral frame elements.
    validate_fe_constraints(fe_set)
        Validate a set of FEs against constraints.

    Examples
    --------
    >>> frame = Frame(
    ...     id=2031,
    ...     name="Abandonment",
    ...     definition=AnnotatedText.parse("An <fex>Agent</fex> leaves behind..."),
    ...     frame_elements=[]
    ... )
    >>> print(frame.name)
    'Abandonment'
    """

    id: FrameID = Field(description="Unique frame identifier")
    name: FrameName = Field(description="Human-readable frame name")
    definition: AnnotatedText = Field(description="Frame definition with markup")
    frame_elements: list[FrameElement] = Field(description="Frame elements")
    created_by: Username | None = Field(None, description="Frame creator username")
    created_date: datetime | None = Field(None, description="Creation timestamp")
    modified_date: datetime | None = Field(None, description="Modification timestamp")

    @field_validator("name")
    @classmethod
    def validate_frame_name(cls, v: str) -> str:
        """Validate frame name format."""
        return validate_pattern(v, FRAME_NAME_PATTERN, "frame name")

    @field_validator("created_by")
    @classmethod
    def validate_created_by(cls, v: str | None) -> str | None:
        """Validate creator username format."""
        if v is not None:
            return validate_pattern(v, USERNAME_PATTERN, "username")
        return v

    @model_validator(mode="after")
    def validate_frame_elements(self) -> Self:
        """Validate frame element consistency."""
        fe_names = [fe.name for fe in self.frame_elements]

        # Check for duplicate FE names
        if len(fe_names) != len(set(fe_names)):
            duplicates = [name for name in fe_names if fe_names.count(name) > 1]
            msg = f"Duplicate frame element names: {set(duplicates)}"
            raise ValueError(msg)

        # Validate FE constraint references
        for fe in self.frame_elements:
            for required_fe in fe.requires_fe:
                if required_fe not in fe_names:
                    msg = f"FE '{fe.name}' requires unknown FE '{required_fe}'"
                    raise ValueError(msg)
            for excluded_fe in fe.excludes_fe:
                if excluded_fe not in fe_names:
                    msg = f"FE '{fe.name}' excludes unknown FE '{excluded_fe}'"
                    raise ValueError(msg)

        return self

    def get_fe_by_name(self, name: str) -> FrameElement | None:
        """Get frame element by name.

        Parameters
        ----------
        name : str
            Name of the frame element.

        Returns
        -------
        FrameElement | None
            The frame element, or None if not found.
        """
        for fe in self.frame_elements:
            if fe.name == name:
                return fe
        return None

    def get_core_elements(self) -> list[FrameElement]:
        """Get all core frame elements.

        Returns
        -------
        list[FrameElement]
            Frame elements with core_type "Core" or "Core-Unexpressed".
        """
        return [fe for fe in self.frame_elements if fe.is_core()]

    def get_peripheral_elements(self) -> list[FrameElement]:
        """Get all peripheral frame elements.

        Returns
        -------
        list[FrameElement]
            Frame elements with core_type "Peripheral" or "Extra-Thematic".
        """
        return [fe for fe in self.frame_elements if not fe.is_core()]

    def validate_fe_constraints(self, fe_names: list[str]) -> dict[str, list[str]]:
        """Validate a set of FEs against dependency constraints.

        Parameters
        ----------
        fe_names : list[str]
            Names of FEs to validate.

        Returns
        -------
        dict[str, list[str]]
            Dictionary with 'errors' and 'warnings' keys containing
            lists of constraint violation messages.
        """
        errors: list[str] = []
        warnings: list[str] = []
        fe_set = set(fe_names)

        for fe_name in fe_names:
            fe = self.get_fe_by_name(fe_name)
            if not fe:
                errors.append(f"Unknown frame element: {fe_name}")
                continue

            # Check requires constraints
            missing_required = [req for req in fe.requires_fe if req not in fe_set]
            if missing_required:
                errors.append(f"FE '{fe_name}' requires missing FEs: {missing_required}")

            # Check excludes constraints
            conflicting = [exc for exc in fe.excludes_fe if exc in fe_set]
            if conflicting:
                errors.append(f"FE '{fe_name}' conflicts with present FEs: {conflicting}")

        return {"errors": errors, "warnings": warnings}


class FERelation(GlazingBaseModel):
    """FE mapping between related frames with alignment metadata.

    Parameters
    ----------
    sub_fe_id : int | None, default=None
        ID of the sub-frame FE.
    sub_fe_name : FEName | None, default=None
        Name of the sub-frame FE.
    super_fe_id : int | None, default=None
        ID of the super-frame FE.
    super_fe_name : FEName | None, default=None
        Name of the super-frame FE.
    relation_type : FrameRelationSubType | None, default=None
        Type of FE relation.
    alignment_confidence : MappingConfidenceScore | None, default=None
        Confidence in the alignment.
    semantic_similarity : MappingConfidenceScore | None, default=None
        Semantic similarity score.
    syntactic_similarity : MappingConfidenceScore | None, default=None
        Syntactic similarity score.
    mapping_notes : str | None, default=None
        Notes about the mapping.

    Methods
    -------
    is_inheritance()
        Check if this is an inheritance relation.
    is_equivalence()
        Check if FEs are equivalent.
    get_combined_score()
        Get combined confidence score.

    Examples
    --------
    >>> fe_rel = FERelation(
    ...     sub_fe_name="Giver",
    ...     super_fe_name="Agent",
    ...     relation_type="Inheritance",
    ...     alignment_confidence=0.95
    ... )
    >>> print(fe_rel.is_inheritance())
    True
    """

    sub_fe_id: int | None = Field(None, description="Sub-frame FE ID")
    sub_fe_name: FEName | None = Field(None, description="Sub-frame FE name")
    super_fe_id: int | None = Field(None, description="Super-frame FE ID")
    super_fe_name: FEName | None = Field(None, description="Super-frame FE name")
    relation_type: FrameRelationSubType | None = Field(None, description="Relation type")
    alignment_confidence: MappingConfidenceScore | None = Field(
        None, description="Alignment confidence"
    )
    semantic_similarity: MappingConfidenceScore | None = Field(
        None, description="Semantic similarity score"
    )
    syntactic_similarity: MappingConfidenceScore | None = Field(
        None, description="Syntactic similarity score"
    )
    mapping_notes: str | None = Field(None, description="Mapping notes")

    @field_validator("sub_fe_name", "super_fe_name")
    @classmethod
    def validate_fe_names(cls, v: str | None) -> str | None:
        """Validate FE name format."""
        if v is not None:
            return validate_pattern(v, FE_NAME_PATTERN, "FE name")
        return v

    @model_validator(mode="after")
    def validate_fe_relation(self) -> Self:
        """Validate FE relation completeness."""
        if not any([self.sub_fe_id, self.sub_fe_name]):
            raise ValueError("Either sub_fe_id or sub_fe_name must be provided")
        if not any([self.super_fe_id, self.super_fe_name]):
            raise ValueError("Either super_fe_id or super_fe_name must be provided")
        return self

    def is_inheritance(self) -> bool:
        """Check if this is an inheritance relation.

        Returns
        -------
        bool
            True if relation_type is "Inheritance".
        """
        return self.relation_type == "Inheritance"

    def is_equivalence(self) -> bool:
        """Check if FEs are equivalent.

        Returns
        -------
        bool
            True if relation_type is "Equivalence".
        """
        return self.relation_type == "Equivalence"

    def get_combined_score(self) -> float:
        """Get combined confidence score.

        Combines alignment confidence with similarity scores.

        Returns
        -------
        float
            Combined confidence score (0.0-1.0).
        """
        scores = []
        if self.alignment_confidence is not None:
            scores.append(self.alignment_confidence)
        if self.semantic_similarity is not None:
            scores.append(self.semantic_similarity)
        if self.syntactic_similarity is not None:
            scores.append(self.syntactic_similarity)

        return sum(scores) / len(scores) if scores else 0.5


class FrameRelation(GlazingBaseModel):
    """Relationship between frames.

    Parameters
    ----------
    id : int | None, default=None
        Relation identifier.
    type : FrameRelationType
        Type of frame relation.
    sub_frame_id : FrameID | None, default=None
        ID of the sub-frame.
    sub_frame_name : FrameName | None, default=None
        Name of the sub-frame.
    super_frame_id : FrameID | None, default=None
        ID of the super-frame.
    super_frame_name : FrameName | None, default=None
        Name of the super-frame.
    fe_relations : list[FERelation], default=[]
        FE-level mappings for this relation.

    Methods
    -------
    is_inheritance()
        Check if this is an inheritance relation.
    get_fe_mapping(sub_fe_name)
        Get FE mapping for a sub-frame FE.

    Examples
    --------
    >>> frame_rel = FrameRelation(
    ...     type="Inherits from",
    ...     sub_frame_name="Giving",
    ...     super_frame_name="Transfer",
    ...     fe_relations=[]
    ... )
    >>> print(frame_rel.is_inheritance())
    True
    """

    id: int | None = Field(None, description="Relation identifier")
    type: FrameRelationType = Field(description="Frame relation type")
    sub_frame_id: FrameID | None = Field(None, description="Sub-frame ID")
    sub_frame_name: FrameName | None = Field(None, description="Sub-frame name")
    super_frame_id: FrameID | None = Field(None, description="Super-frame ID")
    super_frame_name: FrameName | None = Field(None, description="Super-frame name")
    fe_relations: list[FERelation] = Field(default_factory=list, description="FE-level mappings")

    @field_validator("sub_frame_name", "super_frame_name")
    @classmethod
    def validate_frame_names(cls, v: str | None) -> str | None:
        """Validate frame name format."""
        if v is not None:
            return validate_pattern(v, FRAME_NAME_PATTERN, "frame name")
        return v

    def is_inheritance(self) -> bool:
        """Check if this is an inheritance relation.

        Returns
        -------
        bool
            True if type is "Inherits from" or "Is Inherited by".
        """
        return self.type in ("Inherits from", "Is Inherited by")

    def get_fe_mapping(self, sub_fe_name: str) -> FERelation | None:
        """Get FE mapping for a sub-frame FE.

        Parameters
        ----------
        sub_fe_name : str
            Name of the sub-frame FE.

        Returns
        -------
        FERelation | None
            The FE relation, or None if not found.
        """
        for fe_rel in self.fe_relations:
            if fe_rel.sub_fe_name == sub_fe_name:
                return fe_rel
        return None


class SemanticType(GlazingBaseModel):
    """Semantic type in the FrameNet type system.

    Parameters
    ----------
    id : SemTypeID
        Semantic type identifier.
    name : str
        Type name.
    abbrev : str
        Type abbreviation.
    definition : str
        Type definition.
    super_type_id : SemTypeID | None, default=None
        Parent type ID.
    super_type_name : str | None, default=None
        Parent type name.
    root_type_id : SemTypeID | None, default=None
        Root type ID.
    root_type_name : str | None, default=None
        Root type name.

    Methods
    -------
    is_root_type()
        Check if this is a root semantic type.
    get_depth()
        Get depth in the type hierarchy.

    Examples
    --------
    >>> sem_type = SemanticType(
    ...     id=123,
    ...     name="Sentient",
    ...     abbrev="sent",
    ...     definition="Capable of perception and feeling"
    ... )
    >>> print(sem_type.is_root_type())
    True
    """

    id: SemTypeID = Field(description="Semantic type identifier")
    name: str = Field(min_length=1, description="Type name")
    abbrev: str = Field(min_length=1, description="Type abbreviation")
    definition: str = Field(min_length=1, description="Type definition")
    super_type_id: SemTypeID | None = Field(None, description="Parent type ID")
    super_type_name: str | None = Field(None, description="Parent type name")
    root_type_id: SemTypeID | None = Field(None, description="Root type ID")
    root_type_name: str | None = Field(None, description="Root type name")

    @model_validator(mode="after")
    def validate_type_hierarchy(self) -> Self:
        """Validate semantic type hierarchy consistency."""
        # If super_type_id is provided, super_type_name should also be provided
        if self.super_type_id is not None and self.super_type_name is None:
            raise ValueError("super_type_name required when super_type_id is provided")
        if self.super_type_name is not None and self.super_type_id is None:
            raise ValueError("super_type_id required when super_type_name is provided")

        # Same for root type
        if self.root_type_id is not None and self.root_type_name is None:
            raise ValueError("root_type_name required when root_type_id is provided")
        if self.root_type_name is not None and self.root_type_id is None:
            raise ValueError("root_type_id required when root_type_name is provided")

        return self

    def is_root_type(self) -> bool:
        """Check if this is a root semantic type.

        Returns
        -------
        bool
            True if this type has no super type.
        """
        return self.super_type_id is None

    def get_depth(self) -> int:
        """Get depth in the type hierarchy.

        Returns
        -------
        int
            Depth (0 for root types, 1 for direct children, etc.).
        """
        if self.is_root_type():
            return 0
        # Note: This would need access to the full type hierarchy to compute accurately
        # For now, return estimated depth based on available information
        return 1 if self.super_type_id else 0


class FrameIndexEntry(GlazingBaseModel):
    """Entry in the frame index file.

    Parameters
    ----------
    id : FrameID
        Frame identifier.
    name : FrameName
        Frame name.
    modified_date : datetime
        Last modification date.

    Examples
    --------
    >>> entry = FrameIndexEntry(
    ...     id=2031,
    ...     name="Abandonment",
    ...     modified_date=datetime.now()
    ... )
    >>> print(entry.name)
    'Abandonment'
    """

    id: FrameID = Field(description="Frame identifier")
    name: FrameName = Field(description="Frame name")
    modified_date: datetime = Field(description="Last modification date", alias="mDate")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate frame name format."""
        return validate_pattern(v, FRAME_NAME_PATTERN, "frame name")
