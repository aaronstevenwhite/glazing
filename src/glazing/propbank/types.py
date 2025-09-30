"""PropBank-specific type definitions.

Defines type aliases and literal types for PropBank data models.

Constants
---------
ArgumentNumber : type[Literal]
    PropBank argument numbers (0-7, m, M).
FunctionTag : type[Literal]
    PropBank function tags including spatial relations.
AliasPOS : type[Literal]
    Part-of-speech markers for aliases.
ArgumentTypePB : type[Literal]
    Complete argument types including modifiers and continuations.
CoreArgumentType : type[Literal]
    Core argument types (ARG0-6).
ModifierArgumentType : type[Literal]
    Modifier argument types (ARGM-*).
ContinuationArgumentType : type[Literal]
    Continuation argument types (C-ARG*, C-ARGM-*).
ReferenceArgumentType : type[Literal]
    Reference argument types (R-ARG*, R-ARGM-*).
UsageInUse : type[Literal]
    Usage status indicators.
RolesetID : type[str]
    Roleset identifier with validation pattern.
PredicateLemma : type[str]
    Predicate lemma with validation pattern.
ROLESET_ID_PATTERN : str
    Regex pattern for roleset ID validation.
PREDICATE_LEMMA_PATTERN : str
    Regex pattern for predicate lemma validation.

Examples
--------
>>> from glazing.propbank.types import ArgumentNumber, FunctionTag
>>> arg_num: ArgumentNumber = "0"
>>> func_tag: FunctionTag = "PAG"
"""

from typing import Literal

# Argument number literals - these are the actual values of the 'n' field in PropBank data
# Core arguments: "0"-"6" for ARG0-ARG6
# Modifiers: "m", "M" for modifier arguments (function tags go in 'f' field)
type ArgumentNumber = Literal["0", "1", "2", "3", "4", "5", "6", "m", "M"]

# Complete function tag set based on PropBank documentation
type FunctionTag = Literal[
    # Prefix tags for continuation and reference
    "C",  # Continuation prefix
    "R",  # Reference prefix
    # Standard function tags
    "ADJ",  # Adjectival modifier
    "ADV",  # Adverbial modifier
    "CAU",  # Cause
    "COM",  # Comitative
    "DIR",  # Direction
    "DIS",  # Discourse marker
    "DSP",  # Direct speech
    "EXT",  # Extent
    "GOL",  # Goal
    "LOC",  # Location
    "LVB",  # Light verb
    "MNR",  # Manner
    "MOD",  # Modal
    "NEG",  # Negation
    "PAG",  # Proto-agent (agent-like argument)
    "PNC",  # Purpose not cause
    "PPT",  # Proto-patient (patient-like argument)
    "PRD",  # Predicate
    "PRP",  # Purpose
    "PRR",  # Predicative
    "PRX",  # Proximal
    "REC",  # Reciprocal
    "RCL",  # Relative clause
    "SLC",  # Selectional
    "TMP",  # Temporal
    "VSP",  # Verb specific
    "CXN",  # Construction
    # Spatial relation tags (ISO-Space)
    "ANC",  # Anchor
    "ANC1",  # Anchor 1
    "ANC2",  # Anchor 2
    "ANG",  # Angle
    "AXS",  # Axis
    "AXSp",  # Axis point
    "AXSc",  # Axis coordinate
    "AXS1",  # Axis 1
    "AXS2",  # Axis 2
    "WHL",  # Whole
    "SEQ",  # Sequence
    "PSN",  # Position
    "SET",  # Set
    "SRC",  # Source
    "PRT",  # Part
    "DOM",  # Domain
    "SCL",  # Scale
    # Spatial entity tags
    "SE1",  # Spatial entity 1
    "SE2",  # Spatial entity 2
    "SE3",  # Spatial entity 3
    "SE4",  # Spatial entity 4
    "SE5",  # Spatial entity 5
    "SE6",  # Spatial entity 6
    # Lowercase variants (from DTD files)
    "adv",  # Adverbial (lowercase)
    "tmp",  # Temporal (lowercase)
    "pag",  # Proto-agent (lowercase)
    "ppt",  # Proto-patient (lowercase)
    "gol",  # Goal (lowercase)
    "vsp",  # Verb specific (lowercase)
    "com",  # Comitative (lowercase)
    "adj",  # Adjectival (lowercase)
    "cau",  # Cause (lowercase)
    "prp",  # Purpose (lowercase)
    "rec",  # Reciprocal (lowercase)
    "mnr",  # Manner (lowercase)
    "ext",  # Extent (lowercase)
    "loc",  # Location (lowercase)
    "dir",  # Direction (lowercase)
    "prd",  # Predicate (lowercase)
    # Additional function tags found in data
    "-",  # Dash/hyphen (special marker)
    "Framenet",  # FrameNet reference
    "ORT",  # Orthographic
    "PLN",  # Plain
    "PRT1",  # Particle variant 1
    "PRT2",  # Particle variant 2
    "",  # Empty tag (found in some files)
]

# Alias part-of-speech tags
type AliasPOS = Literal[
    "r",  # Adverb
    "p",  # Preposition
    "v",  # Verb
    "n",  # Noun
    "j",  # Adjective
    "l",  # Unknown/Other
    "x",  # Unknown/Other
    "m",  # Multi-word
    "d",  # Determiner/Other
    "f",  # Unknown/Other
]

# Complete argument type system
type ArgumentTypePB = Literal[
    # Core arguments
    "ARG0",
    "ARG1",
    "ARG2",
    "ARG3",
    "ARG4",
    "ARG5",
    "ARG6",
    # Continuation arguments (C-ARG)
    "C-ARG0",
    "C-ARG1",
    "C-ARG2",
    "C-ARG3",
    "C-ARG4",
    "C-ARG5",
    "C-ARG6",
    # Reference arguments (R-ARG)
    "R-ARG0",
    "R-ARG1",
    "R-ARG2",
    "R-ARG3",
    "R-ARG4",
    "R-ARG5",
    "R-ARG6",
    # Modifier arguments (ARGM)
    "ARGM-ADJ",  # Adjectival modifier
    "ARGM-ADV",  # Adverbial modifier
    "ARGM-CAU",  # Cause
    "ARGM-COM",  # Comitative
    "ARGM-DIR",  # Direction
    "ARGM-DIS",  # Discourse
    "ARGM-DSP",  # Direct speech
    "ARGM-EXT",  # Extent
    "ARGM-GOL",  # Goal
    "ARGM-LOC",  # Location
    "ARGM-LVB",  # Light verb
    "ARGM-MNR",  # Manner
    "ARGM-MOD",  # Modal
    "ARGM-NEG",  # Negation
    "ARGM-PNC",  # Purpose not cause
    "ARGM-PRD",  # Predicate
    "ARGM-PRP",  # Purpose
    "ARGM-PRR",  # Predicative
    "ARGM-PRX",  # Proximal
    "ARGM-REC",  # Reciprocal
    "ARGM-TMP",  # Temporal
    "ARGM-CXN",  # Construction
    # Continuation modifiers (C-ARGM)
    "C-ARGM-ADJ",
    "C-ARGM-ADV",
    "C-ARGM-CAU",
    "C-ARGM-COM",
    "C-ARGM-DIR",
    "C-ARGM-DIS",
    "C-ARGM-DSP",
    "C-ARGM-EXT",
    "C-ARGM-LOC",
    "C-ARGM-MNR",
    "C-ARGM-MOD",
    "C-ARGM-NEG",
    "C-ARGM-PRP",
    "C-ARGM-TMP",
    "C-ARGM-CXN",
    # Reference modifiers (R-ARGM)
    "R-ARGM-ADV",
    "R-ARGM-CAU",
    "R-ARGM-COM",
    "R-ARGM-DIR",
    "R-ARGM-EXT",
    "R-ARGM-GOL",
    "R-ARGM-LOC",
    "R-ARGM-MNR",
    "R-ARGM-MOD",
    "R-ARGM-PNC",
    "R-ARGM-PRD",
    "R-ARGM-PRP",
    "R-ARGM-TMP",
    # Additional argument types found in data
    "ARGA",  # Special argument type (found in examples)
    "ARGM-TOP",  # Topic modifier
]

# Usage status indicators
type UsageInUse = Literal["+", "-"]

# Regex patterns for validation (to be used with validators)
ROLESET_ID_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]*\.(\d+|LV)$"  # Support light verb suffix .LV
PREDICATE_LEMMA_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]*$"  # Allow uppercase

# Type aliases for validated strings
type RolesetID = str  # Validated with ROLESET_ID_PATTERN
type PredicateLemma = str  # Validated with PREDICATE_LEMMA_PATTERN
type IntOrQuestionMark = int | Literal["?"]  # For start/end fields that can be ? or integer

# Core argument types (ARG0-6, ARGA) - based on actual data
type CoreArgumentType = Literal["ARG0", "ARG1", "ARG2", "ARG3", "ARG4", "ARG5", "ARG6", "ARGA"]

# Modifier argument types (ARGM-*)
type ModifierArgumentType = Literal[
    "ARGM-ADJ",
    "ARGM-ADV",
    "ARGM-CAU",
    "ARGM-COM",
    "ARGM-DIR",
    "ARGM-DIS",
    "ARGM-DSP",
    "ARGM-EXT",
    "ARGM-GOL",
    "ARGM-LOC",
    "ARGM-LVB",
    "ARGM-MNR",
    "ARGM-MOD",
    "ARGM-NEG",
    "ARGM-PNC",
    "ARGM-PRD",
    "ARGM-PRP",
    "ARGM-PRR",
    "ARGM-PRX",
    "ARGM-REC",
    "ARGM-TMP",
    "ARGM-CXN",
    "ARGM-TOP",
]

# Continuation argument types (C-ARG*, C-ARGM-*)
type ContinuationArgumentType = Literal[
    "C-ARG0",
    "C-ARG1",
    "C-ARG2",
    "C-ARG3",
    "C-ARG4",
    "C-ARG5",
    "C-ARG6",
    "C-ARGM-ADJ",
    "C-ARGM-ADV",
    "C-ARGM-CAU",
    "C-ARGM-COM",
    "C-ARGM-DIR",
    "C-ARGM-DIS",
    "C-ARGM-DSP",
    "C-ARGM-EXT",
    "C-ARGM-LOC",
    "C-ARGM-MNR",
    "C-ARGM-MOD",
    "C-ARGM-NEG",
    "C-ARGM-PRP",
    "C-ARGM-TMP",
    "C-ARGM-CXN",
]

# Reference argument types (R-ARG*, R-ARGM-*)
type ReferenceArgumentType = Literal[
    "R-ARG0",
    "R-ARG1",
    "R-ARG2",
    "R-ARG3",
    "R-ARG4",
    "R-ARG5",
    "R-ARG6",
    "R-ARGM-ADV",
    "R-ARGM-CAU",
    "R-ARGM-COM",
    "R-ARGM-DIR",
    "R-ARGM-EXT",
    "R-ARGM-GOL",
    "R-ARGM-LOC",
    "R-ARGM-MNR",
    "R-ARGM-MOD",
    "R-ARGM-PNC",
    "R-ARGM-PRD",
    "R-ARGM-PRP",
    "R-ARGM-TMP",
]

# Union of all PropBank argument types
type PropBankArgumentType = (
    CoreArgumentType | ModifierArgumentType | ContinuationArgumentType | ReferenceArgumentType
)
