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
    LEXEME_NAME_PATTERN,
    LU_NAME_PATTERN,
    USERNAME_PATTERN,
    AnnotationSetID,
    AnnotationStatus,
    CoreType,
    CorpusID,
    DocumentID,
    FEAbbrev,
    FEName,
    FrameID,
    FrameName,
    FrameNetPOS,
    FrameRelationSubType,
    FrameRelationType,
    GrammaticalFunction,
    LabelID,
    LayerType,
    LexicalUnitID,
    LexicalUnitName,
    MarkupType,
    PhraseType,
    SemTypeID,
    SentenceID,
    Username,
)
from glazing.types import MappingConfidenceScore


class TextAnnotation(GlazingBaseModel):
    """An annotation within text (FE reference, target, example, etc.).

    Attributes
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
    text: str = Field(description="The annotated text span")  # Allow empty text

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate FE reference names."""
        if v is not None and not re.match(FE_NAME_PATTERN, v):
            msg = f"Invalid FE name format: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_positions(self) -> Self:
        """Validate that end position is at or after start position."""
        if self.end < self.start:
            msg = f"End position ({self.end}) must be at or after start position ({self.start})"
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

    Attributes
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

    Attributes
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

    Attributes
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
    lexical_units: list[LexicalUnit] = Field(
        default_factory=list, description="Lexical units in this frame"
    )
    frame_relations: list[FrameRelation] = Field(
        default_factory=list, description="Relations to other frames"
    )
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

    Attributes
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

    Attributes
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

    Attributes
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

    Attributes
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


class SemTypeRef(GlazingBaseModel):
    """Reference to a semantic type with name and ID.

    Attributes
    ----------
    name : str
        Semantic type name.
    id : SemTypeID
        Semantic type ID.

    Methods
    -------
    is_valid_name()
        Check if the name follows semantic type naming conventions.

    Examples
    --------
    >>> ref = SemTypeRef(name="Sentient", id=123)
    >>> print(ref.name)
    'Sentient'
    """

    name: str = Field(min_length=1, description="Semantic type name")
    id: SemTypeID = Field(description="Semantic type ID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate semantic type name format."""
        # Allow flexible semantic type names - some may have spaces, hyphens, etc.
        if not re.match(r"^[A-Z][A-Za-z0-9_\s-]*$", v):
            # Log unusual formats but don't fail validation
            pass
        return v

    def is_valid_name(self) -> bool:
        """Check if the name follows standard semantic type naming conventions.

        Returns
        -------
        bool
            True if name follows standard pattern.
        """
        return bool(re.match(r"^[A-Z][A-Za-z0-9_]*$", self.name))


class SentenceCount(GlazingBaseModel):
    """Frequency counts for annotated sentences.

    Attributes
    ----------
    annotated : int, default=0
        Number of annotated sentences.
    total : int, default=0
        Total number of sentences.

    Methods
    -------
    get_annotation_rate()
        Calculate the annotation completion rate.
    has_annotations()
        Check if any sentences are annotated.

    Examples
    --------
    >>> count = SentenceCount(annotated=50, total=100)
    >>> print(count.get_annotation_rate())
    0.5
    """

    annotated: int = Field(0, ge=0, description="Number of annotated sentences")
    total: int = Field(0, ge=0, description="Total number of sentences")

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        """Validate that annotated count doesn't exceed total."""
        if self.annotated > self.total:
            msg = f"Annotated count ({self.annotated}) cannot exceed total ({self.total})"
            raise ValueError(msg)
        return self

    def get_annotation_rate(self) -> float:
        """Calculate the annotation completion rate.

        Returns
        -------
        float
            Completion rate (0.0-1.0), or 0.0 if no total sentences.
        """
        return self.annotated / self.total if self.total > 0 else 0.0

    def has_annotations(self) -> bool:
        """Check if any sentences are annotated.

        Returns
        -------
        bool
            True if annotated count > 0.
        """
        return self.annotated > 0


class Lexeme(GlazingBaseModel):
    """A lexical form in a lexical unit.

    Attributes
    ----------
    name : str
        The word form (validated pattern).
    pos : FrameNetPOS
        Part of speech tag.
    headword : bool, default=False
        True if this is the head word of the LU.
    break_before : bool, default=False
        True if there should be a break before this lexeme.
    order : int, default=1
        Order position in multi-word LUs.

    Methods
    -------
    is_headword()
        Check if this is the headword.

    Examples
    --------
    >>> lexeme = Lexeme(name="abandon", pos="V", headword=True)
    >>> print(lexeme.is_headword())
    True
    """

    name: str = Field(description="The word form")
    pos: FrameNetPOS = Field(description="Part of speech")
    headword: bool = Field(default=False, description="True if this is the head word")
    break_before: bool = Field(
        default=False, alias="breakBefore", description="Break before this lexeme"
    )
    order: int = Field(1, ge=1, description="Order position in multi-word LUs")

    @field_validator("name")
    @classmethod
    def validate_lexeme_name(cls, v: str) -> str:
        """Validate lexeme name (individual word form)."""
        return validate_pattern(v, LEXEME_NAME_PATTERN, "lexeme name")

    def is_headword(self) -> bool:
        """Check if this is the headword.

        Returns
        -------
        bool
            True if this lexeme is marked as headword.
        """
        return self.headword


class Label(GlazingBaseModel):
    """An annotation label on a text span.

    Attributes
    ----------
    id : LabelID | None, default=None
        Label identifier.
    name : str
        Label name (FE name, GF type, PT type, etc.).
    start : int
        Start position in sentence.
    end : int
        End position in sentence.
    fe_id : int | None, default=None
        Frame element ID for FE labels.
    is_instantiated_null : bool, default=False
        True for null instantiation labels.

    Methods
    -------
    get_span_length()
        Get the length of the labeled span.
    is_null_instantiation()
        Check if this is a null instantiation.
    overlaps_with(other)
        Check if this label overlaps with another.

    Examples
    --------
    >>> label = Label(name="Agent", start=0, end=5)
    >>> print(label.get_span_length())
    5
    """

    id: LabelID | None = Field(None, description="Label identifier")
    name: str = Field(min_length=1, description="Label name")
    start: int = Field(ge=0, description="Start position in sentence")
    end: int = Field(ge=0, description="End position in sentence")
    fe_id: int | None = Field(None, description="Frame element ID for FE labels")
    is_instantiated_null: bool = Field(
        default=False, alias="itype", description="Null instantiation flag"
    )

    @model_validator(mode="after")
    def validate_positions(self) -> Self:
        """Validate that end position is at or after start position."""
        if self.end < self.start:
            msg = f"End position ({self.end}) must be at or after start position ({self.start})"
            raise ValueError(msg)
        return self

    def get_span_length(self) -> int:
        """Get the length of the labeled span.

        Returns
        -------
        int
            Length of the span.
        """
        return self.end - self.start

    def is_null_instantiation(self) -> bool:
        """Check if this is a null instantiation.

        Returns
        -------
        bool
            True if is_instantiated_null is True.
        """
        return self.is_instantiated_null

    def overlaps_with(self, other: Label) -> bool:
        """Check if this label overlaps with another.

        Parameters
        ----------
        other : Label
            The other label to check.

        Returns
        -------
        bool
            True if the labels overlap.
        """
        return not (self.end <= other.start or other.end <= self.start)


class AnnotationLayer(GlazingBaseModel):
    """A layer of annotation (FE, GF, PT, Target, etc.).

    Attributes
    ----------
    name : LayerType
        Layer type name.
    rank : int, default=1
        Layer rank/priority.
    labels : list[Label]
        Labels in this layer.

    Methods
    -------
    get_labels_by_name(name)
        Get all labels with a specific name.
    has_overlapping_labels()
        Check if any labels in this layer overlap.
    get_label_count()
        Get the number of labels in this layer.

    Examples
    --------
    >>> layer = AnnotationLayer(name="FE", labels=[...])
    >>> print(layer.get_label_count())
    3
    """

    name: LayerType = Field(description="Layer type name")
    rank: int = Field(1, ge=1, description="Layer rank/priority")
    labels: list[Label] = Field(default_factory=list, description="Labels in this layer")

    def get_labels_by_name(self, name: str) -> list[Label]:
        """Get all labels with a specific name.

        Parameters
        ----------
        name : str
            The label name to search for.

        Returns
        -------
        list[Label]
            List of matching labels.
        """
        return [label for label in self.labels if label.name == name]

    def has_overlapping_labels(self) -> bool:
        """Check if any labels in this layer overlap.

        Returns
        -------
        bool
            True if any labels overlap.
        """
        for i, label1 in enumerate(self.labels):
            for label2 in self.labels[i + 1 :]:
                if label1.overlaps_with(label2):
                    return True
        return False

    def get_label_count(self) -> int:
        """Get the number of labels in this layer.

        Returns
        -------
        int
            Number of labels.
        """
        return len(self.labels)


class AnnotationSet(GlazingBaseModel):
    """A set of annotations on a sentence.

    Attributes
    ----------
    id : AnnotationSetID
        Annotation set identifier.
    status : AnnotationStatus
        Annotation completion status.
    sentence_id : SentenceID
        ID of the annotated sentence.
    layers : list[AnnotationLayer]
        Annotation layers in this set.
    created_by : Username | None, default=None
        Creator username.
    created_date : datetime | None, default=None
        Creation timestamp.

    Methods
    -------
    get_layer_by_name(name)
        Get annotation layer by name.
    get_fe_layer()
        Get the frame element layer.
    get_target_layer()
        Get the target layer.
    has_layer(layer_name)
        Check if a specific layer exists.

    Examples
    --------
    >>> anno_set = AnnotationSet(
    ...     id=123,
    ...     status="MANUAL",
    ...     sentence_id=456,
    ...     layers=[...]
    ... )
    """

    id: AnnotationSetID = Field(description="Annotation set identifier")
    status: AnnotationStatus = Field(description="Annotation completion status")
    sentence_id: SentenceID = Field(description="ID of the annotated sentence")
    layers: list[AnnotationLayer] = Field(default_factory=list, description="Annotation layers")
    created_by: Username | None = Field(None, alias="cBy", description="Creator username")
    created_date: datetime | None = Field(None, alias="cDate", description="Creation timestamp")

    @field_validator("created_by")
    @classmethod
    def validate_created_by(cls, v: str | None) -> str | None:
        """Validate creator username format."""
        if v is not None:
            return validate_pattern(v, USERNAME_PATTERN, "username")
        return v

    def get_layer_by_name(self, name: LayerType) -> AnnotationLayer | None:
        """Get annotation layer by name.

        Parameters
        ----------
        name : LayerType
            The layer name to find.

        Returns
        -------
        AnnotationLayer | None
            The layer, or None if not found.
        """
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def get_fe_layer(self) -> AnnotationLayer | None:
        """Get the frame element layer.

        Returns
        -------
        AnnotationLayer | None
            The FE layer, or None if not found.
        """
        return self.get_layer_by_name("FE")

    def get_target_layer(self) -> AnnotationLayer | None:
        """Get the target layer.

        Returns
        -------
        AnnotationLayer | None
            The Target layer, or None if not found.
        """
        return self.get_layer_by_name("Target")

    def has_layer(self, layer_name: LayerType) -> bool:
        """Check if a specific layer exists.

        Parameters
        ----------
        layer_name : LayerType
            The layer name to check.

        Returns
        -------
        bool
            True if the layer exists.
        """
        return self.get_layer_by_name(layer_name) is not None


class Sentence(GlazingBaseModel):
    """A sentence with its annotations.

    Attributes
    ----------
    id : SentenceID
        Sentence identifier.
    text : str
        The sentence text.
    paragraph_no : int | None, default=None
        Paragraph number in document.
    sentence_no : int | None, default=None
        Sentence number in paragraph.
    doc_id : DocumentID | None, default=None
        Document identifier.
    corpus_id : CorpusID | None, default=None
        Corpus identifier.
    apos : int | None, default=None
        Absolute position in document.
    annotation_sets : list[AnnotationSet], default=[]
        Annotation sets for this sentence.

    Methods
    -------
    get_annotation_set_by_id(anno_id)
        Get annotation set by ID.
    has_annotations()
        Check if sentence has any annotations.
    get_annotation_count()
        Get number of annotation sets.

    Examples
    --------
    >>> sentence = Sentence(
    ...     id=123,
    ...     text="John abandoned the car.",
    ...     paragraph_no=1,
    ...     sentence_no=1
    ... )
    """

    id: SentenceID = Field(description="Sentence identifier")
    text: str = Field(min_length=1, description="The sentence text")
    paragraph_no: int | None = Field(None, alias="paragNo", description="Paragraph number")
    sentence_no: int | None = Field(None, alias="sentNo", description="Sentence number")
    doc_id: DocumentID | None = Field(None, alias="docID", description="Document identifier")
    corpus_id: CorpusID | None = Field(None, alias="corpID", description="Corpus identifier")
    apos: int | None = Field(None, description="Absolute position in document")
    annotation_sets: list[AnnotationSet] = Field(
        default_factory=list, description="Annotation sets"
    )

    def get_annotation_set_by_id(self, anno_id: AnnotationSetID) -> AnnotationSet | None:
        """Get annotation set by ID.

        Parameters
        ----------
        anno_id : AnnotationSetID
            The annotation set ID to find.

        Returns
        -------
        AnnotationSet | None
            The annotation set, or None if not found.
        """
        for anno_set in self.annotation_sets:
            if anno_set.id == anno_id:
                return anno_set
        return None

    def has_annotations(self) -> bool:
        """Check if sentence has any annotations.

        Returns
        -------
        bool
            True if there are annotation sets.
        """
        return len(self.annotation_sets) > 0

    def get_annotation_count(self) -> int:
        """Get number of annotation sets.

        Returns
        -------
        int
            Number of annotation sets.
        """
        return len(self.annotation_sets)


class ValenceUnit(GlazingBaseModel):
    """A valence unit in a realization pattern.

    Attributes
    ----------
    gf : GrammaticalFunction | str
        Grammatical function (can be empty string or special values).
    pt : PhraseType | str
        Phrase type or special values.
    fe : str
        Frame element name.

    Methods
    -------
    is_null_instantiation()
        Check if this represents null instantiation.
    has_grammatical_function()
        Check if a grammatical function is specified.

    Examples
    --------
    >>> unit = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
    >>> print(unit.has_grammatical_function())
    True
    """

    gf: GrammaticalFunction | str = Field(alias="GF", description="Grammatical function")
    pt: PhraseType | str = Field(alias="PT", description="Phrase type")
    fe: str = Field(alias="FE", min_length=1, description="Frame element name")

    @field_validator("gf")
    @classmethod
    def validate_gf(cls, v: str) -> str:
        """Validate grammatical function."""
        # GF can be empty string or special null instantiation values
        if v == "" or v in ["CNI", "INI", "DNI", "NI"]:
            return v
        # Otherwise should be a valid GrammaticalFunction or pass through
        return v

    @field_validator("pt")
    @classmethod
    def validate_pt(cls, v: str) -> str:
        """Validate phrase type."""
        # PT can be special null instantiation values
        if v in ["CNI", "INI", "DNI", "NI", "--", "unknown"]:
            return v
        # Otherwise should be a valid PhraseType or pass through
        return v

    def is_null_instantiation(self) -> bool:
        """Check if this represents null instantiation.

        Returns
        -------
        bool
            True if this is a null instantiation pattern.
        """
        return self.pt in ["CNI", "INI", "DNI", "NI"]

    def has_grammatical_function(self) -> bool:
        """Check if a grammatical function is specified.

        Returns
        -------
        bool
            True if GF is not empty.
        """
        return self.gf != ""


class ValenceRealizationPattern(GlazingBaseModel):
    """A specific realization pattern for an FE.

    Attributes
    ----------
    valence_units : list[ValenceUnit]
        Valence units in this pattern.
    anno_set_ids : list[int]
        Annotation set IDs supporting this pattern.
    total : int
        Frequency count for this pattern.

    Methods
    -------
    get_pattern_signature()
        Get a string signature for this pattern.
    has_null_instantiation()
        Check if pattern includes null instantiation.

    Examples
    --------
    >>> pattern = ValenceRealizationPattern(
    ...     valence_units=[ValenceUnit(gf="Ext", pt="NP", fe="Agent")],
    ...     anno_set_ids=[1, 2, 3],
    ...     total=3
    ... )
    """

    valence_units: list[ValenceUnit] = Field(description="Valence units in pattern")
    anno_set_ids: list[int] = Field(description="Supporting annotation set IDs")
    total: int = Field(ge=1, description="Frequency count")

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        """Validate pattern consistency."""
        if self.total > 0 and not self.anno_set_ids:
            # Allow empty anno_set_ids if total is provided
            pass
        return self

    def get_pattern_signature(self) -> str:
        """Get a string signature for this pattern.

        Returns
        -------
        str
            Pattern signature like "Ext:NP:Agent|Obj:NP:Theme".
        """
        units = []
        for unit in self.valence_units:
            units.append(f"{unit.gf}:{unit.pt}:{unit.fe}")
        return "|".join(units)

    def has_null_instantiation(self) -> bool:
        """Check if pattern includes null instantiation.

        Returns
        -------
        bool
            True if any valence unit is null instantiation.
        """
        return any(unit.is_null_instantiation() for unit in self.valence_units)


class FERealization(GlazingBaseModel):
    """How a frame element is realized syntactically.

    Attributes
    ----------
    fe_name : str
        Frame element name.
    total : int
        Total occurrences of this FE.
    patterns : list[ValenceRealizationPattern], default=[]
        Realization patterns for this FE.

    Methods
    -------
    get_most_frequent_pattern()
        Get the most frequent realization pattern.
    has_patterns()
        Check if this FE has realization patterns.
    get_pattern_count()
        Get number of realization patterns.

    Examples
    --------
    >>> fe_real = FERealization(
    ...     fe_name="Agent",
    ...     total=10,
    ...     patterns=[...]
    ... )
    """

    fe_name: str = Field(min_length=1, description="Frame element name")
    total: int = Field(ge=0, description="Total occurrences")
    patterns: list[ValenceRealizationPattern] = Field(
        default_factory=list, description="Realization patterns"
    )

    @field_validator("fe_name")
    @classmethod
    def validate_fe_name(cls, v: str) -> str:
        """Validate FE name format."""
        return validate_pattern(v, FE_NAME_PATTERN, "FE name")

    def get_most_frequent_pattern(self) -> ValenceRealizationPattern | None:
        """Get the most frequent realization pattern.

        Returns
        -------
        ValenceRealizationPattern | None
            Most frequent pattern, or None if no patterns.
        """
        if not self.patterns:
            return None
        return max(self.patterns, key=lambda p: p.total)

    def has_patterns(self) -> bool:
        """Check if this FE has realization patterns.

        Returns
        -------
        bool
            True if patterns exist.
        """
        return len(self.patterns) > 0

    def get_pattern_count(self) -> int:
        """Get number of realization patterns.

        Returns
        -------
        int
            Number of patterns.
        """
        return len(self.patterns)


class FEGroupRealization(GlazingBaseModel):
    """Realization of grouped FEs in a pattern.

    Attributes
    ----------
    fe_names : list[str]
        Frame element names in this group.
    grammatical_function : GrammaticalFunction
        Grammatical function for the group.
    phrase_type : PhraseType
        Phrase type for the group.

    Methods
    -------
    contains_fe(fe_name)
        Check if group contains a specific FE.
    get_fe_count()
        Get number of FEs in group.

    Examples
    --------
    >>> group = FEGroupRealization(
    ...     fe_names=["Agent", "Theme"],
    ...     grammatical_function="Ext",
    ...     phrase_type="NP"
    ... )
    """

    fe_names: list[str] = Field(min_length=1, description="FE names in group")
    grammatical_function: GrammaticalFunction = Field(description="Grammatical function")
    phrase_type: PhraseType = Field(description="Phrase type")

    @field_validator("fe_names")
    @classmethod
    def validate_fe_names(cls, v: list[str]) -> list[str]:
        """Validate FE names in group."""
        for fe_name in v:
            if not re.match(FE_NAME_PATTERN, fe_name):
                msg = f"Invalid FE name in group: {fe_name}"
                raise ValueError(msg)
        return v

    def contains_fe(self, fe_name: str) -> bool:
        """Check if group contains a specific FE.

        Parameters
        ----------
        fe_name : str
            FE name to check.

        Returns
        -------
        bool
            True if FE is in this group.
        """
        return fe_name in self.fe_names

    def get_fe_count(self) -> int:
        """Get number of FEs in group.

        Returns
        -------
        int
            Number of FEs.
        """
        return len(self.fe_names)


class ValenceAnnotationPattern(GlazingBaseModel):
    """A specific valence pattern with annotated examples.

    Attributes
    ----------
    anno_sets : list[AnnotationSetID]
        References to annotation sets.
    pattern : list[FEGroupRealization]
        FE group realizations in this pattern.

    Methods
    -------
    get_annotation_count()
        Get number of annotation sets.
    get_fe_groups()
        Get all FE groups in pattern.

    Examples
    --------
    >>> pattern = ValenceAnnotationPattern(
    ...     anno_sets=[1, 2, 3],
    ...     pattern=[FEGroupRealization(...)]
    ... )
    """

    anno_sets: list[AnnotationSetID] = Field(description="Annotation set references")
    pattern: list[FEGroupRealization] = Field(description="FE group realizations")

    def get_annotation_count(self) -> int:
        """Get number of annotation sets.

        Returns
        -------
        int
            Number of annotation sets.
        """
        return len(self.anno_sets)

    def get_fe_groups(self) -> list[FEGroupRealization]:
        """Get all FE groups in pattern.

        Returns
        -------
        list[FEGroupRealization]
            List of FE group realizations.
        """
        return self.pattern


class ValencePattern(GlazingBaseModel):
    """Syntactic valence pattern for a lexical unit.

    Attributes
    ----------
    total_annotated : int
        Total number of annotated instances.
    fe_realizations : list[FERealization]
        How frame elements are realized.
    patterns : list[ValenceAnnotationPattern]
        Specific valence patterns with examples.

    Methods
    -------
    get_fe_realization(fe_name)
        Get realization info for a specific FE.
    get_most_frequent_fe()
        Get the most frequently realized FE.
    has_fe_realizations()
        Check if FE realizations exist.

    Examples
    --------
    >>> valence = ValencePattern(
    ...     total_annotated=100,
    ...     fe_realizations=[...],
    ...     patterns=[...]
    ... )
    """

    total_annotated: int = Field(ge=0, description="Total annotated instances")
    fe_realizations: list[FERealization] = Field(description="FE realizations")
    patterns: list[ValenceAnnotationPattern] = Field(
        default_factory=list, description="Valence annotation patterns"
    )

    def get_fe_realization(self, fe_name: str) -> FERealization | None:
        """Get realization info for a specific FE.

        Parameters
        ----------
        fe_name : str
            Frame element name.

        Returns
        -------
        FERealization | None
            FE realization, or None if not found.
        """
        for fe_real in self.fe_realizations:
            if fe_real.fe_name == fe_name:
                return fe_real
        return None

    def get_most_frequent_fe(self) -> FERealization | None:
        """Get the most frequently realized FE.

        Returns
        -------
        FERealization | None
            Most frequent FE, or None if no realizations.
        """
        if not self.fe_realizations:
            return None
        return max(self.fe_realizations, key=lambda fe: fe.total)

    def has_fe_realizations(self) -> bool:
        """Check if FE realizations exist.

        Returns
        -------
        bool
            True if there are FE realizations.
        """
        return len(self.fe_realizations) > 0


class LexicalUnit(GlazingBaseModel):
    """A word or phrase that evokes a frame.

    Attributes
    ----------
    id : LexicalUnitID
        Unique lexical unit identifier.
    lemma_id : int | None, default=None
        Lemma identifier.
    name : LexicalUnitName
        LU name in lemma.pos format (validated).
    pos : FrameNetPOS
        Part of speech tag.
    definition : str
        LU definition (may have COD: or FN: prefix).
    annotation_status : AnnotationStatus | None, default=None
        Annotation completion status.
    total_annotated : int | None, default=None
        Total number of annotated instances.
    has_annotated_examples : bool, default=False
        Whether this LU has annotated examples.
    frame_id : FrameID
        ID of the frame this LU evokes.
    frame_name : FrameName
        Name of the frame this LU evokes.
    sentence_count : SentenceCount
        Sentence frequency information.
    lexemes : list[Lexeme]
        Individual word forms in this LU.
    semtypes : list[SemTypeRef], default=[]
        Semantic type references.
    valence_patterns : list[ValencePattern], default=[]
        Syntactic valence patterns.
    annotation_sets : list[AnnotationSet], default=[]
        Annotation sets for this LU.
    created_by : Username | None, default=None
        Creator username.
    created_date : datetime | None, default=None
        Creation timestamp.

    Methods
    -------
    get_headword_lexeme()
        Get the headword lexeme.
    has_valence_patterns()
        Check if LU has valence patterns.
    get_annotation_rate()
        Get sentence annotation completion rate.
    is_multi_word()
        Check if this is a multi-word LU.
    get_most_frequent_valence()
        Get most frequent valence pattern.

    Examples
    --------
    >>> lu = LexicalUnit(
    ...     id=1234,
    ...     name="abandon.v",
    ...     pos="V",
    ...     definition="To leave behind permanently",
    ...     frame_id=2031,
    ...     frame_name="Abandonment",
    ...     sentence_count=SentenceCount(annotated=50, total=100),
    ...     lexemes=[Lexeme(name="abandon", pos="V", headword=True)]
    ... )
    >>> print(lu.get_annotation_rate())
    0.5
    """

    id: LexicalUnitID = Field(description="Unique lexical unit identifier")
    lemma_id: int | None = Field(None, alias="lemmaID", description="Lemma identifier")
    name: LexicalUnitName = Field(description="LU name (lemma.pos format)")
    pos: FrameNetPOS = Field(description="Part of speech tag")
    definition: str = Field(min_length=1, description="LU definition")
    annotation_status: AnnotationStatus | None = Field(
        None, alias="status", description="Annotation completion status"
    )
    total_annotated: int | None = Field(
        None, alias="totalAnnotated", description="Total annotated instances"
    )
    has_annotated_examples: bool = Field(
        default=False, description="Whether this LU has annotated examples"
    )
    frame_id: FrameID = Field(description="Frame ID this LU evokes")
    frame_name: FrameName = Field(description="Frame name this LU evokes")
    sentence_count: SentenceCount = Field(description="Sentence frequency information")
    lexemes: list[Lexeme] = Field(description="Individual word forms")
    semtypes: list[SemTypeRef] = Field(default_factory=list, description="Semantic type references")
    valence_patterns: list[ValencePattern] = Field(
        default_factory=list, description="Syntactic valence patterns"
    )
    annotation_sets: list[AnnotationSet] = Field(
        default_factory=list, description="Annotation sets"
    )
    created_by: Username | None = Field(None, alias="cBy", description="Creator username")
    created_date: datetime | None = Field(None, alias="cDate", description="Creation timestamp")

    @field_validator("name")
    @classmethod
    def validate_lu_name(cls, v: str) -> str:
        """Validate LU name format (e.g., 'abandon.v', 'give_up.v')."""
        return validate_pattern(v, LU_NAME_PATTERN, "lexical unit name")

    @field_validator("definition")
    @classmethod
    def validate_definition(cls, v: str) -> str:
        """Parse and validate definition with optional prefix."""
        # Definitions often start with COD: or FN: but can be freeform
        # Allow any non-empty definition
        return v

    @field_validator("frame_name")
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
    def validate_lu_consistency(self) -> Self:
        """Validate lexical unit consistency."""
        # Check that at least one lexeme exists
        if not self.lexemes:
            raise ValueError("Lexical unit must have at least one lexeme")

        # Check that exactly one lexeme is marked as headword
        headwords = [lex for lex in self.lexemes if lex.headword]
        if len(headwords) != 1:
            raise ValueError("Lexical unit must have exactly one headword lexeme")

        # Validate total_annotated consistency
        if (
            self.total_annotated is not None
            and self.total_annotated > 0
            and self.sentence_count.total > 0
            and self.total_annotated > self.sentence_count.total
        ):
            raise ValueError("total_annotated cannot exceed sentence count total")

        return self

    def get_headword_lexeme(self) -> Lexeme | None:
        """Get the headword lexeme.

        Returns
        -------
        Lexeme | None
            The headword lexeme, or None if none found.
        """
        for lexeme in self.lexemes:
            if lexeme.headword:
                return lexeme
        return None

    def has_valence_patterns(self) -> bool:
        """Check if LU has valence patterns.

        Returns
        -------
        bool
            True if valence patterns exist.
        """
        return len(self.valence_patterns) > 0

    def get_annotation_rate(self) -> float:
        """Get sentence annotation completion rate.

        Returns
        -------
        float
            Annotation rate from sentence count (0.0-1.0).
        """
        return self.sentence_count.get_annotation_rate()

    def is_multi_word(self) -> bool:
        """Check if this is a multi-word LU.

        Returns
        -------
        bool
            True if LU contains multiple lexemes.
        """
        return len(self.lexemes) > 1

    def get_most_frequent_valence(self) -> ValencePattern | None:
        """Get most frequent valence pattern.

        Returns
        -------
        ValencePattern | None
            Most frequent pattern, or None if no patterns.
        """
        if not self.valence_patterns:
            return None
        return max(self.valence_patterns, key=lambda p: p.total_annotated)

    def get_annotation_set_by_id(self, anno_id: AnnotationSetID) -> AnnotationSet | None:
        """Get annotation set by ID.

        Parameters
        ----------
        anno_id : AnnotationSetID
            Annotation set ID to find.

        Returns
        -------
        AnnotationSet | None
            The annotation set, or None if not found.
        """
        for anno_set in self.annotation_sets:
            if anno_set.id == anno_id:
                return anno_set
        return None
