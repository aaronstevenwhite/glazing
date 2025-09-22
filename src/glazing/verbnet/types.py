"""VerbNet-specific type definitions.

This module defines all type aliases and literal types specific to VerbNet,
including thematic roles, selectional restrictions, syntactic elements, and
semantic predicates.

Constants
---------
ThematicRoleType : type[Literal]
    All 48 VerbNet thematic roles.
ThematicRoleValue : type[Literal]
    Role values as they appear in semantic predicates.
SelectionalRestrictionType : type[Literal]
    All 42 selectional restriction types.
SyntacticRestrictionType : type[Literal]
    All 35 syntactic restriction types.
RestrictionValue : type[Literal]
    Restriction polarity ("+", "-").
SyntacticPOS : type[Literal]
    Syntactic positions in frames.
ArgumentType : type[Literal]
    Argument types in predicates.
PredicateType : type[Literal]
    All 150+ semantic predicate types.
EventType : type[Literal]
    Event structure types.
FrameDescriptionElement : type[Literal]
    Primary pattern elements.
SecondaryPattern : type[Literal]
    Secondary pattern descriptors.
QualiaType : type[Literal]
    Generative Lexicon qualia types.
OppositionType : type[Literal]
    Opposition structure types.
VerbClassID : type[str]
    VerbNet class identifier (e.g., "leave-51.2", "give-13.1-1").
VerbNetKey : type[str]
    Unique member identifier (e.g., "give#2").
WordNetSense : type[str]
    WordNet sense in percentage notation (e.g., "give%2:40:00").
DescriptionNumber : type[str]
    Frame description number (e.g., "0.2", "2.5.1").
PrepositionValue : type[str]
    Preposition values, space or pipe separated.
VERBNET_CLASS_PATTERN : str
    Regex pattern for VerbNet class ID validation.
VERBNET_KEY_PATTERN : str
    Regex pattern for VerbNet key validation.
PERCENTAGE_NOTATION_PATTERN : str
    Regex pattern for WordNet percentage notation.
DESCRIPTION_NUMBER_PATTERN : str
    Regex pattern for description numbers.

Examples
--------
>>> from glazing.verbnet.types import ThematicRoleType, PredicateType
>>> role: ThematicRoleType = "Agent"
>>> predicate: PredicateType = "motion"
"""

from typing import Literal

# Regex patterns for VerbNet identifiers
VERBNET_CLASS_PATTERN = r"^[a-z_]+-[0-9]+(?:\.[0-9]+)*(?:-[0-9]+)*$"  # e.g., "give-13.1-1"
VERBNET_KEY_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_\-\.\s]*#\d+$"  # e.g., "give#2", "tart up#1"
PERCENTAGE_NOTATION_PATTERN = r"^[a-z_-]+%[1-5]:[0-9]{2}:[0-9]{2}$"  # e.g., "give%2:40:00"
DESCRIPTION_NUMBER_PATTERN = r"^[0-9]+(?:\.[0-9]+)*$"  # e.g., "2.5.1"

# Type aliases for VerbNet identifiers (regex-validated in models)
type VerbClassID = str  # e.g., "leave-51.2", "give-13.1-1"
type VerbNetKey = str  # e.g., "give#2"
type WordNetSense = str  # e.g., "give%2:40:00" - percentage notation
type DescriptionNumber = str  # e.g., "0.2", "2.5.1"
type PrepositionValue = str  # e.g., "to", "at for on" - space or pipe separated

# Thematic role types (48 roles from VerbNet 3.4)
type ThematicRoleType = Literal[
    "Affector",
    "Agent",
    "Agent_i",
    "Agent_j",
    "Asset",
    "Attribute",
    "Axis",
    "Beneficiary",
    "Causer",
    "Circumstance",
    "Co-Agent",
    "Co-Patient",
    "Co-Theme",
    "Context",
    "Destination",
    "Duration",
    "Eventuality",
    "Experiencer",
    "Extent",
    "Final_Time",
    "Goal",
    "Initial_Location",
    "Initial_State",
    "Instrument",
    "Location",
    "Maleficiary",
    "Manner",
    "Material",
    "Path",
    "Patient",
    "Patient_i",
    "Patient_j",
    "Pivot",
    "Precondition",
    "Predicate",
    "Product",
    "Recipient",
    "Reflexive",
    "Result",
    "Source",
    "Stimulus",
    "Subeventuality",
    "Theme",
    "Theme_i",
    "Theme_j",
    "Topic",
    "Trajectory",
    "Value",
]

# Thematic role values as they appear in semantic predicates
# Includes standard roles, indexed variants, question-marked, and special forms
type ThematicRoleValue = Literal[
    # Standard roles
    "Affector",
    "Agent",
    "Asset",
    "Attribute",
    "Axis",
    "Beneficiary",
    "Causer",
    "Circumstance",
    "Co-Agent",
    "Co-Patient",
    "Co-Theme",
    "Context",
    "Destination",
    "Destination_Time",
    "Duration",
    "Eventuality",
    "Experiencer",
    "Extent",
    "Goal",
    "Initial_Location",
    "Initial_State",
    "Initial_Time",
    "Initial_location",  # Note: lowercase variant exists in data
    "Instrument",
    "Location",
    "Maleficiary",
    "Manner",
    "Material",
    "Path",
    "Patient",
    "Pivot",
    "Precondition",
    "Product",
    "Recipient",
    "Result",
    "Source",
    "Stimulus",
    "Subeventuality",
    "Theme",
    "Theme ",  # Note: trailing space variant exists in data
    "Topic",
    "Trajectory",
    "Value",
    # Indexed variants (_I, _J for plural arguments)
    "Agent_I",
    "Agent_J",
    "Location_I",
    "Location_J",
    "Patient_I",
    "Patient_J",
    "Theme_I",
    "Theme_J",
    "Topic_I",
    "Topic_J",
    # Question-marked roles (optional/implicit participants)
    "?Agent",
    "?Asset",
    "?Attribute",
    "?Beneficiary",
    "?Causer",
    "?Circumstance",
    "?Co-Agent",
    "?Co-Patient",
    "?Co-Theme",
    "?Destination",
    "?Eventuality",
    "?Experiencer",
    "?Extent",
    "?Goal",
    "?Initial_Location",
    "?Initial_location",
    "?Initial_State",
    "?Instrument",
    "?Location",
    "?Location_I",
    "?Location_J",
    "?Maleficiary",
    "?Material",
    "?Path",
    "?Patient",
    "?Pivot",
    "?Product",
    "?Recipient",
    "?Result",
    "?Source",
    "?Stimulus",
    "?Theme",
    "?Topic",
    "?Topic_I",
    "?Topic_J",
    "?Trajectory",
    "?Value",
    # Verb-specific roles (V_ prefix)
    "V_Final_State",
    "V_Manner",
    "V_State",
    "V_Vehicle",
    # Event variables
    "e1",
    "e2",
]

# Selectional restriction types (42 types)
type SelectionalRestrictionType = Literal[
    "abstract",
    "animal",
    "animate",
    "at",
    "biotic",
    "body_part",
    "comestible",
    "communication",
    "concrete",
    "currency",
    "dest",
    "dest_conf",
    "dest_dir",
    "dir",
    "elongated",
    "eventive",
    "force",
    "garment",
    "gol",
    "human",
    "int_control",
    "loc",
    "location",
    "machine",
    "nonrigid",
    "organization",
    "path",
    "plural",
    "pointy",
    "question",
    "refl",
    "region",
    "solid",
    "sound",
    "spatial",
    "src",
    "src_conf",
    "state",
    "substance",
    "time",
    "vehicle",
    "vehicle_part",
]

# Syntactic restriction types (45 types)
type SyntacticRestrictionType = Literal[
    "ac_ing",
    "ac_to_inf",
    "adv_loc",
    "be_sc_ing",
    "definite",
    "for_comp",
    "genitive",
    "how_extract",
    "np_ing",
    "np_omit_ing",
    "np_p_ing",
    "np_ppart",
    "np_to_inf",
    "oc_bare_inf",
    "oc_ing",
    "oc_to_inf",
    "plural",
    "poss_ing",
    "quotation",
    "refl",
    "rs_to_inf",
    "sc_ing",
    "sc_to_inf",
    "sentential",
    "small_clause",
    "tensed_that",
    "that_comp",
    "to_be",
    "wh_comp",
    "wh_extract",
    "wh_inf",
    "wh_ing",
    "what_extract",
    "what_inf",
    "wheth_inf",
]

# Restriction value (polarity)
type RestrictionValue = Literal["+", "-"]

# Syntactic positions in frames
type SyntacticPOS = Literal["NP", "VERB", "PREP", "ADV", "ADJ", "LEX", "ADVP", "S", "SBAR"]

# Argument types in semantic predicates
type ArgumentType = Literal["Event", "ThemRole", "VerbSpecific", "PredSpecific", "Constant"]

# Semantic predicate types (150+ types from VerbNet)
type PredicateType = Literal[
    # Motion and spatial predicates
    "motion",
    "body_motion",
    "elliptical_motion",
    "fictive_motion",
    "intrinsic_motion",
    "rotational_motion",
    "temporal_motion",
    "location",
    "has_location",
    "has_position",
    "has_spatial_relationship",
    "path",
    "direction",
    "pace",
    "penetrating",
    "together",
    "apart",
    # Possession and transfer
    "transfer",
    "transfer_info",
    "has_possession",
    "financial_interaction",
    "financial_interest_in",
    "cost",
    "earn",
    "spend",
    # Causation and change
    "cause",
    "change",
    "change_value",
    "become",
    "develop",
    "disappear",
    "start",
    "end",
    "finish",
    "continue",
    "completed",
    "succeed",
    # States and attributes
    "state",
    "has_state",
    "has_attribute",
    "has_value",
    "has_role",
    "has_designation",
    "has_configuration",
    "has_orientation",
    "has_physical_form",
    "has_capacity",
    "has_boundary",
    "has_material_integrity_state",
    "degradation_material_integrity",
    "has_organization_role",
    "has_emotional_state",
    "has_sentiment",
    "has_information",
    "has_set_member",
    "has_temporal_location",
    "alive",
    "free",
    "visible",
    "attached",
    "confined",
    "covered",
    "destroyed",
    "endangered",
    "harmed",
    "injured",
    "subjugated",
    "suffocated",
    "adjusted",
    "cooked",
    "full_of",
    "made_of",
    "mingled",
    "voided",
    # Actions and events
    "do",
    "act",
    "perform",
    "function",
    "operate_vehicle",
    "handle",
    "use",
    "utilize",
    "contact",
    "exert_force",
    "apply_heat",
    "apply_material",
    "work",
    "attempt",
    "engage_in",
    "take_care_of",
    "wear",
    # Communication and cognition
    "admit",
    "approve",
    "declare",
    "indicate",
    "signify",
    "believe",
    "calculate",
    "conclude",
    "desire",
    "discover",
    "intend",
    "judge",
    "perceive",
    "seem",
    "suspect",
    "think",
    "understand",
    "assess",
    "characterize",
    # Social interaction
    "abide_by",
    "allow",
    "avoid",
    "benefit",
    "charge",
    "conflict",
    "cooperate",
    "dedicate",
    "depend",
    "discourage",
    "encourage",
    "ensure",
    "harmonize",
    "help",
    "meet",
    "meets",
    "require",
    "support",
    "social_interaction",
    "authority_relationship",
    # Biological processes
    "body_process",
    "body_reflex",
    "body_sensation",
    "discomfort",
    "give_birth",
    "procreate",
    "sleep",
    "harm",
    "injury",
    # Abstract relations
    "about",
    "be",
    "contain",
    "control",
    "correlated",
    "differ",
    "equals",
    "exceed",
    "limit",
    "necessitate",
    "overlaps",
    "part_of",
    "relate",
    "satisfy",
    # Temporal relations
    "co-temporal",
    "duration",
    "endure",
    "occur",
    "repeated_sequence",
    "spend_time",
    # Environmental
    "weather",
    "emit",
    # Special/Other predicates
    "appear",
    "create_image",
    "Find",
    "in_reaction_to",
    "involuntary",
    "involved",
    "irrealis",
    "manner",
    "opposition",
    "reside",
    "search",
    "yield",
]

# Event structure types
type EventType = Literal["process", "state", "transition", "achievement"]

# Frame description elements that can appear in primary patterns
type FrameDescriptionElement = Literal[
    # Basic constituents
    "V",
    "NP",
    "PP",
    "S",
    "VP",
    "ADJP",
    "ADVP",
    "ADJ",
    "ADV",
    # Sentence types
    "S_INF",
    "S_ING",
    "S-INF",
    "S-Quote",
    "wh-S_INF",
    # Question words
    "how",
    "what",
    "when",
    "whether",
    "why",
    "that",
    "That",
    "whether/if",
    "how/whether",
    # Special NP types with semantic roles
    "NP-dative",
    "NP-Dative",
    "NP-Fulfilling",
    "NP-PRO-ARB",
    "NP-ATTR-POS",
    "NP.agent",
    "NP.asset",
    "NP.attribute",
    "NP.beneficiary",
    "NP.cause",
    "NP.destination",
    "NP.eventuality",
    "NP.experiencer",
    "NP.extent",
    "NP.goal",
    "NP.initial_location",
    "NP.instrument",
    "NP.location",
    "NP.material",
    "NP.patient",
    "NP.predicate",
    "NP.product",
    "NP.recipient",
    "NP.source",
    "NP.Source",
    "NP.stimulus",
    "NP.subeventuality",
    "NP.theme",
    "NP.topic",
    "NP.value",
    # PP types with semantic roles
    "PP-Conative",
    "PP.asset",
    "PP.attribute",
    "PP.beneficary",
    "PP.beneficiary",
    "PP.cause",
    "PP.co-agent",
    "PP.co-patient",
    "PP.co-theme",
    "PP.destination",
    "PP.destination-Conative",
    "PP.destinations",
    "PP.eventuality",
    "PP.experiencer",
    "PP.extent",
    "PP.goal",
    "PP.initial_location",
    "PP.initial_state",
    "PP.instrument",
    "PP.instsrument",  # Note: typo variant exists in data
    "PP.location",
    "PP.maleficiary",
    "PP.manner",
    "PP.agent",
    "PP.material",
    "PP.patient",
    "PP.pivot",
    "PP.predicate",
    "PP.product",
    "PP.recipient",
    "PP.result",
    "PP.source",
    "PP.stimulus",
    "PP.subeventuality",
    "PP.theme",
    "PP.Theme",
    "PP.topic",
    "PP.Topic",
    "PP.trajectory",
    "PP.value",
    # Adjective/Adverb types
    "ADJ.result",
    "ADJP-Result",
    "ADV-Middle",
    "ADVP-Middle",
    # Other elements
    "P.asset",
    "VP.predicate",
    "S.stimulus",
    "Passive",
    "(PP)",
    # Particles and special words
    "apart",
    "be",
    "down",
    "for",
    "out",
    "to",
    "together",
    "up",
    "It",
    "it",
    "There",
    "there",
]

# Secondary pattern descriptors
type SecondaryPattern = Literal[
    "Basic Transitive",
    "Basic Intransitive",
    "Transitive",
    "Intransitive",
    "NP-PP",
    "PP",
    "Dative",
    "Double Object",
    "Middle Construction",
    "Passive",
    "Reciprocal",
    "Reflexive",
    "Simple Reciprocal Transitive",
    "Simple Reciprocal Intransitive",
    "POSSING",
    "S",
    "WHAT-S",
    "HOW-S",
    "TO_INF",
    "N-SC",
    "NP-P-ING-SC",
    "PP-P-ING-SC",
    "AC-ING",
    "SC-ING",
    "with-PP",
    "to-PP",
    "from-PP",
    "into-PP",
    "on-PP",
    "at-PP",
    "for-PP",
    "against-PP",
    "about-PP",
    "of-PP",
    "in-PP",
    "Source-PP",
    "Goal-PP",
    "Theme-PP",
    "Path-PP",
    "Asset-PP",
    "Attribute-PP",
    "Location-PP",
    "Destination-PP",
    "Recipient-PP",
    "Patient-PP",
    "Beneficiary-PP",
    # Compound descriptors with semicolons
    "NP-PP; Source-PP",
    "NP-PP; to-PP",
    "NP-PP; from-PP",
    "NP-PP; Asset-PP",
    "NP-PP; Theme-PP",
    "NP-PP; path-PP",
    "NP-P-ING-SC; to-PP",
    "PP-P-ING-SC; from-PP",
    "NP-PP-PP; Theme-PP Destination-PP",
    "Transitive; passive",
    "Dative; Recipient-PP",
    "Double Object; Dative",
    "",  # Empty string is valid
]

# VerbNet-GL (Generative Lexicon) specific types

# GL Subcategorization POS values (extends beyond standard VerbNet syntax)
type GLSubcatPOS = Literal[
    "NP",  # Noun phrase - gets integer variable (0, 1, 2...)
    "VERB",  # Verb - gets event variable "e"
    "PREP",  # Preposition
    "ADV",  # Adverb
    "ADJ",  # Adjective
    "PP",  # Prepositional phrase (GL-specific)
]

# GL Variable assignments for subcategorization
type GLVariable = str  # e.g., "x", "y", "z", "e", "0", "1", "2"

# GL Temporal relations for subevents
type GLTemporalRelation = Literal[
    "starts",  # Subevent starts the main event
    "culminates",  # Subevent culminates the main event
    "results",  # Subevent results from the main event
    "during",  # Subevent occurs during the main event
    "before",  # Subevent occurs before the main event
    "after",  # Subevent occurs after the main event
]

type QualiaType = Literal[
    "formal",  # What type of thing it is
    "constitutive",  # What it's made of
    "telic",  # Purpose or function
    "agentive",  # How it comes about
]

type OppositionType = Literal["motion", "state_change", "possession_transfer", "info_transfer"]
