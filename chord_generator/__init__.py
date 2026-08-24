"""Jazz Chord Generator.

Given a melody (a sequence of notes), generate a context-aware jazz chord
progression that harmonizes it, using a Markov chain trained on jazz standards
and a user-controlled creativity level.
"""

from .chords import JazzChord
from .markov_chain import MarkovChain
from .phrase_analysis import BeatStrength, Note, Phrase, PhraseAnalyzer
from .key_detector import Key, KeyAwareHarmonizer, ScaleDetector, ScaleType
from .melody_generator import MelodyGenerator, create_melody_for_progression
from .standard_finder import JazzStandardsScraper
from .app import (
    ChordWithDuration,
    CreativityLevel,
    JazzChordGeneratorApp,
    RhythmStyle,
    demo_complete_app,
    interactive_demo,
)

__all__ = [
    "JazzChord",
    "MarkovChain",
    "BeatStrength",
    "Note",
    "Phrase",
    "PhraseAnalyzer",
    "Key",
    "KeyAwareHarmonizer",
    "ScaleDetector",
    "ScaleType",
    "MelodyGenerator",
    "create_melody_for_progression",
    "JazzStandardsScraper",
    "ChordWithDuration",
    "CreativityLevel",
    "JazzChordGeneratorApp",
    "RhythmStyle",
    "demo_complete_app",
    "interactive_demo",
]
