"""Reference resolution and validation for linguistic datasets.

This module provides functionality to validate cross-references, resolve
transitive mappings through intermediate datasets, and handle inheritance
chains in FrameNet and VerbNet.

Classes
-------
ReferenceResolver
    Main class for validating and resolving cross-dataset references.

Notes
-----
The resolver handles transitive reference resolution by finding paths through
intermediate datasets and propagating confidence scores along the path.
"""

from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from glazing.framenet.models import Frame, FrameRelation
from glazing.propbank.models import Frameset, Roleset
from glazing.references.models import (
    CrossReference,
    FEAlignment,
    FEInheritanceChain,
    MappingConfidence,
    MappingConflict,
    MappingIndex,
    MappingMetadata,
    TransitiveMapping,
)
from glazing.references.models import (
    FERelation as RefsFERelation,
)
from glazing.types import DatasetType
from glazing.verbnet.models import Member, VerbClass
from glazing.wordnet.models import Sense, Synset

T = TypeVar("T")


class ReferenceResolver:
    """Validate and resolve cross-references between linguistic datasets.

    This class provides methods to validate references against loaded datasets,
    resolve transitive mappings through intermediate resources, and handle
    inheritance relationships in VerbNet and FrameNet.

    Attributes
    ----------
    mapping_index : MappingIndex
        Index of all known mappings.
    framenet_frames : dict[str, Frame]
        FrameNet frames indexed by name.
    propbank_rolesets : dict[str, Roleset]
        PropBank rolesets indexed by ID.
    verbnet_classes : dict[str, VerbClass]
        VerbNet classes indexed by ID.
    wordnet_synsets : dict[str, Synset]
        WordNet synsets indexed by offset.
    wordnet_senses : dict[str, Sense]
        WordNet senses indexed by sense key.

    Methods
    -------
    set_datasets(framenet, propbank, verbnet, wordnet)
        Set the datasets for validation.
    validate_reference(reference)
        Validate that a reference's target exists.
    resolve_transitive(source_id, source_dataset, target_dataset, max_hops)
        Find indirect mappings through intermediate datasets.
    resolve_verbnet_inheritance(member, class_hierarchy)
        Resolve inherited mappings for a VerbNet member.
    resolve_framenet_fe_inheritance(frame, frame_relations)
        Resolve FE inheritance through frame relations.
    calculate_combined_confidence(path)
        Calculate confidence for a transitive mapping path.
    detect_conflicts(mappings)
        Detect conflicting mappings.
    """

    def __init__(self, mapping_index: MappingIndex | None = None) -> None:
        """Initialize the reference resolver.

        Parameters
        ----------
        mapping_index : MappingIndex | None, default=None
            Pre-existing mapping index to use.
        """
        self.mapping_index = mapping_index or MappingIndex()
        self.framenet_frames: dict[str, Frame] = {}
        self.propbank_rolesets: dict[str, Roleset] = {}
        self.verbnet_classes: dict[str, VerbClass] = {}
        self.wordnet_synsets: dict[str, Synset] = {}
        self.wordnet_senses: dict[str, Sense] = {}
        self._visited: set[str] = set()  # For cycle detection

    def set_datasets(
        self,
        framenet: list[Frame] | None = None,
        propbank: list[Frameset] | None = None,
        verbnet: list[VerbClass] | None = None,
        wordnet: tuple[list[Synset], list[Sense]] | None = None,
    ) -> None:
        """Set the datasets for validation.

        Parameters
        ----------
        framenet : list[Frame] | None, default=None
            FrameNet frames for validation.
        propbank : list[Frameset] | None, default=None
            PropBank framesets for validation.
        verbnet : list[VerbClass] | None, default=None
            VerbNet classes for validation.
        wordnet : tuple[list[Synset], list[Sense]] | None, default=None
            WordNet synsets and senses for validation.
        """
        if framenet:
            self.framenet_frames = {frame.name: frame for frame in framenet}

        if propbank:
            for frameset in propbank:
                for roleset in frameset.rolesets:
                    self.propbank_rolesets[roleset.id] = roleset

        if verbnet:
            for verb_class in verbnet:
                self._index_verbnet_class(verb_class)

        if wordnet:
            synsets, senses = wordnet
            self.wordnet_synsets = {synset.offset: synset for synset in synsets}
            self.wordnet_senses = {sense.sense_key: sense for sense in senses}

    def _index_verbnet_class(self, verb_class: VerbClass) -> None:
        """Recursively index a VerbNet class and its subclasses.

        Parameters
        ----------
        verb_class : VerbClass
            VerbNet class to index.
        """
        self.verbnet_classes[verb_class.id] = verb_class
        for subclass in verb_class.subclasses:
            self._index_verbnet_class(subclass)

    def validate_reference(self, reference: CrossReference) -> bool:
        """Validate that a reference's target exists in the dataset.

        Parameters
        ----------
        reference : CrossReference
            Reference to validate.

        Returns
        -------
        bool
            True if the target exists, False otherwise.
        """
        target_ids = (
            reference.target_id if isinstance(reference.target_id, list) else [reference.target_id]
        )

        for target_id in target_ids:
            if not self._validate_single_target(target_id, reference.target_dataset):
                return False
        return True

    def _validate_single_target(self, target_id: str, dataset: DatasetType) -> bool:
        """Validate a single target ID exists in the dataset.

        Parameters
        ----------
        target_id : str
            Target entity ID.
        dataset : DatasetType
            Target dataset type.

        Returns
        -------
        bool
            True if the target exists.
        """
        validation_methods: dict[str, Callable[[], bool]] = {
            "framenet": lambda: target_id in self.framenet_frames,
            "propbank": lambda: target_id in self.propbank_rolesets,
            "verbnet": lambda: self._validate_verbnet_target(target_id),
            "wordnet": lambda: (
                target_id in self.wordnet_synsets or target_id in self.wordnet_senses
            ),
        }

        validator = validation_methods.get(dataset)
        return bool(validator and validator())

    def _validate_verbnet_target(self, target_id: str) -> bool:
        """Validate VerbNet target ID.

        Parameters
        ----------
        target_id : str
            VerbNet target ID.

        Returns
        -------
        bool
            True if target exists.
        """
        # Check if it's a class ID
        if target_id in self.verbnet_classes:
            return True

        # Check members across all classes
        for verb_class in self.verbnet_classes.values():
            if any(m.verbnet_key == target_id for m in verb_class.members):
                return True

        return False

    def resolve_transitive(
        self,
        source_id: str,
        source_dataset: DatasetType,
        target_dataset: DatasetType,
        max_hops: int = 3,
    ) -> list[TransitiveMapping]:
        """Find indirect mappings through intermediate datasets.

        Uses breadth-first search to find all paths from source to target
        through intermediate datasets, up to max_hops in length.

        Parameters
        ----------
        source_id : str
            Source entity ID.
        source_dataset : DatasetType
            Source dataset type.
        target_dataset : DatasetType
            Target dataset type.
        max_hops : int, default=3
            Maximum number of intermediate mappings.

        Returns
        -------
        list[TransitiveMapping]
            All transitive mapping paths found, sorted by confidence.
        """
        results: list[TransitiveMapping] = []
        queue: deque[tuple[str, DatasetType, list[CrossReference]]] = deque()

        # Start BFS from source
        queue.append((source_id, source_dataset, []))

        while queue:
            current_id, current_dataset, path = queue.popleft()

            # Check if we've reached max depth
            if len(path) >= max_hops:
                continue

            # Get direct mappings from current node
            key = f"{current_dataset}:{current_id}"
            direct_mappings = self.mapping_index.forward_index.get(key, [])

            for mapping in direct_mappings:
                new_path = [*path, mapping]

                # Check if we reached target dataset
                if mapping.target_dataset == target_dataset:
                    # Create transitive mapping
                    transitive = TransitiveMapping(
                        source_dataset=source_dataset,
                        source_id=source_id,
                        target_dataset=target_dataset,
                        target_id=(
                            mapping.target_id[0]
                            if isinstance(mapping.target_id, list)
                            else mapping.target_id
                        ),
                        path=new_path,
                        combined_confidence=self.calculate_combined_confidence(new_path),
                    )
                    results.append(transitive)
                else:
                    # Continue searching from this node
                    targets = (
                        mapping.target_id
                        if isinstance(mapping.target_id, list)
                        else [mapping.target_id]
                    )
                    for target in targets:
                        # Avoid cycles
                        next_key = f"{mapping.target_dataset}:{target}"
                        if next_key not in self._visited:
                            self._visited.add(next_key)
                            queue.append((target, mapping.target_dataset, new_path))
                            self._visited.remove(next_key)

        # Sort by confidence
        return sorted(results, key=lambda x: x.combined_confidence, reverse=True)

    def resolve_verbnet_inheritance(
        self, member: Member, class_hierarchy: dict[str, VerbClass]
    ) -> list[CrossReference]:
        """Resolve inherited mappings for a VerbNet member.

        Traces through parent classes to find inherited mappings that
        aren't overridden in the member's class.

        Parameters
        ----------
        member : Member
            VerbNet member to resolve inheritance for.
        class_hierarchy : dict[str, VerbClass]
            All VerbNet classes indexed by ID.

        Returns
        -------
        list[CrossReference]
            Inherited mappings with metadata.
        """
        inherited_mappings: list[CrossReference] = []

        if not member.inherited_from_class:
            return inherited_mappings

        current_class = class_hierarchy.get(member.inherited_from_class)

        while current_class and current_class.parent_class:
            parent_class = class_hierarchy.get(current_class.parent_class)
            if not parent_class:
                break

            # Find parent member with same lemma
            parent_member = next((m for m in parent_class.members if m.name == member.name), None)

            if parent_member:
                # Inherit FrameNet mappings if not overridden
                if not member.framenet_mappings and parent_member.framenet_mappings:
                    for fn_mapping in parent_member.framenet_mappings:
                        inherited = CrossReference(
                            source_dataset="verbnet",
                            source_id=member.verbnet_key,
                            source_version="3.4",
                            target_dataset="framenet",
                            target_id=fn_mapping.frame_name,
                            mapping_type="inferred",
                            confidence=MappingConfidence(
                                score=(
                                    fn_mapping.confidence.score * 0.9
                                    if fn_mapping.confidence
                                    else 0.5
                                ),
                                method="inheritance",
                                factors={},
                            ),
                            metadata=MappingMetadata(
                                created_date=datetime.now(UTC),
                                created_by="resolver",
                                version="3.4",
                                validation_status="unvalidated",
                                notes=f"Inherited from {parent_class.id}",
                            ),
                            inherited_from=parent_class.id,
                        )
                        inherited_mappings.append(inherited)

                # Inherit PropBank mappings similarly
                if not member.propbank_mappings and parent_member.propbank_mappings:
                    for pb_mapping in parent_member.propbank_mappings:
                        inherited = CrossReference(
                            source_dataset="verbnet",
                            source_id=member.verbnet_key,
                            source_version="3.4",
                            target_dataset=pb_mapping.target_dataset,
                            target_id=pb_mapping.target_id,
                            mapping_type="inferred",
                            confidence=MappingConfidence(
                                score=(
                                    pb_mapping.confidence.score * 0.9
                                    if pb_mapping.confidence
                                    else 0.5
                                ),
                                method="inheritance",
                                factors={},
                            ),
                            metadata=MappingMetadata(
                                created_date=datetime.now(UTC),
                                created_by="resolver",
                                version="3.4",
                                validation_status="unvalidated",
                                notes=f"Inherited from {parent_class.id}",
                            ),
                            inherited_from=parent_class.id,
                        )
                        inherited_mappings.append(inherited)

            current_class = parent_class

        return inherited_mappings

    def resolve_framenet_fe_inheritance(
        self, frame: Frame, frame_relations: list[FrameRelation]
    ) -> list[FEAlignment]:
        """Resolve FE inheritance through frame relations.

        Traces FE mappings through inheritance relations to find
        alignments with parent frame FEs.

        Parameters
        ----------
        frame : Frame
            FrameNet frame to resolve FE inheritance for.
        frame_relations : list[FrameRelation]
            Frame relations to trace through.

        Returns
        -------
        list[FEAlignment]
            FE alignments including inherited ones.
        """
        alignments: list[FEAlignment] = []

        for relation in frame_relations:
            if relation.type == "Inherits from" and relation.sub_frame_id == frame.id:
                # Process FE mappings in inheritance relation
                for fe_rel in relation.fe_relations:
                    if fe_rel.relation_type == "Inheritance":
                        alignment = FEAlignment(
                            source_frame=frame.name,
                            source_fe=fe_rel.sub_fe_name or "",
                            target_dataset="framenet",
                            target_role=fe_rel.super_fe_name or "",
                            alignment_type="inherited",
                            confidence=MappingConfidence(
                                score=fe_rel.alignment_confidence or 0.9,
                                method="frame_inheritance",
                                factors={
                                    "semantic": fe_rel.semantic_similarity or 0.9,
                                    "syntactic": fe_rel.syntactic_similarity or 0.9,
                                },
                            ),
                            evidence=[f"Inherited from {relation.super_frame_name}"],
                        )
                        alignments.append(alignment)

        return alignments

    def trace_fe_inheritance_chain(
        self, fe_name: str, frame_name: str, frame_index: dict[str, Frame]
    ) -> FEInheritanceChain:
        """Trace FE inheritance through frame hierarchy.

        Follows inheritance relations to build a complete chain showing
        how an FE is inherited through parent frames.

        Parameters
        ----------
        fe_name : str
            Frame element name to trace.
        frame_name : str
            Starting frame name.
        frame_index : dict[str, Frame]
            All frames indexed by name.

        Returns
        -------
        FEInheritanceChain
            Complete inheritance chain for the FE.
        """
        chain = FEInheritanceChain(
            fe_name=fe_name,
            frame_chain=[frame_name],
            inheritance_path=[],
        )

        current_frame = frame_index.get(frame_name)
        while current_frame:
            # Find parent frame relation
            parent_rel = next(
                (r for r in current_frame.frame_relations if r.type == "Inherits from"),
                None,
            )
            if not parent_rel:
                break

            # Find FE mapping in relation
            fe_mapping = next(
                (fe for fe in parent_rel.fe_relations if fe.sub_fe_name == fe_name),
                None,
            )
            if fe_mapping:
                # Convert FrameNet FERelation to references FERelation
                refs_fe_mapping = RefsFERelation(
                    subID=fe_mapping.sub_fe_id,
                    subFEName=fe_mapping.sub_fe_name,
                    supID=fe_mapping.super_fe_id,
                    supFEName=fe_mapping.super_fe_name,
                    relation_type=getattr(fe_mapping, "relation_type", None),
                    alignment_confidence=getattr(fe_mapping, "alignment_confidence", None),
                    semantic_similarity=getattr(fe_mapping, "semantic_similarity", None),
                    syntactic_similarity=getattr(fe_mapping, "syntactic_similarity", None),
                    mapping_notes=getattr(fe_mapping, "mapping_notes", None),
                )
                chain.inheritance_path.append(refs_fe_mapping)
                chain.frame_chain.append(parent_rel.super_frame_name or "")
                fe_name = fe_mapping.super_fe_name or ""  # Continue with parent FE

            current_frame = frame_index.get(parent_rel.super_frame_name or "")

        return chain

    def calculate_combined_confidence(self, path: list[CrossReference]) -> float:
        """Calculate combined confidence for a transitive mapping path.

        Multiplies confidence scores along the path, with a default
        penalty for mappings without confidence.

        Parameters
        ----------
        path : list[CrossReference]
            Sequence of mappings forming a path.

        Returns
        -------
        float
            Combined confidence score (0.0-1.0).
        """
        if not path:
            return 0.0

        confidence = 1.0
        for mapping in path:
            if mapping.confidence:
                confidence *= mapping.confidence.score
            else:
                confidence *= 0.5  # Default penalty for unscored mappings

        return confidence

    def detect_conflicts(self, mappings: list[CrossReference]) -> list[MappingConflict]:
        """Detect conflicting mappings.

        Identifies cases where multiple high-confidence mappings point
        to different targets, or where mappings contradict each other.

        Parameters
        ----------
        mappings : list[CrossReference]
            Mappings to check for conflicts.

        Returns
        -------
        list[MappingConflict]
            Detected conflicts requiring resolution.
        """
        by_source = self._group_mappings_by_source(mappings)
        conflicts = []

        for (source_dataset, source_id), source_mappings in by_source.items():
            by_target_dataset = self._group_mappings_by_target_dataset(source_mappings)
            source_conflicts = self._find_conflicts_for_source(
                source_dataset, source_id, by_target_dataset
            )
            conflicts.extend(source_conflicts)

        return conflicts

    def _group_mappings_by_source(
        self, mappings: list[CrossReference]
    ) -> dict[tuple[DatasetType, str], list[CrossReference]]:
        """Group mappings by source dataset and ID.

        Parameters
        ----------
        mappings : list[CrossReference]
            Mappings to group.

        Returns
        -------
        dict[tuple[DatasetType, str], list[CrossReference]]
            Mappings grouped by source.
        """
        by_source: dict[tuple[DatasetType, str], list[CrossReference]] = {}
        for mapping in mappings:
            key = (mapping.source_dataset, mapping.source_id)
            if key not in by_source:
                by_source[key] = []
            by_source[key].append(mapping)
        return by_source

    def _group_mappings_by_target_dataset(
        self, mappings: list[CrossReference]
    ) -> dict[DatasetType, list[CrossReference]]:
        """Group mappings by target dataset.

        Parameters
        ----------
        mappings : list[CrossReference]
            Mappings to group.

        Returns
        -------
        dict[DatasetType, list[CrossReference]]
            Mappings grouped by target dataset.
        """
        by_target_dataset: dict[DatasetType, list[CrossReference]] = {}
        for mapping in mappings:
            if mapping.target_dataset not in by_target_dataset:
                by_target_dataset[mapping.target_dataset] = []
            by_target_dataset[mapping.target_dataset].append(mapping)
        return by_target_dataset

    def _find_conflicts_for_source(
        self,
        source_dataset: DatasetType,
        source_id: str,
        by_target_dataset: dict[DatasetType, list[CrossReference]],
    ) -> list[MappingConflict]:
        """Find conflicts for a specific source.

        Parameters
        ----------
        source_dataset : DatasetType
            Source dataset.
        source_id : str
            Source ID.
        by_target_dataset : dict[DatasetType, list[CrossReference]]
            Mappings grouped by target dataset.

        Returns
        -------
        list[MappingConflict]
            Conflicts found for this source.
        """
        conflicts = []

        for dataset_mappings in by_target_dataset.values():
            if len(dataset_mappings) <= 1:
                continue

            conflict = self._check_high_confidence_conflicts(
                source_dataset, source_id, dataset_mappings
            )
            if conflict:
                conflicts.append(conflict)

        return conflicts

    def _check_high_confidence_conflicts(
        self,
        source_dataset: DatasetType,
        source_id: str,
        dataset_mappings: list[CrossReference],
    ) -> MappingConflict | None:
        """Check for high-confidence conflicts in dataset mappings.

        Parameters
        ----------
        source_dataset : DatasetType
            Source dataset.
        source_id : str
            Source ID.
        dataset_mappings : list[CrossReference]
            Mappings to the same target dataset.

        Returns
        -------
        MappingConflict | None
            Conflict if found, None otherwise.
        """
        high_conf = [m for m in dataset_mappings if m.confidence and m.confidence.score > 0.7]

        if len(high_conf) <= 1:
            return None

        unique_targets = self._extract_unique_targets(high_conf)

        if len(unique_targets) > 1:
            return MappingConflict(
                conflict_type="ambiguous",
                source_dataset=source_dataset,
                source_id=source_id,
                conflicting_mappings=high_conf,
            )

        return None

    def _extract_unique_targets(self, mappings: list[CrossReference]) -> set[str]:
        """Extract unique target IDs from mappings.

        Parameters
        ----------
        mappings : list[CrossReference]
            Mappings to process.

        Returns
        -------
        set[str]
            Unique target IDs.
        """
        unique_targets = set()
        for mapping in mappings:
            if isinstance(mapping.target_id, list):
                unique_targets.update(mapping.target_id)
            else:
                unique_targets.add(mapping.target_id)
        return unique_targets
